"""
Specialized deterministic workers for the audited rule-based workflow.
"""
import uuid
from typing import List

from .models import AgentAlert, SystemTaskPayload, UrgencyLevel


class InvariantQCWorker:
    """Check the repository-defined primary metric threshold."""

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        alerts = []
        if payload.primary_metric > 25.0:
            alerts.append(AgentAlert(
                alert_id=f"QC-{uuid.uuid4().hex[:6]}",
                origin_worker="InvariantQCWorker",
                urgency=UrgencyLevel.ELEVATED,
                summary="Primary Metric Threshold Exceeded",
                technical_details=(
                    f"Primary measurement ({payload.primary_metric:.2f}) exceeds "
                    "the repository threshold (25.00)."
                ),
                actionable_remediation=(
                    "Review the input and threshold assumptions before downstream use."
                ),
            ))
        return alerts


class SafetyEscalationWorker:
    """Check the secondary metric threshold and explicit critical flag."""

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        alerts = []
        if payload.is_critical_flag or payload.secondary_metric > 12.0:
            alerts.append(AgentAlert(
                alert_id=f"SAFE-{uuid.uuid4().hex[:6]}",
                origin_worker="SafetyEscalationWorker",
                urgency=(
                    UrgencyLevel.CRITICAL_STAT
                    if payload.is_critical_flag
                    else UrgencyLevel.ELEVATED
                ),
                summary=(
                    "Critical Flag Set"
                    if payload.is_critical_flag
                    else "Secondary Metric Threshold Exceeded"
                ),
                technical_details=(
                    f"CriticalFlag={payload.is_critical_flag} with secondary "
                    f"metric {payload.secondary_metric:.2f}."
                ),
                actionable_remediation=(
                    "Review the flagged condition before downstream use."
                ),
            ))
        return alerts


class ProtocolConformanceWorker:
    """Check the status descriptor for configured discordance keywords."""

    FLAGS = ("DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT")

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        alerts = []
        desc_upper = str(payload.status_descriptor).upper()
        matched = next((flag for flag in cls.FLAGS if flag in desc_upper), None)
        if matched:
            alerts.append(AgentAlert(
                alert_id=f"CONF-{uuid.uuid4().hex[:6]}",
                origin_worker="ProtocolConformanceWorker",
                urgency=UrgencyLevel.ELEVATED,
                summary="Configured Discordance Keyword Detected",
                technical_details=(
                    f"Descriptor '{payload.status_descriptor}' contains the "
                    f"configured keyword '{matched}'."
                ),
                actionable_remediation=(
                    "Verify the status descriptor and associated source data."
                ),
            ))
        return alerts
