# Implementation Plan: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

**Branch**: `001-consciousness-bootstrapping-self-aware-ai` | **Date**: 2026-07-02 | **Spec**: `specs/001-consciousness-bootstrapping-self-aware-a/spec.md`
**Input**: Feature specification from `/specs/001-consciousness-bootstrapping-self-aware-a/spec.md`

## Summary

This project implements a computational study to investigate whether a recursive self-attention mechanism, trained with a joint loss on a subset of the Pile dataset, improves meta-cognitive metrics (self-consistency, error detection, uncertainty calibration) compared to a static-confidence baseline. The implementation adheres strictly to the GitHub Actions free-tier constraints (limited CPU and RAM) by utilizing a parameter-efficient TinyLlama model with a modified architecture, streaming data to avoid OOM, and limiting training epochs. The plan resolves previous fabrication concerns by ensuring all metrics are derived from real model inference and statistical testing, not placeholders.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `torch` (CPU-only build), `scikit-learn`, `numpy`, `pandas`, `peft`, `accelerate`  
**Storage**: Local ephemeral storage on CI runner; artifacts (checkpoints, results JSON) saved to `data/` and `results/`.  
**Testing**: `pytest` for unit tests on data loaders and metric calculators; integration tests for the training/evaluation loop.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Research / Machine Learning Pipeline.  
**Performance Goals**: Training complete within 4 hours; Evaluation complete within 1 hour.  
**Constraints**: Maximize RAM usage within constrained memory limits.; No GPU available on default runner (GPU offload handled via Kaggle escape hatch if CUDA is explicitly required by a specific kernel, but the plan prioritizes CPU-tractable methods); Recursion depth swept at, 2, 3 (primary run at 2); random seeds.  
**Scale/Scope**: B parameter model (TinyLlama); A training subset comprising a large volume of tokens (streamed); 5 random seeds; Several benchmark datasets (MMLU, GSM8K, Self-Consistency proxy).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

- **I. Reproducibility**: **PASS**. The plan mandates pinned seeds, explicit `requirements.txt`, and streaming data fetching from canonical HuggingFace sources. All random seeds will be logged in the `StatisticalReport`.
- **II. Verified Accuracy**: **PASS**. All dataset URLs cited in `research.md` are restricted to the verified list provided in the prompt. No fabricated metrics will be used; all results will be computed via `scikit-learn` and `torch`.
- **III. Data Hygiene**: **PASS**. Data will be streamed or downloaded to `data/raw/` with checksums recorded. No in-place modification; derived metrics stored in `data/processed/`.
- **IV. Single Source of Truth**: **PASS**. The `StatisticalReport` will be generated programmatically from the `EvaluationResult` JSON files. No hand-typed statistics.
- **V. Versioning Discipline**: **PASS**. Artifacts (checkpoints, result files) will be hashed. The plan includes steps to update the project state file upon completion.
- **VI. Statistical Rigor**: **PASS**. The plan explicitly includes paired t-tests across 5 seeds, Bonferroni correction, and effect size calculation (Cohen's d), as required by the constitution. The low sample size (n=5) is acknowledged as a limitation, with effect sizes prioritized over p-values. A power analysis is included to justify the exploratory nature.
- **VII. Resource-Constrained Architectural Fidelity**: **PASS**. The plan uses a 1.1B model (TinyLlama) on CPU with streaming and gradient accumulation to fit within 7 GB RAM. Recursion depth is capped at a conservative limit for primary runs. The GPU escape hatch (Kaggle) is strictly a feasibility fallback for the *same* methodology if CPU OOM occurs, preserving the method's integrity.

## De Facto Requirements (Addressing Malformed Spec Text)

The source spec contains malformed text in FR-001 and placeholders in FR-002. To ensure testability while maintaining provenance, the following operational mandates are established:

1.  **FR-001 Override**: The text "...for a The research will investigate..." is syntactically broken. The plan interprets the *intent* as an instruction to perform a sensitivity sweep of recursion depths (1, 2, 3). This "Depth Sweep" is the binding implementation requirement, superseding the broken text for execution purposes.
2. **FR-002 Override**: The text "...first [deferred] tokens..." is incomplete. The plan adopts **[deferred] tokens** as the operational value for this cycle. This value is derived from compute constraints (4-hour budget) and is the binding constraint for the implementation.

## Project Structure

### Documentation (this feature)

```text
specs/001-consciousness-bootstrapping-self-aware-a/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (See Cross-Reference below)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── checkpoint.py          # ModelCheckpoint class definition
│   ├── recursive_attention.py   # Custom module implementation
│   └── model_factory.py         # Instantiation logic
├── data/
│   ├── __init__.py
│   ├── loaders.py               # Streaming dataset logic
│   └── preprocessing.py         # Tokenization logic
├── training/
│   ├── __init__.py
│   ├── train_loop.py            # Main training script
│   └── loss_functions.py        # Joint loss implementation (Self-Consistency Proxy)
├── evaluation/
│   ├── __init__.py
│   ├── results.py               # EvaluationResult class definition
│   ├── metrics.py               # Brier, ECE, ROC-AUC, Consistency
│   ├── benchmarks.py            # MMLU, GSM8K runners
│   └── runner.py                # Inference orchestration
├── analysis/
│   ├── __init__.py
│   ├── stats.py                 # T-tests, corrections
│   └── sensitivity.py           # Threshold sweeps
├── utils/
│   ├── __init__.py
│   └── logging.py
└── main.py                      # Entry point

tests/
├── __init__.py
├── contract/
│   ├── test_schema_validation.py
│   └── test_data_integrity.py
├── unit/
│   ├── test_metrics.py
│   └── test_recursive_module.py
└── integration/
    └── test_training_loop.py
```

**Contract Cross-Reference**:
- `contracts/evaluation-schema.schema.yaml`: Validates outputs from **US-02** (Evaluation).
- `contracts/model_checkpoint.schema.yaml`: Validates outputs from **US-01** (Training).
- `contracts/statistical_report.schema.yaml`: Validates outputs from **US-03** (Analysis).

**Structure Decision**: Single project structure (`code/`) selected to minimize overhead and align with the compute constraints. The separation of `models`, `data`, `training`, and `evaluation` ensures modularity for the statistical analysis phase. `__init__.py` files are included in all directories to ensure proper Python package recognition and testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Custom Recursive Attention Module | Required by FR-001 to attend to confidence distribution of previous step. | Standard attention does not model temporal self-reference; a simple loop would not capture the "recursive self-modeling" hypothesis. |
| Joint Loss Function (Self-Consistency Proxy) | Required by FR-002 to train confidence prediction using the spec-defined proxy. | Standard cross-entropy only optimizes token prediction; self-referential proxy losses create circular validation, but this is the mandated method. |
| GPU Escape Hatch (Kaggle) | Required if 1.1B model on CPU exceeds 7 GB RAM despite optimizations. | CPU-only execution is the primary goal; GPU is a fallback for feasibility, not a replacement for the method. |
| Sensitivity Sweep (Depth 1, 2, 3) | Required to address the "varying depth" intent in malformed FR-001. | Single depth runs cannot investigate the influence of depth variation. |
| Static-Confidence Baseline | Required to isolate temporal coherence from architectural complexity. | Shuffled-attention baseline tests a different architectural class; static-confidence isolates the specific variable of interest (temporal recursion). |

## Spec Coverage Notes

- **FR-001 (Malformed)**: The spec text "for a The research will investigate..." is syntactically broken. The plan interprets this as an instruction to perform a sensitivity sweep of recursion depths (1, 2, 3) and explicitly flags the spec for correction.
- **FR-002 (Malformed)**: The spec text "first [deferred] tokens" is incomplete. The plan adopts "[deferred] tokens" as the operational value for this cycle and flags the spec for correction.
- **SC-001**: The plan explicitly includes a `percentage_difference` metric in the StatisticalReport to satisfy the requirement. The `stats.py` script will compute `((mean_recursive - mean_baseline) / mean_baseline) * 100`.

## Data & Compute Strategy

- **Data**: Streaming `arXiv` subset of The Pile (100k tokens) for training. `GSM8K` and `MMLU` for evaluation. All data is real, open, and programmatic.
- **Compute**: Primary execution on GitHub Actions CPU (multiple cores, standard RAM). If OOM occurs, the system automatically re-runs the *same* configuration on a Kaggle GPU with increased VRAM capacity as a feasibility fallback.
- **Metrics**: All metrics (Self-Consistency, Brier, ECE, ROC-AUC) are computed from real model inference on benchmark data. No hardcoded values or placeholders are used.

## Statistical Analysis Plan

- **Test**: Paired t-test (recursive vs. static-confidence baseline) across the 5 seeds.
- **Correction**: **Bonferroni correction** exclusively for the 3 primary metrics (Consistency, Calibration, Error Detection). The schema enforces `bonferroni` exclusively.
- **Sensitivity**: Sweep confidence thresholds across a range of low to high values. and report false positive/negative rates.
- **Power Analysis**: The sample size (n=5) is the maximum feasible for a 1.1B model on CPU within 4 hours. The study acknowledges low statistical power and frames results as exploratory. Effect sizes (Cohen's d) are prioritized over p-values to quantify the magnitude of any observed effect despite the small n.
- **Percentage Difference**: The `stats.py` script will explicitly calculate and report the percentage difference in self-consistency scores as a distinct metric in the `StatisticalReport`.

## Risk Mitigation

- **Circular Loss**: The training loss is tautological (self-consistency proxy). The plan mitigates this by framing the hypothesis as an architectural comparison (recursive vs. static) rather than an absolute claim of "truth."
- **Dataset Size**: A relatively small number of tokens is small for a 1.1B model. The hypothesis is reframed to test "architectural influence in a data-scarce regime" rather than full convergence.
- **OOM**: Gradient checkpointing and streaming are used. If OOM occurs, the Kaggle GPU escape hatch is triggered.