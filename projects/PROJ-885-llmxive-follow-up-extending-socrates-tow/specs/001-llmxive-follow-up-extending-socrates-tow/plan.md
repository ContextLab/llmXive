# Implementation Plan: Dynamic Socio-Cognitive State Injection

**Branch**: `001-dynamic-state-injection` | **Date**: 2026-07-14 | **Spec**: `specs/001-dynamic-state-injection/spec.md`
**Input**: Feature specification from `/specs/001-dynamic-state-injection/spec.md`

## Summary

The project implements a CPU‑tractable adapter for LLM mediation that **dynamically** injects socio‑cognitive state signals (e.g., “escalating”, “cultural‑friction”) into the system prompt based on a lightweight logistic‑regression classifier that operates on **turn‑level dialogue text** (every few turns) and auxiliary scenario metadata. The primary hypothesis is that this dynamic injection improves consensus gap closure in high‑emotion, culturally diverse conflict scenarios compared to a static baseline.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `scikit-learn` (logistic regression, stats), `pandas`, `transformers` (CPU‑only inference, `torch` CPU backend), `datasets` (for optional loading utilities), `pytest`
- **Storage**: Local JSON/CSV files under `data/`; all files checksummed.
- **Testing**: `pytest` with unit, integration, and contract tests.
- **Target Platform**: GitHub Actions free tier (2 CPU, ≈7 GB RAM, no GPU).
- **Performance Goals**: ≤45 s inference/trajectory, total runtime ≤6 h, memory <7 GB.
- **Constraints**: No CUDA, no 8‑bit/4‑bit quantization, no large‑scale model training.

## Constitution Check

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/config.py`; all data generated locally; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | No external citations are used; all references are internal or to verified code repositories. |
| **III. Data Hygiene** | **PASS** | Raw data in `data/raw/` immutable; derived data in `data/processed/` with SHA‑256 checksums recorded in project state. |
| **IV. Single Source of Truth** | **PASS** | Figures and statistics are generated directly from scripts reading `data/processed/`. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked; state file updated on artifact changes. |
| **VI. Low‑Resource Feasibility** | **PASS** | Logistic regression classifier and CPU‑only LLM inference; memory‑aware batching. |
| **VII. Dynamic State Injection Isolation** | **PASS** | Paired experiment runs use identical trajectories and LLMs; only the prompt differs between Adapter and Static conditions. |

## Project Structure

### Documentation (this feature)

```
specs/001-dynamic-state-injection/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── experiment.schema.yaml
│   └── report.schema.yaml
└── tasks.md
```

### Source Code (repository root)

```
projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/
├── code/
│   ├── __init__.py
│   ├── config.py                # paths, seeds, hyper‑parameters
│   ├── data/
│   │   ├── generator.py         # SoCRATES trajectory generation (US‑1)
│   │   └── loader.py            # Dataset loading & validation (now a no‑op generator)
│   ├── models/
│   │   ├── classifier.py        # Logistic‑Regression dynamic state classifier (FR‑002)
│   │   └── evaluator.py         # Topic‑localized consensus‑gap evaluator (FR‑005)
│   ├── experiments/
│   │   ├── runner.py            # Main experiment loop (US‑2, FR‑003, FR‑004)
│   │   └── prompts.py           # Static vs. dynamic prompt templates
│   ├── analysis/
│   │   ├── metrics.py           # Consensus‑gap calculation (FR‑005)
│   │   └── stats.py             # Normality test, paired t‑test / Wilcoxon, Holm‑Bonferroni (FR‑006, FR‑007)
│   └── main.py                  # Entry point
├── data/
│   ├── raw/                     # (empty – data generated locally)
│   ├── processed/               # Generated trajectories, experiment logs
│   └── results/                 # Final statistical reports
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── contracts/
│   ├── dataset.schema.yaml
│   ├── experiment.schema.yaml
│   └── report.schema.yaml
├── requirements.txt
└── README.md
```

**Rationale**: Keeping a single, self‑contained repository simplifies reproducibility and ensures all steps run on the free‑tier CI without external data downloads.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | All steps respect CPU‑only constraints, FR‑002, FR‑004, and the Constitution. | N/A |
