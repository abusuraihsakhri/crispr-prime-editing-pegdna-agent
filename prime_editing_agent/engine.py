"""
Deterministic threshold engine for the lightweight package.

The thresholds are repository constants used for demonstration and testing.
They are not validated pegRNA design criteria.
"""
from typing import Any, Dict, Optional


class FrontierDomainEngine:
    STANDARD = "Repository-defined rule thresholds"
    PRIMARY_BOUND = 25.0
    SECONDARY_BOUND = 10.0

    @classmethod
    def evaluate_primary_parameter(
        cls,
        value: float,
    ) -> Optional[Dict[str, Any]]:
        if value > cls.PRIMARY_BOUND:
            return {
                "summary": "Primary Metric Threshold Exceeded",
                "details": (
                    f"Parameter value ({value:.3f}) exceeds the repository "
                    f"threshold ({cls.PRIMARY_BOUND:.1f})."
                ),
                "remediation": (
                    "Review the input and threshold assumptions before downstream use."
                ),
            }
        return None

    @classmethod
    def evaluate_secondary_kinetics(
        cls,
        value: float,
        is_critical: bool,
    ) -> Optional[Dict[str, Any]]:
        if value > cls.SECONDARY_BOUND or is_critical:
            return {
                "summary": (
                    "Critical Flag Set"
                    if is_critical
                    else "Secondary Metric Threshold Exceeded"
                ),
                "details": (
                    f"Secondary metric ({value:.3f}) with "
                    f"CriticalFlag={is_critical}."
                ),
                "remediation": (
                    "Review the flagged condition before downstream use."
                ),
            }
        return None

    @classmethod
    def audit_specification_conformance(
        cls,
        descriptor: str,
        attributes: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        del attributes
        desc_upper = str(descriptor).upper()
        flags = ("VIOLATION", "DISCORDANT", "ANOMALY", "MUTANT", "LEAK")
        matched = next((flag for flag in flags if flag in desc_upper), None)
        if matched:
            return {
                "summary": "Configured Discordance Keyword Detected",
                "details": (
                    f"Status descriptor '{descriptor}' contains the configured "
                    f"keyword '{matched}'."
                ),
                "remediation": (
                    "Verify the status descriptor and associated source data."
                ),
            }
        return None
