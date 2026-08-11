# Implementation Plan: Self-improving LLM: recursive architecture refinement and re‑training

**Branch**: `001-self-improving-llm-recursive-architectur` | **Date**: 2026-06-26 | **Spec**: `specs/001-self-improving-llm-recursive-architectur/spec.md`
**Input**: Feature specification from `/specs/001-self-improving-llm-recursive-architectur/spec.md`

## Summary

This project implements a single-cycle and three-cycle recursive refinement pipeline for a GPT model. The system downloads a base model, prompts it to propose an architectural modification (validated by an external oracle), re-trains on a subset of OpenWebText, and evaluates performance on GSMK, ARC-Challenge, and BoolQ. The plan ensures strict adherence to CPU constraints (GitHub Actions free-tier), handles dataset streaming to fit memory, and implements rigorous statistical testing (paired bootstrap) and resource tracking.

**Critical Methodological Update**: To address scientific soundness concerns regarding baseline variance, the plan now includes a **Baseline Variance Estimation** step. This step runs the *evaluation* phase (inference only) of the baseline model (Cycle 0) three times with different random seeds for data shuffling/sampling. This establishes a variance floor for the metrics without requiring re-training, thus preserving the -hour time budget mandated by User Story and complying with FR-004's "exactly 1 epoch" training constraint for modification cycles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `psutil`, `accelerate` (CPU config)  
**Storage**: Local filesystem for model checkpoints (ephemeral), `results/` for logs and trajectory JSON.  
**Testing**: `pytest` with unit tests for validation logic, integration tests for pipeline steps.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free-tier: vCPU, ~7 GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete 3 attempted cycles (including retries) within 12 hours wall-clock; peak RAM ≤ 7 GB.  
**Constraints**: No GPU usage; strict parameter count increase ≤ 30% from baseline; distinctness of modifications; strict separation of evaluation and generation.  
**Scale/Scope**: GPT base model; A large-scale dataset comprising hundreds of thousands of OpenWebText samples (streamed/sampled); 3 cycles.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

**Status**: PASSED (with explicit mitigation strategies for V and VII).

| Principle | Requirement | Plan Mitigation / Compliance |
| :--- | :--- | :--- |
| **I. Reproducibility** | Pin seeds, fetch canonical data. | `code/config.py` will pin `seed=42` for training, but `code/utils/stats.py` will use a separate seed list `[, 123, 456]` for the baseline variance estimation step. Datasets loaded via `datasets.load_dataset` with explicit revision/commit hash where available. |
| **II. Verified Accuracy** | Verify external citations. | All dataset URLs in `research.md` are restricted to the "Verified datasets" block provided in the prompt. No fabricated URLs. |
| **III. Data Hygiene** | Checksums, no in-place mods. | `code/utils/data_loader.py` will compute SHA256 of downloaded shards and record in `data/checksums.json`. Derived data (samples) written to new files. |
| **IV. Single Source of Truth** | Trace figures to data/code. | `results/trajectory.json` is the sole source for the performance plot. All metrics derived programmatically from `results/logs/cycle_N.log`. |
| **V. Versioning Discipline** | Content hashes, update timestamps. | `code/utils/versioning.py` will generate content hashes for `config.py`, `pipeline/`, and `data/` and update the project state YAML. The utility file is implemented as part of this scope to ensure its availability and correct functionality.|
| **VI. Performance Metric Attribution** | Comparative analysis, consistent eval. | `pipeline/evaluator.py` uses fixed prompts and sampling seeds for GSM8K/ARC/BoolQ. Metrics (accuracy, ECE) compared against Cycle 0 baseline. The baseline comparison now accounts for evaluation variance via the 3-seed estimation. |
| **VII. Data Source Independence** | Eval data independent of mod process. | **Critical Mitigation**: The "External Oracle" (FR-021) and benchmark datasets (GSM8K, etc.) are strictly read-only during the modification proposal phase. The model proposes changes based on *past* cycle logs, not current evaluation data. The evaluation data is never used to generate the next modification proposal directly, preventing circular validation. |

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
│   ├── __init__.py
│   ├── config.py                # Hyperparameters, constraints, paths
│   ├── main.py                  # Entry point, orchestrator
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_loader.py       # Streaming, checksumming, sampling
│   │   ├── logging.py           # JSON log formatting, rotation
│   │   ├── stats.py             # Bootstrap, linear regression, variance estimation
│   │   └── versioning.py        # Hashing, state updates
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── loader.py            # Model loading (CPU)
│   │   ├── modifier.py          # Prompting, distinctness check, oracle
│   │   ├── trainer.py           # Training loop, FLOPs profiling
│   │   └── evaluator.py         # Benchmark runners, metric calculation
│   └── tests/
│       ├── __init__.py
│       ├── unit/
│       │   ├── test_config.py
│       │   ├── test_external_validator.py  # T066
│       │   ├── test_rollback.py            # T067
│       │   └── test_stats.py
│       └── integration/
│           └── test_pipeline.py
├── data/
│   ├── raw/                     # Streamed shards (if cached)
│   ├── processed/               # Sampled datasets
│   └── checksums.json
├── results/
│   ├── logs/                    # cycle_N.log
│   ├── trajectory.json          # T034
│   └── metrics/
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/` and `tests/` at root) chosen to minimize overhead and simplify dependency management for a research pipeline. The `pipeline/` directory isolates the core logic (load, modify, train, evaluate) from utilities and configuration, facilitating the separation of concerns required by Constitution Principle VII.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **External Oracle Check (FR-021)** | Prevents circular validation where the model validates its own bad ideas. | Direct self-validation leads to infinite regression or hallucinated "improvements" (per Von Neumann feedback). |
| **Streaming Data Loader** | OpenWebText exceeds 7 GB RAM; full download impossible. | Downloading full dataset fails CI; synthetic data violates Constitution III (Data Hygiene). |
| **Paired Bootstrap (FR-006)** | Small sample sizes (GSM8K) require non-parametric significance testing. | Standard t-tests assume normality which may not hold for small, skewed accuracy distributions. |
| **Baseline Variance Estimation** | Scientific rigor requires distinguishing model change effects from evaluation noise. | Running a single baseline evaluation is insufficient to establish a variance floor; re-training baseline 3 times would exceed the 2-hour time limit (US-1). Evaluation-only re-sampling provides the necessary variance estimate within the time budget. |
| **Retry Logic (FR-012)** | CI instability (OOM, transient HF errors) is expected. | Single-run pipeline has high failure rate; requires robustness to complete 3 cycles. |

