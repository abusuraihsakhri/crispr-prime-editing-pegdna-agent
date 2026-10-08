import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-2026-secure")

from fastapi.testclient import TestClient

from agents.api import app as audited_app
from cli import main as audited_cli_main
from prime_editing_agent.cli import main as lightweight_cli_main
from prime_editing_agent.server import create_app


def _write_csv(path: Path, critical_value: str) -> None:
    path.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
        f"TASK-1,TARGET-1,10,4,{critical_value},NOMINAL\n",
        encoding="utf-8",
    )


def _read_single_row(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    return rows[0]


def test_audited_batch_parses_false_string_as_false(tmp_path):
    source = tmp_path / "input.csv"
    target = tmp_path / "output.csv"
    _write_csv(source, "False")

    assert audited_cli_main(["batch", "-i", str(source), "-o", str(target)]) == 0

    row = _read_single_row(target)
    assert row["overall_urgency"] == "ROUTINE"
    assert row["integrity_status"] == "VALIDATED_OPTIMAL"
    assert row["total_alerts"] == "0"


def test_lightweight_batch_parses_false_string_as_false(tmp_path):
    source = tmp_path / "input.csv"
    target = tmp_path / "output.csv"
    _write_csv(source, "False")

    assert lightweight_cli_main(["batch", "-i", str(source), "-o", str(target)]) == 0

    row = _read_single_row(target)
    assert row["overall_status"] == "NOMINAL_OPTIMAL"
    assert row["critical_count"] == "0"
    assert row["total_alerts"] == "0"


def test_batch_rejects_invalid_boolean_value(tmp_path):
    source = tmp_path / "input.csv"
    target = tmp_path / "output.csv"
    _write_csv(source, "sometimes")

    assert audited_cli_main(["batch", "-i", str(source), "-o", str(target)]) == 1
    assert not target.exists()

    assert lightweight_cli_main(["batch", "-i", str(source), "-o", str(target)]) == 1
    assert not target.exists()


def test_audited_api_health_and_nominal_evaluation():
    client = TestClient(audited_app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "HEALTHY"

    response = client.post(
        "/api/audit",
        json={
            "task_id": "API-1",
            "target_identifier": "TARGET-1",
            "primary_metric": 10,
            "secondary_metric": 4,
            "status_descriptor": "NOMINAL",
            "is_critical_flag": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_urgency"] == "ROUTINE"
    assert payload["total_alerts"] == 0


def test_lightweight_api_health_and_nominal_evaluation():
    app = create_app()
    assert app is not None
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "HEALTHY"

    response = client.post(
        "/api/audit",
        json={
            "task_id": "API-2",
            "target_identifier": "TARGET-2",
            "primary_metric": 10,
            "secondary_metric": 4,
            "status_descriptor": "NOMINAL",
            "is_critical_flag": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "NOMINAL_OPTIMAL"
    assert payload["total_alerts"] == 0


def test_static_web_app_has_no_backend_dependency():
    root = Path(__file__).parent.parent
    html = (root / "web" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "web" / "app.js").read_text(encoding="utf-8")

    assert 'src="./app.js"' in html
    assert "fetch(" not in javascript
    assert "XMLHttpRequest" not in javascript
    assert "audit_hash: null" in javascript
