# Implementation Plan: llmXive follow-up: extending "Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution"

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-16 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary

This feature implements a computational experiment to validate the hypothesis that lightweight syntactic abstractions can substitute for deep predictive modeling (World-in-Agent) in recovering agent performance after failure. The system generates **three independent cohorts** of 500 failed trajectories (N=1500 total) in the ALFWorld environment:
1.  **Baseline Cohort**: Generated with full World-in-Agent (WIA) prediction horizon > 0 using Llama-3-8B.
2.  **Degraded Cohort**: Generated with WIA prediction horizon = 0 using Llama-3-8B (no predictive context).
3.  **Intervention Cohort**: Generated with WIA prediction horizon = 0, but with the rule-based "Syntactic Abstraction" parser active during the failure analysis phase.

The system statistically compares retrieval relevance scores and task completion rates across these three independent groups. The implementation is designed for CPU-only execution on GitHub Actions free-tier runners, prioritizing streaming data processing and lightweight statistical methods.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU mode), `torch` (CPU), `scipy` (stats), `datasets` (streaming), `alfworld` (simulator), `pandas`, `pytest`  
**Storage**: Local filesystem (`data/`), JSON/Parquet for trajectory logs, SQLite for task bank metadata  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Research simulation / Computational experiment  
**Performance Goals**: <6 hours total runtime; <7 GB peak RAM; reproducible seeds  
**Constraints**: No local GPU; no external API calls; no access-gated datasets; deterministic simulation  
**Scale/Scope**: 1500 total failure trajectories (500 per condition); experimental conditions; A statistical test suite.  
**Canonical Sources**: 
- **LLM**: `meta-llama/Llama-3-8B` (Hugging Face)
- **Simulator**: `alfworld` (PyPI package v1.1.0+)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|-----------|--------|-----------|
| **I. Reproducibility** | ✅ Pass | All random seeds pinned in `code/config.py`; ALFWorld simulator deterministic; external data fetched via programmatic loader (or simulated if no open source exists); `requirements.txt` pins versions. |
| **II. Verified Accuracy** | ✅ Pass | **Verification Mechanism**: The Reference-Validator Agent will verify the Hugging Face model ID `meta-llama/Llama-3-8B` and the PyPI package `alfworld` (version `>=1.1.0`) before execution. The plan explicitly names these canonical sources to ensure the 'Verified Accuracy' gate can be performed. |
| **III. Data Hygiene** | ✅ Pass | Raw trajectories stored in `data/raw/`; derivations in `data/derived/`; checksums recorded in `state/...yaml`; no in-place modifications. |
| **IV. Single Source of Truth** | ✅ Pass | All stats/figures trace to `data/derived/stats.csv` and `code/analysis/`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | ✅ Pass | Artifacts carry content hashes; `updated_at` timestamp updated on change. |
| **VI. Validation Independence** | ✅ Pass | **Separation Mechanism**: The 'ground-truth root cause' is extracted strictly from the ALFWorld simulator's low-level state transition log (e.g., `state_id: 123, action: pick, result: fail`), which is independent of the agent's text generation. The 'Frozen Task Bank' is a separate, human-annotated index of task definitions. The scoring logic matches the trajectory's *failure description* to the Task Bank, but the *ground-truth* used for validation is strictly the simulator log, preventing leakage. |
| **VII. Computational Fidelity** | ✅ Pass | Syntactic abstraction implemented as lightweight Python script using `re` and `json`; no retraining/fine-tuning; CPU-only execution planned. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── config/
│   └── config.py              # Pinned seeds, paths, hyperparameters
├── data/
│   ├── raw/                   # Generated trajectories, simulator logs
│   └── derived/               # Processed stats, aggregated scores
├── sim/
│   ├── alfworld_runner.py     # ALFWorld environment wrapper
│   ├── trajectory_generator.py# Generates 1500 failure trajectories (3 cohorts)
│   └── validation.py          # Validates against ground-truth state transitions
├── conditions/
│   ├── degraded.py            # WIA prediction horizon = 0 (Generation Config)
│   └── intervention.py        # WIA=0 + Syntactic Abstraction (Generation Config)
├── retrieval/
│   ├── task_bank.py           # Frozen task bank with human-annotated IDs
│   └── relevance_scorer.py    # Calculates retrieval relevance scores
├── analysis/
│   ├── statistical_tests.py   # Shapiro-Wilk, t-test, Mann-Whitney U (Independent Samples)
│   └── power_analysis.py      # Power calculation for N=1500 (500/group)
└── tests/
    ├── contract/              # Schema validation tests
    ├── integration/           # End-to-end condition tests
    └── unit/                  # Parser, scorer, validator unit tests

requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead; all components are research-specific and tightly coupled; no frontend/backend split needed; tests organized by contract/integration/unit.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All principles satisfied; no violations detected. | N/A |