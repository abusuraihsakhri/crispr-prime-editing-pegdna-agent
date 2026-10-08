"""
Coordinator and worker wrappers for the lightweight deterministic rule engine.
"""
import uuid
from typing import Any, Dict, List

from .engine import FrontierDomainEngine
from .models import AgentTelemetryAlert, ExecutionStatus, FrontierPayload


class PBSThermodynamicsAgent:
    """Evaluate the package's primary numeric threshold."""

    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.evaluate_primary_parameter(
            payload.primary_metric
        )
        if res:
            alerts.append(
                AgentTelemetryAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    origin_agent="PBSThermodynamicsAgent",
                    status=ExecutionStatus.ELEVATED_RISK,
                    summary=res["summary"],
                    technical_details=res["details"],
                    actionable_remediation=res["remediation"],
                )
            )
        return alerts


class RTTemplateLengthAgent:
    """Evaluate the package's secondary numeric threshold and critical flag."""

    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.evaluate_secondary_kinetics(
            payload.secondary_metric,
            payload.is_critical_flag,
        )
        if res:
            alerts.append(
                AgentTelemetryAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    origin_agent="RTTemplateLengthAgent",
                    status=(
                        ExecutionStatus.CRITICAL_INTERVENTION
                        if payload.is_critical_flag
                        else ExecutionStatus.ELEVATED_RISK
                    ),
                    summary=res["summary"],
                    technical_details=res["details"],
                    actionable_remediation=res["remediation"],
                )
            )
        return alerts


class SecondaryFlapEquilibriumAgent:
    """Evaluate configured status-descriptor keywords."""

    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.audit_specification_conformance(
            payload.status_descriptor,
            payload.attributes,
        )
        if res:
            alerts.append(
                AgentTelemetryAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    origin_agent="SecondaryFlapEquilibriumAgent",
                    status=ExecutionStatus.ELEVATED_RISK,
                    summary=res["summary"],
                    technical_details=res["details"],
                    actionable_remediation=res["remediation"],
                )
            )
        return alerts


class PrimeEditingCoordinator:
    """Coordinate the three lightweight deterministic checks."""

    def __init__(self):
        self.sub_1 = PBSThermodynamicsAgent()
        self.sub_2 = RTTemplateLengthAgent()
        self.sub_3 = SecondaryFlapEquilibriumAgent()
        self.execution_ledger: Dict[str, Dict[str, Any]] = {}

    def process(self, payload: FrontierPayload) -> Dict[str, Any]:
        all_alerts: List[AgentTelemetryAlert] = []
        all_alerts.extend(self.sub_1.audit(payload))
        all_alerts.extend(self.sub_2.audit(payload))
        all_alerts.extend(self.sub_3.audit(payload))

        crit_count = sum(
            1
            for alert in all_alerts
            if alert.status == ExecutionStatus.CRITICAL_INTERVENTION
        )
        warn_count = sum(
            1
            for alert in all_alerts
            if alert.status == ExecutionStatus.ELEVATED_RISK
        )

        if crit_count > 0:
            status = ExecutionStatus.CRITICAL_INTERVENTION
        elif warn_count > 0:
            status = ExecutionStatus.ELEVATED_RISK
        else:
            status = ExecutionStatus.NOMINAL

        dossier = {
            "system": "crispr-prime-editing-pegdna-agent",
            "domain": "Genome Engineering",
            "task_id": payload.task_id,
            "target_identifier": payload.target_identifier,
            "overall_status": status.value,
            "total_alerts": len(all_alerts),
            "critical_count": crit_count,
            "warning_count": warn_count,
            "alerts": [alert.to_dict() for alert in all_alerts],
            "standard_specification": FrontierDomainEngine.STANDARD,
            "consensus_summary": (
                "Deterministic evaluation completed across three checks with "
                f"status [{status.value}]."
            ),
        }

        self.execution_ledger[payload.task_id] = dossier
        return dossier

    def query_supervisory_chat(self, query: str) -> str:
        q = query.strip().lower()
        if "status" in q or "ledger" in q:
            return (
                "Prime-editing rule evaluator currently holds "
                f"{len(self.execution_ledger)} in-memory task results."
            )
        if "standard" in q or "spec" in q:
            return (
                "This package uses repository-defined specifications and "
                "demonstration thresholds; they are not validated biological criteria."
            )
        return (
            "Prime-editing rule evaluator is available for deterministic "
            "repository-defined threshold checks."
        )
