# Implementation Plan: llmXive follow-up: extending "PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents "

**Branch**: `001-gene-regulation` | **Date**: 2026-07-13 | **Spec**: [spec.md]
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-planbench-xl/spec.md`

## Summary

This project implements a comparative study to evaluate whether augmenting LLM tool-use agents with lightweight, rule-based "failure signature" retrieval significantly improves recovery rates from implicit tool failures. The system will execute two agents (Baseline and Augmented) on a *synthetically constructed* subset of the PlanBench-XL dataset. The "implicit failure" condition is created by programmatically injecting specific error patterns into tool outputs for a subset of tasks that originally have a "success" ground truth. The Baseline agent relies solely on internal LLM reasoning, while the Augmented agent performs a static string-matching check against a pre-constructed JSON index of these *injected* failure signatures. The study measures task completion success rates (against the original, untouched ground truth) and applies a **two-proportion z-test** (Constitution Principle VII) to determine significance (p < 0.05). A power analysis is conducted to ensure the sample size (targeting the Constitution's task subset) is sufficient to detect a [deferred] effect size. All operations are constrained to run on a CPU-only GitHub Actions runner (2 cores, 7GB RAM) within 6 hours.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `datasets` (HuggingFace), `transformers` (CPU-only), `torch` (CPU), `scikit-learn`, `pandas`, `pytest`, `requests`
**Storage**: Local file system (`data/`), JSON index (`data/failure_signatures.json`)
**Testing**: `pytest` (unit tests for signature logic, integration tests for agent execution)
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Research/Computational Experiment
**Performance Goals**: Total runtime ≤ 6 hours; Memory footprint ≤ 7 GB RAM.
**Constraints**: No GPU/CUDA; No large-LLM fine-tuning; Deterministic signature indexing; Statistical rigor (p < 0.05, z-test only).
**Scale/Scope**: Synthetically modified subset of PlanBench-XL (up to 327 tasks); 2 agents; 1 statistical report.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Note |
|-----------|--------|-----------------|
| **I. Reproducibility** | **Pass** | Plan mandates pinned seeds, isolated virtualenv, and re-download of canonical datasets on every run. Synthetic injection logic is deterministic and versioned. |
| **II. Verified Accuracy** | **Pass** | Plan restricts dataset URLs to the verified list in the prompt; no fabricated citations. |
| **III. Data Hygiene** | **Pass** | Plan requires checksumming raw data in `state/` and treating derived files (indices, logs) as new artifacts. |
| **IV. Single Source of Truth** | **Pass** | Final report numbers must trace to `data/` logs and `code/` analysis scripts. |
| **V. Versioning Discipline** | **Pass** | Plan includes content hashing for the signature index and execution logs. |
| **VI. Deterministic Signature Indexing** | **Pass** | Plan explicitly defines the construction of the JSON index from *synthetic injection logic*, ensuring it is static, CPU-tractable, and independent of the evaluation ground truth. |
| **VII. Statistical Rigor** | **Pass** | Plan mandates the **two-proportion z-test** exclusively (per Constitution Principle VII). A power analysis ensures the sample size (targeting a sufficient number of tasks) is sufficient to detect a [deferred] effect size. If underpowered, the study reports the effect size with a limitation disclaimer rather than performing a fallback test. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/
├── data/
│   ├── raw/                 # Downloaded PlanBench-XL parquet files
│   ├── derived/             # Synthetic failure injection index, filtered task subsets
│   └── logs/                # Execution logs (baseline, augmented)
├── code/
│   ├── __init__.py
│   ├── agents/
│   │   ├── base.py          # Abstract agent class
│   │   ├── baseline.py      # Baseline agent (internal reasoning only)
│   │   └── augmented.py     # Augmented agent (signature retrieval)
│   ├── dataset/
│   │   ├── loader.py        # Data download and parsing
│   │   ├── injector.py      # Synthetic failure injection logic
│   │   └── indexer.py       # Failure signature index construction (from injection logic)
│   ├── analysis/
│   │   └── stats.py         # Statistical testing (z-test only) and reporting
│   └── utils/
│       ├── config.py        # Random seeds, hyperparameters
│       └── logger.py        # Structured logging
├── tests/
│   ├── unit/
│   │   └── test_indexer.py
│   └── integration/
│       └── test_agents.py
├── requirements.txt
└── run_experiment.py        # Entry point for CI
```

**Structure Decision**: A modular Python research structure is selected to separate data ingestion, synthetic injection, agent logic, and statistical analysis. This ensures the "Deterministic Signature Indexing" principle is isolated in `dataset/injector.py` and `indexer.py`, and the "Statistical Rigor" is isolated in `analysis/stats.py`, facilitating verification and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Failure Injection** | Required to create a valid test set where "implicit failures" exist, as the original PlanBench dataset lacks these labels. | Relying on original ground truth would create a circular dependency (index built from outcome). Synthetic injection breaks this tautology. |
| **Dual-Agent Architecture** | Required by FR-003 and FR-004 to isolate the effect of the signature retrieval. | A single agent with a toggle would risk state leakage between runs; separate classes ensure clean isolation of the experimental variable. |
| **Static JSON Index** | Required by Constitution Principle VI and FR-002 for CPU-tractability and determinism. | A dynamic retrieval system (e.g., vector DB) would add unnecessary latency and non-determinism, violating the "lightweight" constraint. |
| **Strict Z-Test** | Required by Constitution Principle VII. | Fisher's Exact Test is rejected to maintain strict adherence to the Constitution's exclusive mandate, with underpowered reporting as the fallback. |

