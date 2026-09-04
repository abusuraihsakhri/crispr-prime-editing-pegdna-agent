# CRISPR Prime Editing pegRNA Agent

> **Domain:** Computational Biology & AI Drug Discovery
> **Reference Standards:** wwPDB, IUPAC & CLSI Computational Guidelines

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

CRISPR Prime Editing pegRNA Agent is a computational platform for evaluating and optimizing prime editing guide RNA (pegRNA) designs. It provides deterministic calculation engines for PBS thermodynamics, RT template length optimization, and protocol conformance checking.

---

## Key Capabilities

- **Deterministic Calculation Engine**: Evaluates primary and secondary metrics against reference thresholds for pegRNA design quality.
- **Risk & Urgency Classification**: Multi-tier categorization (ROUTINE, ELEVATED, CRITICAL_STAT) with automated action recommendations.
- **Multi-Agent Architecture**: Specialized workers for QC invariant checking, safety escalation, and protocol conformance.
- **Zero-PHI Outbound Guard**: AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
- **Tamper-Evident HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs for every evaluation.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/crispr-prime-editing-pegdna-agent.git
cd crispr-prime-editing-pegdna-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set required environment variable
export AUDIT_SECRET_KEY="your-secure-audit-key-min-16-chars"
```

---

## Usage

### CLI Commands

#### 1. Single Task Evaluation (Audit)
```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

#### 2. Supervisory Chat Query
```bash
python cli.py chat "What is the system status?"
```

#### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

#### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

#### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `--task-id` | str | TASK-2026-001 | Unique task/case identifier |
| `--target` | str | KEY-TARGET-01 | Genomic target or specimen identifier |
| `--primary` | float | 28.5 | Primary measurement (e.g., PBS Tm in °C) |
| `--secondary` | float | 14.2 | Secondary metric (e.g., RT template length) |
| `--critical` | flag | False | Emergency escalation flag |
| `--status` | str | DISCORDANT | Status/phenotype descriptor |

### Input Data Schema (CSV/JSON)

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `task_id` | str | Yes | Unique task identifier |
| `target_identifier` | str | Yes | Target or specimen key |
| `primary_metric` | float | Yes | Primary measurement value |
| `secondary_metric` | float | No | Secondary measurement value |
| `is_critical_flag` | bool | No | Emergency escalation flag |
| `status_descriptor` | str | No | Status code (NOMINAL, DISCORDANT, ANOMALY, etc.) |

---

## REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Service health check |
| GET | `/metrics` | Operational metrics |
| POST | `/api/audit` | Submit task for evaluation |
| POST | `/api/chat` | Supervisory chat query |
| GET | `/api/audit/logs` | Retrieve and verify audit trail |

---

## Testing

```bash
# Set test environment variable
export AUDIT_SECRET_KEY="test-audit-secret-key-2026-secure"

# Run full test suite
pytest -v

# Run simulation benchmark
python simulator.py 1000
```

---

## Security

- **AUDIT_SECRET_KEY**: Required environment variable (minimum 16 characters). Never hardcode secrets.
- **Zero-PHI Guard**: Automatically blocks outbound data containing SSNs, MRNs, emails, phone numbers, and patient names.
- **HMAC-SHA256 Audit Trail**: Each entry is cryptographically signed and chained to detect tampering.

---

## Docker Deployment

```bash
# Create .env file with required variables
echo "AUDIT_SECRET_KEY=your-production-audit-key-here" > .env

# Build and run
docker-compose up --build
```

---

## Project Structure

```
crispr-prime-editing-pegdna-agent/
├── agents/                    # Core multi-agent system
│   ├── base.py               # Security, PHI guard, audit trail
│   ├── models.py             # Pydantic data models
│   ├── supervisor.py         # Orchestrator
│   ├── workers.py            # Specialized evaluation workers
│   ├── api.py                # FastAPI REST server
│   ├── metrics.py            # Prometheus metrics
│   ├── learning.py           # Bayesian calibration engine
│   ├── llm_factory.py        # LLM provider factory
│   └── streamer.py           # WebSocket telemetry
├── prime_editing_agent/       # Domain-specific engine
│   ├── engine.py             # Core algorithmic engine
│   ├── agents.py             # PBS, RT, Flap agents
│   ├── cli.py                # Domain CLI
│   └── server.py             # Domain REST server
├── tests/                     # Test suite
├── cli.py                     # Main CLI entry point
├── simulator.py               # High-throughput simulation
├── enrichment.py              # Enrichment feature suite
├── web/index.html             # Operations console
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```
