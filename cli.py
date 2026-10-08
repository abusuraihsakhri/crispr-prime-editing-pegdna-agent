"""
Command Line Interface for Crispr Prime Editing Pegdna Agent.
"""
import argparse
import csv
import math
import sys

from agents.base import AuditLogger
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off", ""}


def _parse_bool(value, field_name: str = "is_critical_flag") -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{field_name} must be one of: true/false, yes/no, on/off, or 1/0; got {value!r}"
    )


def _parse_float(value, default: float, field_name: str) -> float:
    if value is None or str(value).strip() == "":
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric; got {value!r}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{field_name} must be finite; got {value!r}")
    return parsed


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="crispr-prime-editing-pegdna-agent",
        description="Crispr Prime Editing Pegdna Agent",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print("  CRISPR PRIME EDITING PEGDNA AGENT")
        print(
            "  Rule-based multi-worker evaluator | "
            "Repository-defined thresholds"
        )
        print(
            f"  Dossier ID: {dossier.dossier_id} | "
            f"Urgency: [{dossier.overall_urgency.value}]"
        )
        print("=" * 80)
        for alert in dossier.alerts:
            print(f"\n  [{alert.urgency.value}] from {alert.origin_worker}:")
            print(f"  Summary: {alert.summary}")
            print(f"  Details: {alert.technical_details}")
            print(f"  Action:  {alert.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Crispr Prime Editing Pegdna Agent Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(
            f"Audit Trail Blocks: {len(trail)} | "
            f"Cryptographic Integrity Verified: {valid}"
        )
        return 0

    if args.command == "batch":
        try:
            with open(args.input, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
        except FileNotFoundError:
            print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
            return 1
        except PermissionError:
            print(f"Error: Permission denied reading '{args.input}'.", file=sys.stderr)
            return 1

        result_fields = [
            "overall_urgency",
            "integrity_status",
            "total_alerts",
            "audit_hash",
        ]
        out_fields = fieldnames + [name for name in result_fields if name not in fieldnames]
        out_rows = []

        for row_number, row in enumerate(rows, start=2):
            try:
                payload = SystemTaskPayload(
                    task_id=row.get("task_id") or "TASK-01",
                    target_identifier=row.get("target_identifier") or "TARGET-01",
                    primary_metric=_parse_float(
                        row.get("primary_metric"), 15.0, "primary_metric"
                    ),
                    secondary_metric=_parse_float(
                        row.get("secondary_metric"), 5.0, "secondary_metric"
                    ),
                    status_descriptor=row.get("status_descriptor") or "NOMINAL",
                    is_critical_flag=_parse_bool(row.get("is_critical_flag")),
                )
            except ValueError as exc:
                print(f"Error: CSV row {row_number}: {exc}", file=sys.stderr)
                return 1

            dossier = supervisor.process_task(payload)
            row_dict = dict(row)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        try:
            with open(args.output, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=out_fields)
                writer.writeheader()
                writer.writerows(out_rows)
        except PermissionError:
            print(f"Error: Permission denied writing '{args.output}'.", file=sys.stderr)
            return 1

        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from agents.api import app
        except ImportError:
            print(
                "FastAPI / uvicorn not installed. "
                "Install the API extra with 'pip install -e .[api]'.",
                file=sys.stderr,
            )
            return 1

        print(
            "Starting Crispr Prime Editing Pegdna Agent API server on "
            f"http://{args.host}:{args.port}"
        )
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
