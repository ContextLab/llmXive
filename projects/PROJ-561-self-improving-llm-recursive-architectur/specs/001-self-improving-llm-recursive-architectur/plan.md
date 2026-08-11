# Implementation Plan: Self-improving LLM: recursive architecture refinement and re‑training

**Branch**: `001-self-improving-llm-recursive-architectur` | **Date**: 2026-06-26
**Spec**: `projects/PROJ-561-self-improving-llm-recursive-architectur/specs/001-self-improving-llm-recursive-architectur/spec.md`
**Input**: Feature specification from `/specs/001-self-improving-llm-recursive-architectur/spec.md`

## Summary

This project implements a recursive pipeline where a GPT model proposes its own architectural modifications, which are validated by an external oracle, re-trained on a subset of OpenWebText, and evaluated on a standard English language modeling benchmark dataset. (replacing GSMK/ARC/BoolQ due to statistical validity concerns). The plan covers three attempted cycles, tracking performance trajectories, parameter counts, and compute efficiency (FLOPs/time). The implementation strictly adheres to CPU-first constraints (GitHub Actions free-tier) and uses verified open datasets.

**Critical Methodological Shift**: The original spec's use of GSM8K/ARC/BoolQ accuracy on a base GPT-2 model is scientifically invalid (signal indistinguishable from zero). The evaluation metrics have been changed to **Perplexity (PPL)** on **Wikitext-2**, which is statistically robust, aligns with the language modeling training objective, and allows for valid detection of architectural improvements.

## Technical Context

**Language/Version**: Python +  
**Primary Dependencies**: `transformers`, `torch` (CPU), `datasets`, `scikit-learn`, `pandas`, `numpy`, `psutil`, `hydra-core` (for config), `pytest`  
**Storage**: Local filesystem (`data/`, `results/`, `models/`); no external DB.  
**Testing**: `pytest` with unit tests for validators, logging, and rollback logic.  
**Target Platform**: Linux (ubuntu-latest GitHub Actions runner).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete 3 cycles within 12 hours wall-clock; peak RAM ≤ 7 GB.  
**Constraints**: CPU-only execution; no CUDA; parameter count increase ≤ 30% per cycle; strict separation of generative (model proposal) and verification (oracle) logic.  
**Scale/Scope**: refinement cycles; [deferred] training samples (OpenWebText subset); [deferred] test samples for Wikitext-2.

> **Deferred**: Exact sample counts for OpenWebText training subset are set to [deferred] to ensure feasibility. Specific architectural modification types are determined at runtime by the model's proposal, constrained by the [deferred] parameter limit.

## Constitution Check

**Status**: PASSED (with explicit mitigation strategies for V and VII).

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `config.py`. All datasets fetched via `datasets.load_dataset` with streaming or explicit version tags. `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs in `research.md` are taken from the verified list. Citations in `research.md` will be validated by the Reference-Validator Agent. **Gate**: The Reference-Validator Agent runs on `research.md` citations before the plan is finalized or executed. |
| **III. Data Hygiene** | **PASS** | Checksums for downloaded datasets recorded in `data/` manifest. No in-place modification; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | `results/trajectory.json` is the single source for performance metrics; all paper figures derived via script from this file. |
| **V. Versioning Discipline** | **PASS** | Content hashes computed for all artifacts in `data/` and `code/`. **Mechanism**: A dedicated `update_state_timestamp()` function in `utils/versioning.py` updates the `state/...yaml` file with `updated_at` timestamps whenever an artifact in `data/` or `code/` changes. |
| **VI. Performance Metric Attribution** | **PASS** | Metrics (Wikitext-2 PPL) computed against baseline using bootstrap CI; improvements attributed only to architectural changes, not evaluation variance. |
| **VII. Data Source Independence** | **PASS** | Verification logic (oracle) is a separate module (`pipeline/oracle.py`) from generative logic (`pipeline/generator.py`); no data used for evaluation influences the modification proposal. |

## Project Structure

### Documentation (this feature)

```text
specs/001-self-improving-llm-recursive-architectur/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-561-self-improving-llm-recursive-architectur/
├── code/
│   ├── config.py                # Hyperparameters, constraints, paths
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── loader.py            # Model and dataset loading (FR-001, FR-011)
│   │   ├── generator.py         # Model self-proposal logic
│   │   ├── validator.py         # External oracle check (FR-021, FR-003, FR-020, FR-019)
│   │   ├── modifier.py          # Apply architecture change (FR-002)
│   │   ├── trainer.py           # Training loop (FR-004)
│   │   ├── evaluator.py         # Benchmark runner (FR-005)
│   │   ├── stats.py             # Bootstrap and Trend Direction (FR-006, FR-009, FR-010)
│   │   └── orchestrator.py      # Main loop, retry logic, termination (FR-007, FR-012, FR-015)
│   ├── utils/
│   │   ├── logging.py           # JSON logging (T009)
│   │   ├── metrics.py           # FLOPs calculation (FR-008)
│   │   ├── monitoring.py        # System monitoring (psutil) (SC-005)
│   │   └── versioning.py        # State file updates (Constitution V)
│   └── main.py                  # Entry point
├── tests/
│   ├── unit/
│   │   ├── test_config.py       # T008
│   │   └── test_metrics.py      # T066 (replaced)
│   └── integration/
│       └── test_pipeline.py
├── data/
│   ├── raw/                     # Downloaded datasets (streamed or cached)
│   └── processed/               # Pre-processed subsets
├── results/
│   ├── trajectory.json          # T034 (Generated)
│   ├── logs/                    # T034 (Generated)
│   └── models/                  # Checkpoints
└── requirements.txt
```

**Structure Decision**: Single project structure chosen to minimize overhead and simplify data flow for a research pipeline. All logic is modularized to allow independent testing of the generator, validator, and trainer.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **External Oracle (Validator)** | Prevents infinite regression and circular validation (Constitution VII). | A purely internal evaluation would allow the model to "hallucinate" improvements without ground truth. |
| **Retry Logic & Termination** | Ensures robustness against transient failures and prevents resource exhaustion on degradation (FR-012, FR-015). | A simple "run 3 times" loop would fail completely on the first error or continue running a degraded model. |
| **Streaming Data Loader** | Required to stay within 7 GB RAM constraint while using real OpenWebText data. | Loading the full dataset into memory would exceed RAM limits and crash the runner. |
| **Control Arm** | Needed to disentangle "model proposal" effect from "parameter increase" effect (Methodology concern). | Without a control arm, the study cannot support the "self-improving" claim. |

## Phase Mapping to Requirements

- **FR-001 (Model Loader)**: Implemented in `pipeline/loader.py` as `load_model(device='cpu')` with explicit verification.
- **FR-002 (One Modification)**: Implemented in `pipeline/modifier.py` as `apply_single_modification()`.
- **FR-003 (Param Check)**: Implemented in `pipeline/validator.py` as `check_param_constraint()`.
- **FR-004 (Training Config)**: Implemented in `pipeline/trainer.py` as `validate_training_config()`.
- **FR-005 (Eval Order)**: Implemented in `pipeline/evaluator.py` as `run_benchmarks(order=['Wikitext-2'])`.
- **FR-006 (Bootstrap)**: Implemented in `pipeline/stats.py` as `paired_bootstrap_ci()`.
- **FR-007 (Loop)**: Implemented in `pipeline/orchestrator.py` as `run_cycles(count=3)`.
- **FR-008 (FLOPs)**: Implemented in `utils/metrics.py` as `calculate_flops()`.
- **FR-009 (Trend)**: Implemented in `pipeline/stats.py` as `compute_trend_direction()`.
- **FR-010 (Trade-off)**: Implemented in `pipeline/stats.py` as `compute_trade_off_metrics()`.
- **FR-011 (Backoff)**: Implemented in `pipeline/loader.py` as `retry_with_backoff()`.
- **FR-012 (Retry)**: Implemented in `pipeline/orchestrator.py` as `handle_training_failure()`.
- **FR-015 (Termination)**: Implemented in `pipeline/orchestrator.py` as `check_termination()`.
- **FR-019 (Param Check Step)**: Implemented in `pipeline/validator.py` as `check_param_constraint()`.
- **FR-020 (Distinctness)**: Implemented in `pipeline/validator.py` as `distinctness_validator()`.
- **FR-021 (Oracle)**: Implemented in `pipeline/validator.py` as `external_oracle_check()`.
- **SC-001/002 (Bootstrap)**: Implemented in `pipeline/stats.py`.
- **SC-003 (Trend)**: Implemented in `pipeline/stats.py`.
- **SC-004 (Trade-off)**: Implemented in `pipeline/stats.py`.
- **SC-005 (Monitoring)**: Implemented in `utils/monitoring.py` using `psutil`.