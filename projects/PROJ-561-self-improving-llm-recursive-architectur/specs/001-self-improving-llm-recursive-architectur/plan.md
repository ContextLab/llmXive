# Implementation Plan: Self-improving LLM: recursive architecture refinement and re‑training

**Branch**: `001-self-improving-llm-recursive-architectur` | **Date**: 2026-06-16 | **Spec**: `specs/001-self-improving-llm-recursive-architectur/spec.md`
**Input**: Feature specification from `/specs/001-self-improving-llm-recursive-architectur/spec.md`

## Summary

This project implements a recursive self-improvement pipeline for a GPT 124M model. The system downloads a base checkpoint, prompts the model to propose a single architectural modification, applies the change (constrained to ≤30% parameter increase), re-trains for a short duration on an OpenWebText subset, and evaluates performance on GSM8K, ARC-Challenge, and Wikitext-2.

**Critical Scope Adjustment**: Due to the strict 6-hour time limit and 7GB RAM constraint of the GitHub Actions free-tier runner, the **primary deliverable is a Single Cycle (US-1)**. The 3-cycle trajectory (US-2) is re-classified as a "Scaling Study" that will only be attempted if the single cycle completes successfully within 1.5 hours. If the single cycle exceeds the time limit, the job terminates, and the result is recorded as "Incomplete - Timeout".

**Data Integrity Policy**: The pipeline enforces a strict **Fail-Fast** policy for all datasets (OpenWebText, GSM8K, ARC-Challenge, Wikitext-2). If these datasets cannot be loaded from their standard HuggingFace sources, the pipeline **terminates immediately** with a specific error code. **Synthetic data is NOT permitted for any part of the experiment**, including training or evaluation. Training on synthetic data renders the "recursive improvement" hypothesis untestable, and evaluation on synthetic data yields meaningless metrics. The experiment is designed to fail if verified data sources are unavailable.

The implementation strictly adheres to CPU-only constraints and incorporates rigorous statistical validation (paired bootstrap) and separation of generative (modification proposal) and verification (benchmark evaluation) logic to prevent infinite regression, addressing concerns raised by simulated reviewers (von Neumann, Wolfram).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `datasets`, `accelerate` (CPU config), `scikit-learn` (bootstrap), `scipy` (curve fitting), `pyyaml`, `pandas`  
**Storage**: Local filesystem (`data/` for cached datasets, `results/` for metrics)  
**Testing**: `pytest` (unit tests for modification logic, integration tests for pipeline cycles)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free-tier)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Single cycle runtime ≤1.5 hours; Peak RAM ≤7 GB; Evaluation latency ≤30 minutes per cycle  
**Constraints**: No GPU/CUDA; No 8-bit/4-bit quantization; Parameter count ≤130% of baseline; Strict separation of generative and verification logic (Constitution Principle VII); No synthetic data for training or evaluation  
**Scale/Scope**: cycle (Primary); 3 cycles (Scaling Study, conditional); ~10k-50k training samples (subset of OpenWebText); 3 benchmarks per cycle

> **Note on Dataset Availability**: The plan relies on OpenWebText, GSMK, and ARC-Challenge. If standard HuggingFace loaders fail to retrieve these datasets, the pipeline **terminates immediately**. No synthetic data is permitted as a fallback. The experiment is designed to fail gracefully if verified data sources are unavailable, ensuring that no invalid scientific claims are made.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seed fixing, and use of canonical dataset loaders. |
| **II. Verified Accuracy** | **FAIL (if data unavailable)** | Plan requires citations to be validated against primary sources. If benchmark data is unavailable, the principle is **not** met, and the run is labeled "Failed - Data Unavailable". Synthetic data is not permitted for any part of the experiment. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of downloaded data and derivation logging. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics trace to `results/trajectory.json` and `data/` artifacts. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; state file updated on change. |
| **VI. Performance Metric Attribution** | **PASS** | Metrics (GSMK, ARC, ECE) are measured against pre-modification baselines using paired bootstrap. |
| **VII. Data Source Independence** | **PASS** | **Critical Implementation Detail**: The "Generative Logic" (model proposing changes) uses **only** the training loss on OpenWebText and model weights. The evaluation set (GSM8K/ARC) is **never** used to generate the modification prompt. This addresses von Neumann's concern about infinite regression. |

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
│   ├── requirements.txt
│   ├── main.py                 # Entry point for pipeline
│   ├── config.py               # Hyperparameters, seeds, constraints
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── loader.py           # Dataset loading (with Fail-Fast for all datasets)
│   │   ├── model.py            # Model loading, modification application
│   │   ├── trainer.py          # CPU training loop
│   │   ├── evaluator.py        # Benchmark evaluation (GSM8K, ARC, ECE)
│   │   └── stats.py            # Bootstrap testing, decay fitting
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py          # Structured logging, checkpointing
│   │   └── memory.py           # RAM monitoring, gradient checkpointing
│   └── tests/
│       ├── test_pipeline.py
│       ├── test_model_mod.py
│       └── test_stats.py
├── data/
│   ├── raw/                    # Downloaded datasets (cached)
│   └── processed/              # Preprocessed subsets
├── results/
│   ├── trajectory.json         # Main output artifact
│   └── logs/                   # Cycle logs
└── specs/                      # Specification docs
```

**Structure Decision**: Single project structure with modular `pipeline/` components. This ensures tight coupling between the modification logic and the training loop while maintaining separation of concerns (Generative vs. Verification) as required by Constitution Principle VII. The `utils/memory.py` module is critical for managing the 7GB RAM constraint on the free-tier runner.

## Complexity Tracking

| Design Decision | Why Needed | Constraint / Mitigation |
| :--- | :--- | :--- |
| **Single Cycle Primary** | Required by US-1 to verify the mechanism. 3 cycles (US-2) is a scaling study due to time constraints. | Attempting 3 cycles on free-tier risks timeout, invalidating the entire experiment. |
| **Fail-Fast for All Datasets** | Required to prevent invalid scientific claims on synthetic data. Synthetic data cannot measure reasoning or language modeling. | Allowing synthetic data for any part of the experiment would render the "recursive improvement" hypothesis untestable. |
| **Paired Bootstrap Testing** | Required by US-1 and SC-001/002 to establish statistical significance without parametric assumptions on small benchmark samples. | Standard t-tests assume normality which may not hold for accuracy metrics on small held-out sets; bootstrap is more robust. |
| **Memory Management Module** | Required to fit GPT-2 124M + training overhead into 7GB RAM. | Standard PyTorch loading often exceeds substantial memory thresholds with gradient accumulation; explicit gradient checkpointing, CPU offloading, and batch size reduction are necessary. |
| **No Synthetic Data Fallback** | Required because synthetic data lacks semantic structure for training or evaluation. | Relying on synthetic data would invalidate the scientific hypothesis. |

## Risk Mitigation

- **RAM Overflow**: Use `gradient_checkpointing`, `batch_size=2` (reducing to 1 if >6.5GB), and a hard "Memory Watchdog" that proactively reduces batch size if RAM exceeds 6.5GB. If usage > 7GB, kill the process to prevent system crash.
- **Timeout**: Strict time limit per cycle. If exceeded, terminate and log "Timeout".
- **Dataset Unavailability**: Fail immediately for all datasets. No fallback to synthetic data.
- **Model Proposal Failure**: Implement validation step. Retry up to 2 times. If still invalid, log failure and proceed to next cycle (or terminate if single cycle).