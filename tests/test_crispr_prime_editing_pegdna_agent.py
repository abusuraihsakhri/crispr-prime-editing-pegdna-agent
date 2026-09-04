"""
Automated Pytest Test Suite for Crispr Prime Editing Pegdna Agent.
Domain: AI Drug Discovery, Structural Biology & Wet-Lab Robotics
Standard: wwPDB / IUPAC / OpenSMILES / ISAC Standards
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set audit key before importing agents that use it
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-2026-secure")

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_audit_trail_signature_verification():
    """Verify that audit trail detects tampered entries via HMAC signature check."""
    from agents.base import AuditTrail
    trail = AuditTrail(secret_key="test-secret-key-for-verification")
    trail.log("test_actor", "test_tier", "TEST_EVENT", {"data": "value1"})
    trail.log("test_actor", "test_tier", "TEST_EVENT", {"data": "value2"})
    assert trail.verify_integrity() is True

    # Tamper with an entry and verify detection
    trail.logs[0]["payload_hash"] = "tampered_hash"
    assert trail.verify_integrity() is False


def test_audit_trail_requires_secret_key():
    """Verify that AuditTrail raises error when no secret key is provided."""
    from agents.base import AuditTrail, SecurityException
    import os

    saved = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        with pytest.raises(SecurityException):
            AuditTrail()
    finally:
        if saved:
            os.environ["AUDIT_SECRET_KEY"] = saved


def test_audit_trail_rejects_short_secret():
    """Verify that AuditTrail rejects short secret keys."""
    from agents.base import AuditTrail, SecurityException

    with pytest.raises(SecurityException):
        AuditTrail(secret_key="short")


def test_batch_missing_file_returns_error():
    """Verify that batch command handles missing input file gracefully."""
    from cli import main
    result = main(["batch", "-i", "nonexistent_file_12345.csv"])
    assert result == 1


def test_phi_redaction():
    """Verify that PHI guard properly redacts sensitive information."""
    redacted = PHIGuard.redact_phi("Patient MRN-12345678 has appointment")
    assert "MRN-12345678" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted
