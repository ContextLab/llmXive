# Implementation Plan: MobileForge Logic Distillation

**Branch**: `930-logic-distillation` | **Date**: 2026-08-27 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/930-logic-distillation/spec.md`

## Summary
This plan implements CPU-tractable logic distillation for the MobileForge framework. It extracts `(UI_state, Corrective_Hint, Action)` triples from raw logs, filters for "failed-then-success" trajectories, and trains a T5-small Encoder-Decoder model to predict action sequences. The implementation strictly adheres to resource constraints (CPU-only, <6h training) and employs rigorous statistical validation (McNemar's test, a priori power analysis) to compare the distilled model against a TinyLlama baseline.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers` (T5-small), `datasets`, `scikit-learn`, `pandas`, `pytest`, `ruff`, `black`
**Storage**: Local filesystem (`data/` for raw/processed data, `models/` for weights), HuggingFace Hub for model loading.
**Testing**: `pytest` (unit, integration, contract tests).
**Target Platform**: Linux (GitHub Actions CPU runner), Android Emulator (for evaluation simulation).
**Project Type**: Research/Data Science Pipeline.
**Performance Goals**: Training ≤ 6 hours on 2 CPU cores, 7GB RAM. Evaluation on N tasks (calculated via power analysis).
**Constraints**: CPU-only execution (CUDA detection = failure), no synthetic data fallbacks, strict memory limits.
**Scale/Scope**: A large-scale set of training triples (sampled if larger), N evaluation tasks (calculated via `power_analysis`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt` pins, random seed management in `utils/`, and dataset checksumming in `state/` (pending creation). |
| **II. Verified Accuracy** | **PENDING** | Requires updated `spec.md` with FR-005 change (McNemar's test) before PASS can be granted. |
| **III. Data Hygiene** | **PASS** | Plan includes `data/` directory structure with checksums. Raw data is read-only; derived data goes to `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | Metrics flow from `utils/metrics.py` and `state/` artifacts to the final report. No hand-typed stats. |
| **V. Versioning Discipline** | **PENDING** | `state/` directory and `artifact_hashes` map are marked "To Be Implemented" in Project Structure. |
| **VI. CPU-Only Inference** | **PASS** | Explicit check for CUDA availability in training script; immediate failure if detected. |
| **VII. Hint-Specific Ablation** | **PASS** | Evaluation phase includes a specific ablation run replacing hints with "retry" prompts. |

## Project Structure

### Documentation (this feature)

```text
specs/930-logic-distillation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── evaluation.schema.yaml
│   └── power_analysis.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/930-llmxive-follow-up-extending-mobileforge/
├── data/
│   ├── raw/                  # Downloaded parquet files
│   ├── processed/            # Filtered triples, train/test splits
│   └── checksums.json        # SHA256 hashes of raw data
├── code/
│   ├── __init__.py
│   ├── config.py             # T008: [To Be Implemented] Env var loading
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── power_analysis.py # T009: [To Be Implemented] calculate_required_n
│   │   ├── metrics.py        # T006: [To Be Implemented] Success Rate, Step Efficiency
│   │   └── emulator.py       # T005: [To Be Implemented] launch, send_action, check_crash
│   ├── pipeline/
│   │   ├── extract.py        # FR-001: Data extraction
│   │   ├── train.py          # FR-002: T5-small training (CPU)
│   │   └── evaluate.py       # FR-003/004/005: Eval + McNemar
│   ├── models/
│   │   └── distilled_t5.py   # Model definition
│   └── main.py               # Entry point
├── tests/
│   ├── contract/             # Schema validation tests
│   ├── integration/          # End-to-end pipeline tests
│   └── unit/                 # Unit tests for utils
├── state/
│   └── validated_n.json      # T009: Output of power analysis [To Be Implemented]
├── requirements.txt          # T001/T002: Pinned dependencies
├── pyproject.toml            # T003: Black/Ruff config
└── .ruff.toml                # T003: Linting config
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) is selected. This aligns with the research nature of the project, keeping data processing, training, and evaluation in a unified pipeline under `code/`. The `state/` directory is explicitly created to satisfy Constitution Principle V and Task T004/T009.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **A Priori Power Analysis** | Required by FR-007 and SC-006 to ensure statistical validity. | Post-hoc power analysis is tautological and prohibited by the spec. |
| **McNemar's Test** | Required by FR-005 for binary paired data. | Paired t-test is statistically invalid for binary outcomes (Success/Fail). |
| **T5-small (Encoder-Decoder)** | Required by FR-002 for conditional generation. | Encoder-only models (e.g., DistilBERT) cannot natively generate variable-length action sequences without complex decoding heads. |
| **Ablation Study (Hint vs. Retry)** | Required by Constitution Principle VII. | Without this, we cannot isolate the "hint-contextualized" reasoning effect from generic context effects. |
| **T009 (Power Analysis)** | Pending Implementation. | Artifact T009 is currently missing; plan acknowledges this status. |

## Implementation Phases

### Phase 0: Setup & Verification
1.  Initialize project structure (`data/`, `code/`, `tests/`, `state/`).
2.  Create `requirements.txt` (T001) and `pyproject.toml`/`.ruff.toml` (T003).
3.  Verify dataset sources (AndroidWorld, ExtractionDataset) and update `research.md`.
4.  **Gate**: Confirm `spec.md` is updated with FR-005 (McNemar's test) to satisfy Constitution Principle II.

### Phase 1: Power Analysis & Setup (FR-007, SC-006)
1.  **Pilot Run**: Execute a small pilot (N=50 tasks) to estimate baseline success rate (p0) for TinyLlama.
2.  **Calculation**: Run `utils/power_analysis.py` (T009) using estimated p0 (or 0.5 fallback) to calculate N.
3.  **Output**: Write `state/validated_n.json` with N and parameters.
4.  **Reporting**: Document a priori parameters in `state/power_report.md` (SC-006).

### Phase 2: Data Extraction & Validation (FR-001)
1.  **Load**: Download raw logs/parquet files.
2.  **Filter**: Extract "failed-then-success" trajectories.
3.  **Validate**: Check `Corrective_Hint` fields for purely linguistic content (no coordinates).
4.  **Control Group**: Ensure a subset of "initial success" trajectories is included to prevent overfitting to error recovery.
5.  **Output**: `data/processed/train_splits.parquet`, `data/processed/test_splits.parquet`.

### Phase 3: Model Training (FR-002, FR-008)
1.  **Feasibility Check**: Run a pilot training (1k samples, 1 epoch) to verify CPU feasibility within 6h.
    *   *Contingency*: If pilot fails, reduce sample size (e.g., 10k) or epochs.
2.  **CUDA Guard**: Implement check in `pipeline/train.py` to abort immediately if CUDA is detected.
3.  **Train**: Train T5-small on CPU.
4.  **Output**: `models/distilled_t5/`.

### Phase 4: Evaluation & Statistical Validation (FR-003, FR-004, FR-005)
1.  **Input Parity**: Ensure TinyLlama baseline receives identical input (UI State + Hint) as T5 model.
2.  **Run**: Evaluate both models on N tasks (from Phase 1).
3.  **Test**: Perform McNemar's test (one-tailed derivation: p/2 if b>c).
4.  **Output**: `state/evaluation_results.json`.

### Phase 5: Sensitivity Analysis (FR-006, SC-005)
1.  **Sweep**: Vary "inconsistency tolerance" (Levenshtein distance) thresholds (0, 1, 2, 3).
2.  **Metric**: Calculate success rates at each threshold.
3.  **Report**: Report variance across thresholds (no hard cutoffs).
4.  **Output**: Append to `state/evaluation_results.json`.

### Phase 6: Ablation & Final Reporting (Constitution VII, SC-006)
1.  **Ablation**: Run evaluation with "retry" prompt instead of `Corrective_Hint`.
2.  **Report**: Document a priori parameters (SC-006) and ablation results in final report.
3.  **Output**: Final `state/final_report.md`.

## Post-Implementation Verification
-   Run `pytest tests/` to validate all contracts.
-   Verify `state/` directory contains all checksums and versioning artifacts.
-   Confirm `spec.md` update is present for Constitution Principle II.