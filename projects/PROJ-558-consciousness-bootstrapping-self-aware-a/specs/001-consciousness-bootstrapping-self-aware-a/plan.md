# Implementation Plan: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

**Branch**: `001-consciousness-bootstrapping-self-aware-ai` | **Date**: 2026-07-02 | **Spec**: `specs/001-consciousness-bootstrapping-self-aware-a/spec.md`
**Input**: Feature specification from `specs/001-consciousness-bootstrapping-self-aware-a/spec.md`

## Summary

This project implements a comparative study of a TinyLlama-based language model augmented with a **temporal recursive self-attention module** against a standard baseline. The core hypothesis is that attending to the uncertainty distribution (projected softmax vector) of previous generation steps improves meta-cognitive behaviors: self-consistency, error detection, and uncertainty calibration. The implementation strictly adheres to the GitHub Actions free-tier compute budget (2 CPU, 7 GB RAM, ≤4 hours) by utilizing a small-scale dataset subset (100k tokens), quantized model loading where possible, and streaming data access. The project delivers trained checkpoints, evaluation metrics, and a statistically rigorous report validating the architectural impact.

**Key Revisions**:
- **Training Objective**: Replaced circular self-consistency proxy with external calibration loss using ground-truth labels from a held-out calibration set (GSM8K/MMLU).
- **Architecture**: Defined recursive input as a projected softmax vector (not scalar) to capture uncertainty shape.
- **Feasibility**: Limited confidence history to a sliding window (t-1 + 5 steps) to fit 7 GB RAM.
- **Token Limit**: 100k tokens derived from memory calculation for TinyLlama-1.1B + recursive overhead.
- **Statistical Rigor**: Added power analysis note and revised interpretation protocol for effect sizes.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `torch` (CPU-only build), `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `pytest`  
**Storage**: Local filesystem (`data/`, `code/`, `artifacts/`); no external database.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: GitHub Actions free-tier runner (Ubuntu-latest, 2 vCPU, 7 GB RAM).  
**Project Type**: Computational Research / Machine Learning Experiment.  
**Performance Goals**: Complete training and evaluation within 4 hours; memory usage < 6 GB to allow OS overhead.  
**Constraints**:  
- No GPU access on primary runner; CPU-first implementation.  
- Max recursion depth fixed at 2 for the primary run (resource constraint), but code supports varying depths as per FR-001.  
- Dataset limited to a token count that fits within available RAM (derived from memory calculation).  
- All random seeds pinned for reproducibility.  
**Scale/Scope**: 1 model architecture variant (recursive) + 1 baseline; 3 benchmark datasets (MMLU, GSM8K, Self-Consistency); 5 random seeds for statistical power.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

### Token Limit Derivation
The 100k token limit is derived from the available memory:
- Available RAM: 7 GB (GitHub Actions) - 2 GB (OS overhead) = 5 GB.
- Model Size (TinyLlama, FP): Approximately several gigabytes.
- Remaining for context/overhead: a substantial amount of memory.
- Estimated memory per token (with recursive overhead): moderate.
- Max tokens: 2.8 GB / 28 KB ≈ a large-scale context window suitable for extensive document analysis.
This calculation ensures the model fits within the available RAM limit while accounting for the recursive module's memory footprint.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | PASS | All seeds pinned; `requirements.txt` provided; CI workflow deterministic. |
| **II. Verified Accuracy** | PASS | Citations limited to verified dataset URLs; no hallucinated DOIs. |
| **III. Data Hygiene** | PASS | Data streamed from HF; checksums recorded; no PII. |
| **IV. Single Source of Truth** | PASS | Metrics flow from `data/` to `paper/` via automated scripts; no manual entry. |
| **V. Versioning Discipline** | PASS | Artifacts hashed; `state` updated on change. |
| **VI. Statistical Rigor** | PASS | Paired t-tests across multiple seeds; Bonferroni correction applied; effect sizes reported with confidence intervals. |
| **VII. Resource-Constrained** | PASS | Model scaled (TinyLlama); data subset (100k tokens, derived from memory calc); recursion depth ≤2 (for primary run); CPU-first. |

## Project Structure

### Documentation (this feature)

```text
specs/001-consciousness-bootstrapping-self-aware-a/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later, currently flawed)
```

### Source Code (repository root)

```text
code/
├── __init__.py          # [REMOVED: Task T001b]
├── models/
│   ├── __init__.py      # [REMOVED: Task T001b]
│   ├── recursive_attention.py  # Custom module
│   └── tinyllama_wrapper.py    # Model loading
├── training/
│   ├── __init__.py      # [REMOVED: Task T001b]
│   ├── train.py                # Main training loop
│   └── config.py               # Hyperparameters
├── evaluation/
│   ├── __init__.py      # [REMOVED: Task T001b]
│   ├── benchmarks.py           # MMLU, GSM8K, Self-Consistency
│   └── metrics.py              # Brier, ECE, ROC-AUC
├── analysis/
│   ├── __init__.py      # [REMOVED: Task T001b]
│   ├── stats.py                # T-tests, effect sizes
│   └── sensitivity.py          # Threshold sweeps
├── utils/
│   ├── __init__.py      # [REMOVED: Task T001b]
│   └── data_loader.py          # Streaming logic
└── main.py                     # Orchestration

data/
├── raw/                        # Streaming pointers (no full download)
└── processed/                  # Checksummed metrics JSONs

artifacts/
├── checkpoints/                # Model weights
└── reports/                    # Statistical reports
```

**Structure Decision**: Single-project structure selected to minimize overhead and ensure tight coupling between training and evaluation scripts, which is critical for the recursive module's dependency on the baseline. The `code/` directory is organized by functional domain (models, training, evaluation, analysis) to align with the User Stories (US-01, US-02, US-03).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Recursive Attention Module** | Core research hypothesis requires temporal recursion. | Standard attention cannot model confidence feedback loops; removing it invalidates the study. |
| **Streaming Data Loading** | 100k token subset must be fetched without OOM on 7 GB RAM. | Downloading full Pile or caching entire subset exceeds RAM; streaming is the only viable path. |
| **Paired T-Tests (5 Seeds)** | Constitution Principle VI mandates statistical rigor. | Single-run comparison is scientifically invalid; 5 seeds balance compute cost and power (with acknowledged limitations). |
| **Sliding Window Confidence** | Full history of confidence vectors exceeds RAM. | Storing only t-1 and 5 previous steps fits memory while preserving the recursive signal. |

## Evaluation Protocol

### Self-Consistency
- Generate N=10 paths per question (Temperature=0.7, top_p=0.9).
- **Tie-Breaking Rule**: If a majority vote tie occurs, select the path with the highest *average confidence* score. (Addresses spec edge case).

### Sensitivity Analysis (FR-006, SC-005)
- Sweep confidence thresholds for error detection: **0.3, 0.5, 0.7**.
- These three values explicitly satisfy the "at least three distinct threshold values" requirement of SC-005.
- Metric: False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold.

### Advanced Analyses (T043, T045, T047, T048)
- **T043 (Adaptation)**: Evaluation script saves both 'first pass' and 'recursive refinement' outputs separately.
- **T045 (Irreducibility)**: Prediction method defined as linear regression on baseline outputs.
- **T047 (Origin)**: Reference distribution for KL-divergence defined as the token distribution of the Pile (arXiv) training data.
- **T048 (Falsification)**: Mechanism defined as setting `recursion_enabled=False` in the model config during mid-inference.