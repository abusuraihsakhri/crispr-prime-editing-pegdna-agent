# CRISPR Prime Editing pegRNA Agent

### [Open the Live Application →](https://abusuraihsakhri.github.io/crispr-prime-editing-pegdna-agent/)

A small Python and browser toolkit for applying deterministic, repository-defined threshold rules to prime-editing-related numeric inputs and status descriptors.

> **Scope:** the current source code is a rule-based evaluator. It does **not** design pegRNA sequences, derive PBS thermodynamics from nucleotide sequences, perform off-target analysis, predict editing efficiency, or implement a validated experimental/clinical decision rule. The numeric thresholds are software demonstration constants and should not be treated as biological recommendations.

## Features

- Deterministic evaluation of primary and secondary numeric metrics.
- Status-keyword checks for configured discordance/anomaly terms.
- Single-record and CSV batch CLI workflows.
- FastAPI endpoints for health, evaluation, chat-style mock responses, and audit metadata.
- In-memory HMAC-SHA256 audit chaining for the audited Python workflow.
- Pattern-based outbound identifier guard for several common identifier formats.
- Static GitHub Pages interface that runs entirely in the browser with no backend request.
- Docker image and Compose configuration.
- Pytest regression tests, lightweight Ruff checks, dependency auditing, and container smoke tests in GitHub Actions.

## Live application

The GitHub Pages application evaluates the same **root worker thresholds** used by the audited Python workflow:

- primary metric > 25 → elevated alert;
- secondary metric > 12 → elevated alert;
- critical flag → critical alert;
- configured discordance/anomaly keywords → elevated conformance alert.

The browser build intentionally does not implement HMAC signing. A public static page cannot safely contain the secret required for HMAC authentication. Browser inputs remain local to the page; the shipped JavaScript makes no network requests.

Python-in-the-browser is not used. The browser workflow is simple deterministic logic, so Pyodide/PyScript would add substantial WebAssembly download and startup overhead without providing useful functionality.

## Installation

Python 3.9 or newer is supported.

```bash
git clone https://github.com/abusuraihsakhri/crispr-prime-editing-pegdna-agent.git
cd crispr-prime-editing-pegdna-agent

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -e ".[api,test]"
```

The audited root CLI/API requires an HMAC secret:

```bash
export AUDIT_SECRET_KEY="replace-with-a-random-secret-at-least-16-characters"
```

Do not commit real secrets. `.env` and common local environment variants are ignored by Git.

## Usage

### Audited root CLI

Single evaluation:

```bash
python cli.py audit \
  --task-id TASK-001 \
  --target TARGET-01 \
  --primary 28.5 \
  --secondary 14.2 \
  --status DISCORDANT
```

Batch CSV:

```bash
python cli.py batch -i sample.csv -o results.csv
```

Verify the current in-memory HMAC chain:

```bash
python cli.py verify-audit
```

Start the root FastAPI service:

```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Lightweight packaged CLI

The installed console command uses the `prime_editing_agent` package:

```bash
crispr-prime-editing-pegdna-engine audit
crispr-prime-editing-pegdna-engine batch -i sample.csv -o results.csv
crispr-prime-editing-pegdna-engine serve
```

The repository contains both the audited `agents/` workflow and the lighter `prime_editing_agent/` workflow. They are retained for compatibility and have separate status models.

## CSV input

Expected columns:

| Column | Required | Meaning |
| --- | --- | --- |
| `task_id` | No | Task identifier; a default is used if blank |
| `target_identifier` | No | Non-secret target identifier |
| `primary_metric` | No | Finite numeric primary value |
| `secondary_metric` | No | Finite numeric secondary value |
| `is_critical_flag` | No | `true/false`, `yes/no`, `on/off`, or `1/0` |
| `status_descriptor` | No | Free-text status descriptor |

Invalid non-finite numbers or unrecognized boolean strings are rejected instead of being silently coerced.

## REST API

The audited root API exposes:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Service status |
| GET | `/metrics` | In-memory process counters |
| POST | `/api/audit` | Evaluate a task and create an HMAC-linked audit record |
| POST | `/api/chat` | Deterministic mock supervisory response |
| GET | `/api/audit/logs` | Return audit metadata and integrity status |

FastAPI also serves the generated OpenAPI schema at `/openapi.json`.

## Privacy and security notes

- The identifier guard is a regex-based safety filter, not a HIPAA de-identification guarantee.
- The HMAC audit trail is in memory only; it is lost when the process exits.
- HMAC integrity detects mutation of entries within the current process state; it is not a durable append-only ledger.
- The repository does not require external model/API credentials for its current deterministic workflows.
- The static browser application has a restrictive Content Security Policy and does not make network requests.
- GitHub Actions are pinned to immutable commit SHAs.

## Testing and checks

Install development tooling:

```bash
python -m pip install -e ".[api,test,dev]"
```

Run the same core checks used by CI:

```bash
python -m pip check
ruff check --select E9,F63,F7,F82 .
python -m compileall -q agents prime_editing_agent cli.py enrichment.py simulator.py
node --check web/app.js
pytest -q
pip-audit
```

## Docker

Create a local `.env` from `.env.example`, set a real secret, then run:

```bash
docker compose up --build
```

The container runs as a non-root user and exposes the API on port 8000.

## Project layout

```text
.
├── agents/                    # Audited multi-worker Python workflow
├── prime_editing_agent/       # Lightweight domain-specific package
├── tests/                     # Regression and API tests
├── web/                       # Static GitHub Pages application
├── cli.py                     # Audited root CLI
├── enrichment.py              # Generic enrichment scaffolding retained for compatibility
├── simulator.py               # Local stress/simulation utility
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Browser compatibility

The static application uses standard HTML, CSS, and modern JavaScript without a framework. Current versions of Chrome, Edge, Firefox, and Safari are expected to work. No browser storage is required.

## License

MIT. See [LICENSE](LICENSE).
