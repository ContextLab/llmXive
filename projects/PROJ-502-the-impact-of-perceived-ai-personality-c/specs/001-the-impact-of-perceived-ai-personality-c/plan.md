# Implementation Plan: The Impact of Perceived AI Personality Consistency on User Trust (Revised Scope)

**Branch**: `001-ai-personality-consistency-trust` | **Date**: 2024-05-22 | **Spec**: `specs/001-the-impact-of-perceived-ai-personality-c/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-perceived-ai-personality-c/spec.md`

## Summary

This feature implements an observational study to determine if **textual variance** (sentiment and lexical diversity) within conversation sessions predicts **session engagement** (interaction length) in the DailyDialog dataset. 

**Critical Scope Revision**: The original hypothesis regarding "AI Personality Consistency" and "User Trust" has been formally revised. The DailyDialog dataset is a static snapshot of human-human dialogues without longitudinal user IDs, timestamps, or AI-specific traits. Therefore, the study **cannot** test AI personality or cross-session trust. The scope is now strictly limited to: "Does variance in sentiment/lexical diversity within a conversation predict the length of that conversation?" This is a proxy analysis for engagement dynamics, with explicit limitations regarding AI personality and trust. The "Proxy Validity Analysis" (KS test against a non-existent AI-human reference) has been removed as scientifically invalid.

The technical approach involves downloading DailyDialog, filtering for valid sessions, computing turn-level metrics, and running Generalized Linear Models (GLM) for count data. The implementation is strictly constrained to CPU-tractable methods to run within GitHub Actions free-tier limits (limited CPU, 7GB RAM, h runtime).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: See `requirements.txt` below.
**Storage**: Local filesystem (`data/raw`, `data/processed`, `output/figures`). No external database.
**Testing**: `pytest` with `pytest-cov`. Contract tests against YAML schemas.
**Target Platform**: Linux (GitHub Actions Free Tier Runner).
**Project Type**: Research Pipeline / CLI.
**Performance Goals**: Runtime ≤ 6 hours; Peak Memory ≤ 7GB (dynamic batching).
**Constraints**: No GPU usage; no 8-bit/4-bit quantization; no large-LLM inference; strict memory management.
**Scale/Scope**: Processing a large-scale subset of conversation turns from the DailyDialog dataset.; generating statistical figures.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

### Requirements.txt (Pinned Dependencies)
*This file ensures Verified Accuracy (Constitution Principle II).*
```text
datasets==2.14.0
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
statsmodels==0.14.0
torch==2.0.1+cpu --index-url https://download.pytorch.org/whl/cpu
transformers==4.30.2
seaborn==0.12.2
matplotlib==3.7.2
pyyaml==6.0
pytest==7.4.0
pytest-cov==4.1.0
```

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Notes |
|-----------|--------|-------------------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds, and checksums for all external datasets. Code will be deterministic. |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset citations to the provided "Verified datasets" block. All URLs will be validated against the primary source before use. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data (`data/raw`), immutable derivation steps (`data/processed`), and PII scanning logic in the ingestion script. |
| **IV. Single Source of Truth** | **PASS** | All statistical outputs will be generated programmatically from `data/processed` and stored in `output/`. No manual entry in reports. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts will be computed and stored in `state/projects/PROJ-502-the-impact-of-perceived-ai-personality-c.yaml`. The `updated_at` timestamp in this file will be updated on every artifact change. |
| **VI. Confounding Mitigation** | **PASS** | Plan explicitly includes control variables (session length, turn count) in GLM models. The 'Turn-Level Lag' design (Turns 1 to N-1 for predictor, Turn N for outcome) is used to minimize immediate circularity. |
| **VII. Construct Operationalization** | **PASS** | Plan defines 'Engagement' strictly via behavioral proxies (length). The 'AI Personality' construct is explicitly removed from the operationalization due to data limitations, and the study is framed as analyzing 'Textual Variance'. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-perceived-ai-personality-c/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── metrics.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Config loading
├── ingestion.py         # FR-001: Download, filter, checksum
├── metrics.py           # Turn-level metric computation (Variance, TTR)
├── analysis.py          # GLM, Linear Regression, Power Analysis
├── viz.py               # Plot generation
├── utils.py             # Dynamic batching, memory management
└── main.py              # Orchestration script
tests/
├── unit/
│   ├── test_ingestion.py
│   ├── test_metrics.py
│   └── test_analysis.py
├── contract/
│   └── test_schemas.py
└── integration/
    └── test_end_to_end.py
data/
├── raw/                 # Downloaded zip/parquet (checksummed)
└── processed/           # Filtered sessions, computed metrics (JSON/CSV)
output/
├── figures/             # PNG plots
└── reports/             # JSON summary of analysis
```

**Structure Decision**: Single `code/` directory with modular scripts. This minimizes overhead for a research pipeline and aligns with the "Single Source of Truth" principle by keeping data processing and analysis in one cohesive codebase. No separate frontend/backend is required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dynamic Batching** | DailyDialog size may exceed 7GB RAM if loaded entirely. | Loading all data at once risks OOM on free-tier runners. |
| **Turn-Level Lag** | Prevents immediate circularity where predictor and outcome are identical. | Standard correlation would conflate variance with length within the same turn. |
| **Reframed Hypothesis** | DailyDialog lacks AI traits and longitudinal data. | Attempting to measure 'AI Personality' or 'Cross-Session Trust' would be scientifically invalid and impossible to execute. |
| **Removed Proxy Validity** | No valid AI-human reference dataset exists for KS test. | The previous plan to use a non-existent dataset for validity checking was scientifically unsound and has been removed. |