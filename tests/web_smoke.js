"use strict";

global.window = {};
global.document = {
  readyState: "loading",
  addEventListener() {},
};

require("../web/app.js");

const evaluate = window.primeEditingEvaluator.evaluatePayload;

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

let result = evaluate({
  task_id: "T1",
  target_identifier: "TARGET-1",
  primary_metric: 10,
  secondary_metric: 4,
  status_descriptor: "NOMINAL",
  is_critical_flag: false,
});
assert(result.overall_urgency === "ROUTINE", "nominal case should be routine");
assert(result.total_alerts === 0, "nominal case should have no alerts");
assert(result.audit_hash === null, "static app must not fabricate an HMAC hash");

result = evaluate({
  task_id: "T2",
  target_identifier: "TARGET-2",
  primary_metric: 30,
  secondary_metric: 4,
  status_descriptor: "NOMINAL",
  is_critical_flag: false,
});
assert(result.overall_urgency === "ELEVATED_RISK", "primary breach should elevate");
assert(result.total_alerts === 1, "primary breach should create one alert");

result = evaluate({
  task_id: "T3",
  target_identifier: "TARGET-3",
  primary_metric: 10,
  secondary_metric: 4,
  status_descriptor: "NOMINAL",
  is_critical_flag: true,
});
assert(
  result.overall_urgency === "CRITICAL_STAT_PANIC",
  "critical flag should trigger critical status"
);

let blankRejected = false;
try {
  evaluate({
    task_id: "T4",
    target_identifier: "TARGET-4",
    primary_metric: "",
    secondary_metric: 4,
    status_descriptor: "NOMINAL",
    is_critical_flag: false,
  });
} catch (error) {
  blankRejected = /required/.test(String(error));
}
assert(blankRejected, "blank numeric input must be rejected");

console.log("Browser evaluator smoke test passed.");
