"""Regression checks for input validation and concurrent audit-chain integrity."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.api import app as audited_app
from agents.base import AuditTrail, _LazyAuditTrail
from agents.models import SystemTaskPayload
from cli import main as audited_cli
from prime_editing_agent.cli import main as lightweight_cli
from prime_editing_agent.server import create_app


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", float("nan"), float("inf")])
@pytest.mark.parametrize("field", ["primary_metric", "secondary_metric"])
def test_audited_model_rejects_nonfinite_metrics(field, value):
    data = {
        "task_id": "CHECK-1",
        "target_identifier": "TARGET-1",
        "primary_metric": 10,
        "secondary_metric": 5,
    }
    data[field] = value
    with pytest.raises(ValidationError):
        SystemTaskPayload(**data)


@pytest.mark.parametrize("field", ["primary_metric", "secondary_metric"])
def test_both_apis_reject_nonfinite_strings(field):
    payload = {
        "task_id": "CHECK-1",
        "target_identifier": "TARGET-1",
        "primary_metric": 10,
        "secondary_metric": 5,
        "status_descriptor": "NOMINAL",
    }
    payload[field] = "NaN"
    for app in (audited_app, create_app()):
        response = TestClient(app).post("/api/audit", json=payload)
        assert response.status_code == 422, response.text


@pytest.mark.parametrize("cli", [audited_cli, lightweight_cli])
@pytest.mark.parametrize("flag", ["--primary", "--secondary"])
@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_both_clis_reject_nonfinite_arguments(cli, flag, value):
    with pytest.raises(SystemExit) as exc:
        cli(["audit", flag, value])
    assert exc.value.code == 2


@pytest.mark.parametrize("cli", [audited_cli, lightweight_cli])
def test_csv_extra_columns_are_rejected_without_output(cli, tmp_path):
    source = tmp_path / "malformed.csv"
    target = tmp_path / "result.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric\n"
        "T1,TARGET-1,10,4,EXTRA\n", encoding="utf-8"
    )
    assert cli(["batch", "-i", str(source), "-o", str(target)]) == 1
    assert not target.exists()


def test_audit_chain_is_consistent_under_concurrent_writes():
    trail = AuditTrail(secret_key="test-threaded-audit-secret-2026")

    def append(i):
        return trail.log("tester", "test", "CASE", {"index": i})

    with ThreadPoolExecutor(max_workers=12) as pool:
        entries = list(pool.map(append, range(100)))

    assert len(entries) == 100
    assert len({entry["audit_id"] for entry in entries}) == 100
    assert len(trail.get_trail()) == 100
    assert trail.verify_integrity()

    # Returned entries must not permit mutation of the internal chain.
    snapshot = trail.get_trail()
    snapshot[0]["current_hash"] = "tampered"
    assert trail.verify_integrity()


def test_lazy_trail_initialization_is_singleton_under_load(monkeypatch):
    monkeypatch.setenv("AUDIT_SECRET_KEY", "test-lazy-audit-secret-2026")
    wrapper = _LazyAuditTrail()
    with ThreadPoolExecutor(max_workers=12) as pool:
        instances = list(pool.map(lambda _: wrapper._get(), range(60)))
    assert len({id(instance) for instance in instances}) == 1
