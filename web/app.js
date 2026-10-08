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
    if (String(value).trim() === "") {
      throw new Error(`${label} is required.`);
    }
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

  const EXAMPLES = Object.freeze({
    nominal: { primary_metric: 14.5, secondary_metric: 3.2, status_descriptor: "NOMINAL", is_critical_flag: false },
    elevated: { primary_metric: 29.4, secondary_metric: 14.8, status_descriptor: "DISCORDANT", is_critical_flag: false },
    critical: { primary_metric: 18.0, secondary_metric: 15.0, status_descriptor: "ANOMALY", is_critical_flag: true },
  });

  function init() {
    const form = document.getElementById("audit-form");
    const output = document.getElementById("results-content");
    const empty = document.getElementById("empty-state");
    if (!form || !output || !empty) return;
    const field = (id) => document.getElementById(id);
    const errorBox = field("form-error");
    const presets = [...document.querySelectorAll("[data-preset]")];
    let runCount = 0;
    let lastResult = null;

    function clearErrors() {
      errorBox.hidden = true;
      errorBox.textContent = "";
      for (const input of form.querySelectorAll("[aria-invalid]")) input.removeAttribute("aria-invalid");
    }

    function setPreset(key) {
      const example = EXAMPLES[key];
      if (!example) return;
      for (const [name, value] of Object.entries(example)) {
        const id = name === "is_critical_flag" ? "is_critical" : name;
        if (id === "is_critical") field(id).checked = value;
        else field(id).value = String(value);
      }
      for (const button of presets) {
        const selected = button.dataset.preset === key;
        button.classList.toggle("active", selected);
        button.setAttribute("aria-pressed", String(selected));
      }
      clearErrors();
    }

    presets.forEach((button) => button.addEventListener("click", () => setPreset(button.dataset.preset)));
    form.addEventListener("input", () => {
      clearErrors();
      presets.forEach((button) => {
        button.classList.remove("active");
        button.setAttribute("aria-pressed", "false");
      });
    });

    function makeFinding(alert) {
      const box = document.createElement("article");
      box.className = "alert-card" + (alert.urgency === "CRITICAL_STAT_PANIC" ? " critical" : "");
      const title = document.createElement("h4");
      title.textContent = alert.summary;
      const source = document.createElement("div");
      source.className = "source";
      source.textContent = alert.origin_worker + " · " + alert.urgency;
      const details = document.createElement("p");
      details.textContent = alert.technical_details;
      box.append(title, source, details);
      return box;
    }

    function render(result) {
      lastResult = result;
      runCount += 1;
      field("run-count").textContent = runCount + (runCount === 1 ? " run" : " runs");
      empty.hidden = true;
      output.hidden = false;
      const critical = result.overall_urgency === "CRITICAL_STAT_PANIC";
      const elevated = result.overall_urgency === "ELEVATED_RISK";
      const outcome = document.querySelector(".outcome-card");
      outcome.className = "outcome-card" + (critical ? " critical" : elevated ? " elevated" : "");
      field("result-status").textContent = critical ? "Critical" : elevated ? "Elevated" : "Nominal";
      field("result-description").textContent = critical
        ? "The critical override was set. Review the triggered demonstration rules."
        : elevated ? "One or more configured threshold or descriptor checks were triggered."
        : "No configured rules were triggered for these inputs.";
      field("result-integrity").textContent = result.integrity_status;
      field("result-alert-count").textContent = String(result.total_alerts);
      field("result-critical-count").textContent = String(result.critical_alerts_count);
      field("alert-summary").textContent = result.total_alerts + (result.total_alerts === 1 ? " finding" : " findings");
      const list = field("alert-cards");
      list.replaceChildren();
      if (result.alerts.length === 0) {
        const message = document.createElement("div");
        message.className = "no-alerts";
        message.textContent = "No configured decision rules were triggered.";
        list.append(message);
      } else result.alerts.forEach((alert) => list.append(makeFinding(alert)));
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      clearErrors();
      try {
        for (const id of ["task_id", "target_id", "primary_metric", "secondary_metric"]) {
          if (!field(id).value.trim()) {
            field(id).setAttribute("aria-invalid", "true");
            throw new Error("Complete all required fields before evaluating.");
          }
        }
        render(evaluatePayload({
          task_id: field("task_id").value.trim(),
          target_identifier: field("target_id").value.trim(),
          primary_metric: field("primary_metric").value,
          secondary_metric: field("secondary_metric").value,
          status_descriptor: field("status_descriptor").value.trim() || "NOMINAL",
          is_critical_flag: field("is_critical").checked,
        }));
      } catch (error) {
        errorBox.hidden = false;
        errorBox.textContent = error instanceof Error ? error.message : "Invalid input.";
      }
    });

    field("copy-json").addEventListener("click", async () => {
      if (!lastResult) return;
      const button = field("copy-json");
      try {
        await navigator.clipboard.writeText(JSON.stringify(lastResult, null, 2));
        button.textContent = "Copied";
      } catch {
        button.textContent = "Copy unavailable";
      }
    });

    field("download-json").addEventListener("click", () => {
      if (!lastResult) return;
      const file = new Blob([JSON.stringify(lastResult, null, 2) + "\n"], { type: "application/json" });
      const url = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = url;
      link.download = "prime-editing-evaluation.json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    });
  }

  window.primeEditingEvaluator = Object.freeze({ evaluatePayload });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
