"use strict";

(() => {
  const PRIMARY_BOUND = 25.0;
  const SECONDARY_BOUND = 12.0;
  const CONFORMANCE_FLAGS = [
    "DISCORDANT",
    "ANOMALY",
    "MUTANT",
    "VIOLATION",
    "FAIL",
    "REJECT",
  ];

  function requireFiniteNumber(value, label) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      throw new Error(`${label} must be a finite number.`);
    }
    return parsed;
  }

  function evaluatePayload(payload) {
    const primary = requireFiniteNumber(payload.primary_metric, "Primary metric");
    const secondary = requireFiniteNumber(payload.secondary_metric, "Secondary metric");
    const descriptor = String(payload.status_descriptor || "NOMINAL");
    const descriptorUpper = descriptor.toUpperCase();
    const isCritical = Boolean(payload.is_critical_flag);
    const alerts = [];

    if (primary > PRIMARY_BOUND) {
      alerts.push({
        origin_worker: "InvariantQCWorker",
        urgency: "ELEVATED_RISK",
        summary: "Primary metric threshold exceeded",
        technical_details:
          `Primary measurement (${primary.toFixed(2)}) exceeds the repository threshold (${PRIMARY_BOUND.toFixed(2)}).`,
        actionable_remediation:
          "Review the input and the threshold assumptions before interpreting the result.",
      });
    }

    if (isCritical || secondary > SECONDARY_BOUND) {
      alerts.push({
        origin_worker: "SafetyEscalationWorker",
        urgency: isCritical ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
        summary: isCritical
          ? "Critical flag set"
          : "Secondary metric threshold exceeded",
        technical_details:
          `CriticalFlag=${isCritical} with secondary metric ${secondary.toFixed(2)}.`,
        actionable_remediation:
          "Review the flagged condition before downstream use.",
      });
    }

    const matchedFlag = CONFORMANCE_FLAGS.find((flag) =>
      descriptorUpper.includes(flag)
    );
    if (matchedFlag) {
      alerts.push({
        origin_worker: "ProtocolConformanceWorker",
        urgency: "ELEVATED_RISK",
        summary: "Conformance keyword detected",
        technical_details:
          `Status descriptor contains the configured keyword "${matchedFlag}".`,
        actionable_remediation:
          "Verify the status descriptor and any associated source data.",
      });
    }

    const criticalCount = alerts.filter(
      (alert) => alert.urgency === "CRITICAL_STAT_PANIC"
    ).length;
    const elevatedCount = alerts.filter(
      (alert) => alert.urgency === "ELEVATED_RISK"
    ).length;

    let overallUrgency = "ROUTINE";
    let integrityStatus = "VALIDATED_OPTIMAL";
    if (criticalCount > 0) {
      overallUrgency = "CRITICAL_STAT_PANIC";
      integrityStatus = "RECALIBRATION_REQUIRED";
    } else if (elevatedCount > 0) {
      overallUrgency = "ELEVATED_RISK";
      integrityStatus = "DISCORDANT_ANOMALY";
    }

    return {
      mode: "browser-only-static",
      task_id: String(payload.task_id || ""),
      target_identifier: String(payload.target_identifier || ""),
      primary_metric: primary,
      secondary_metric: secondary,
      status_descriptor: descriptor,
      is_critical_flag: isCritical,
      overall_urgency: overallUrgency,
      integrity_status: integrityStatus,
      total_alerts: alerts.length,
      critical_alerts_count: criticalCount,
      alerts,
      audit_hash: null,
      audit_note:
        "HMAC audit signing is available only in the Python API/CLI where the secret is not public.",
    };
  }

  function init() {
    const form = document.getElementById("audit-form");
    const output = document.getElementById("output");
    const evaluationMetric = document.getElementById("metric-evaluations");
    const statusMetric = document.getElementById("metric-status");
    const alertsMetric = document.getElementById("metric-alerts");

    if (!form || !output || !evaluationMetric || !statusMetric || !alertsMetric) {
      return;
    }

    let evaluationCount = 0;

    form.addEventListener("submit", (event) => {
      event.preventDefault();

      try {
        const result = evaluatePayload({
          task_id: document.getElementById("task_id").value.trim(),
          target_identifier: document.getElementById("target_id").value.trim(),
          primary_metric: document.getElementById("primary_metric").value,
          secondary_metric: document.getElementById("secondary_metric").value,
          status_descriptor:
            document.getElementById("status_descriptor").value.trim() || "NOMINAL",
          is_critical_flag: document.getElementById("is_critical").checked,
        });

        evaluationCount += 1;
        evaluationMetric.textContent = String(evaluationCount);
        statusMetric.textContent = result.overall_urgency;
        alertsMetric.textContent = String(result.total_alerts);
        output.textContent = JSON.stringify(result, null, 2);
      } catch (error) {
        statusMetric.textContent = "Input error";
        alertsMetric.textContent = "0";
        output.textContent =
          error instanceof Error ? error.message : "Unable to evaluate the inputs.";
      }
    });
  }

  window.primeEditingEvaluator = Object.freeze({ evaluatePayload });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
