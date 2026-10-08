"""
Command-Line Interface for PrimeEditing-Designer: pegRNA Primer Binding & RT Template Agent.
"""
import argparse
import csv
import math
import sys

from .agents import PrimeEditingCoordinator
from .models import FrontierPayload

coordinator = PrimeEditingCoordinator()

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
        description="PrimeEditing-Designer: pegRNA Primer Binding & RT Template Agent",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="TARGET-GEN-01")
    p_audit.add_argument("--primary", type=float, default=29.4)
    p_audit.add_argument("--secondary", type=float, default=15.1)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = FrontierPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = coordinator.process(payload)
        print("=" * 80)
        print("  PRIMEEDITING-DESIGNER: PEGRNA PRIMER BINDING & RT TEMPLATE AGENT")
        print(
            "  Domain: Genome Engineering | "
            "Repository-defined prime-editing thresholds"
        )
        print(
            f"  Task: {dossier['task_id']} | "
            f"Status: [{dossier['overall_status']}] | "
            f"Total Alerts: {dossier['total_alerts']}"
        )
        print("=" * 80)
        for alert in dossier["alerts"]:
            print(f"\n  [{alert['status']}] from {alert['origin_agent']}:")
            print(f"  Summary: {alert['summary']}")
            print(f"  Details: {alert['technical_details']}")
            print(f"  Action:  {alert['actionable_remediation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[PrimeEditingCoordinator]:\n{ans}\n")
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
            "overall_status",
            "total_alerts",
            "critical_count",
            "consensus_summary",
        ]
        out_fields = fieldnames + [name for name in result_fields if name not in fieldnames]
        out_rows = []

        for row_number, row in enumerate(rows, start=2):
            try:
                payload = FrontierPayload(
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

            dossier = coordinator.process(payload)
            row_dict = dict(row)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["critical_count"] = dossier["critical_count"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
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
            from .server import create_app
        except ImportError:
            print(
                "FastAPI / uvicorn not installed. "
                "Install the API extra with 'pip install -e .[api]'.",
                file=sys.stderr,
            )
            return 1

        app = create_app()
        if app is None:
            print(
                "FastAPI is unavailable. Install the API extra with "
                "'pip install -e .[api]'.",
                file=sys.stderr,
            )
            return 1

        print(
            "Starting PrimeEditing-Designer: pegRNA Primer Binding & RT Template "
            f"Agent on http://{args.host}:{args.port}"
        )
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
