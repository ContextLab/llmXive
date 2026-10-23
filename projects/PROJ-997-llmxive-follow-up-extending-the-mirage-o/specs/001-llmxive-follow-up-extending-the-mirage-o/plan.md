# Implementation Plan: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

**Branch**: `001-llmxive-mipu-gap-bounds` | **Date**: 2026-10-23 | **Spec**: `specs/001-llmxive-mipu-gap-bounds/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-mipu-gap-bounds/spec.md`

## Summary
The project creates a **hardware‑grounded dataset** that pairs training‑side signals (gradient norms, local curvature) with KL‑divergence measured on a real CPU‑based quantized inference engine. A lightweight regression model (Kernel Ridge Regression) is then trained to predict this “policy gap”. Finally, we verify that the predictor respects a theoretical bound (|predicted − actual| < 0.1) across three quantization levels (INT4, INT8, FP8) and that using the predictor in a proxy MIPU loop does not degrade downstream performance.

**Feature‑Justification**: Gradient norm reflects the magnitude of parameter updates, while local curvature (Hessian trace approximation) captures loss‑landscape sharpness; both have been shown to correlate with model sensitivity to weight perturbations and thus to quantization‑induced distribution shifts (see literature on gradient‑norm‑based generalization and curvature‑sensitivity). This provides a principled basis for using them as predictors of KL divergence.

**Power Analysis**: Detecting a Pearson correlation r ≥ 0.8 with α = 0.05 and power = 0.8 requires ≈ 85 samples per quantization level (≈ 255 total). We target **≥ 300 samples** to ensure robustness and to accommodate the stratified split and potential drop‑outs.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers`, `datasets`, `llama-cpp-python`, `scikit-learn`, `numpy`, `pandas`, `pytest`, `onnxruntime` (fallback)  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/metrics/`)  
- **Testing**: `pytest` with contract tests under `tests/contract/`  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (2 vCPU, ≈7 GB RAM) – **CPU‑first**; if llama‑cpp inference on the 7 B model exceeds the 6 h limit, the step auto‑offloads to a Kaggle GPU (GPU escape hatch).  
- **Performance Goals**: End‑to‑end pipeline ≤ 6 h; ≥ 300 samples (statistical power).  
- **Constraints**: All ground‑truth must be obtained from an actual quantized engine (Principle VI). No simulated noise.  

## Constitution Check
| Principle | Status | Action / Evidence |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic llama‑cpp calls, checksummed artifacts. |
| II. Verified Accuracy | PASS | All external resources (GSM8K, Llama‑2‑7B‑4bit) are fetched via verified HF loaders; no invented URLs. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded; immutable derivations; no PII. |
| IV. Single Source of Truth | PASS | Every metric in `metrics.json` traces to a row in `training_sample.parquet`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/`; artifact versioning enforced. |
| VI. Hardware‑Grounded Validation | PASS | Ground‑truth KL computed from real llama‑cpp/ONNX Runtime runs; hardware source logged; fallback to Kaggle GPU is recorded and normalized. |
| VII. Non‑Circular Feature‑Target Independence | PASS | Features extracted from full‑precision model state; targets from separate quantized runs. |

## Project Structure

### Documentation (this feature)

```
specs/001-llmxive-mipu-gap-bounds/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── gap_prediction_result.schema.yaml
│   ├── metrics.schema.yaml
│   ├── predictor.schema.yaml
│   └── training_sample.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

### Source Code (repository root)

```
projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/
├── code/
│   ├── __init__.py
│   ├── cli/
│   │   ├── generate_ground_truth.py   # T015 – GPU‑offload aware, logs hardware_source
│   │   └── validate_dataset_stats.py # T016
│   ├── data/
│   │   ├── extract_features.py        # US‑001 feature extraction
│   │   └── preprocess.py              # T023 – stratified split, PCA, VIF
│   ├── models/
│   │   ├── train_predictor.py         # US‑002
│   │   └── evaluate_predictor.py      # US‑002 & US‑003 – writes gap_predictions.parquet
│   ├── validation/
│   │   └── mipu_benchmark.py          # US‑003 proxy vs baseline
│   └── utils/
│       ├── llama_engine.py            # wrapper for llama‑cpp / ONNX Runtime, records hardware_source
│       └── stats.py                   # VIF, Bonferroni, t‑tests, Shapiro‑Wilk, Wilcoxon fallback
├── data/
│   ├── raw/            # GSM8K download, model files (gguf)
│   ├── processed/      # training_sample.parquet
│   └── metrics/        # metrics.json, bound_report.json, runtime.json
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── requirements.txt
```

**Structure Decision**: A single‑project layout keeps data generation, model training, and validation tightly coupled, ensuring traceability from FRs to concrete artifacts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Hardware‑Engine Wrapper** (T015) | Required by Principle VI; must run real quantized inference. | Simulated noise would violate hardware‑grounded validation. |
| **Stratified Split & PCA** (T023) | Guarantees representation of all three quantization levels and mitigates collinearity (VIF ≤ 10). | Random split could omit a level, breaking SC‑004. |
| **Bonferroni Correction** (SC‑003) | Multiple comparisons (3 quantization levels + t‑test) demand family‑wise error control. | Uncorrected p‑values would inflate Type I error. |
| **Runtime Guard** (T034) | Enforces SC‑005 (≤ 6 h) by measuring wall‑clock time and aborting if exceeded. | No explicit runtime check would leave feasibility unverified. |
| **Sensitivity Sweep** (ε) | Demonstrates that the bound is not an arbitrary choice; robustness across ε ∈ {0.05,0.1,0.15}. | Fixed ε without analysis would be arbitrary. |

## Project Tasks

| ID | Description | FRs addressed | Notes |
|----|-------------|---------------|-------|
| **T015** | `code/cli/generate_ground_truth.py` – generate `training_sample.parquet` by (1) extracting gradient norms & curvature from full‑precision Llama‑2‑7B‑4bit, (2) running llama‑cpp quantized inference (INT4, INT8, FP8) on the same prompts, (3) computing KL divergence. Logs `hardware_source` (CPU or GPU). | FR‑001, FR‑002, FR‑003 | Uses `llama_engine.py`; if CPU cannot finish within 6 h, automatically re‑executes on a Kaggle GPU (GPU escape hatch). |
| **T016** | `code/cli/validate_dataset_stats.py` – compute descriptive stats (means, stds, non‑zero KL proportion) and write `data/metrics/dataset_stats.json`. | FR‑001, FR‑004 (ensures dataset suitability) | Verifies that > 5 % of KL values are non‑zero. |
| **T019** | `code/data/extract_features.py` – compute gradient norms & local curvature per prompt. | FR‑001, FR‑004 | Uses `torch.autograd` on full‑precision model; stores intermediate CSV for reproducibility. |
| **T021** | `code/models/train_predictor.py` – train Kernel Ridge Regression on the joint INT4/INT8/FP8 data (stratified split). | FR‑004, FR‑005 | Saves model artifact `gap_predictor.pkl`. |
| **T022** | `code/models/evaluate_predictor.py` – compute Pearson r, MAE, bound check (|pred‑actual| < 0.1) **on the held‑out validation set**, and write per‑sample predictions to `gap_predictions.parquet` (validated against `gap_prediction_result.schema.yaml`). | FR‑005, FR‑007 | Outputs `metrics.json`. |
| **T023** | `code/data/preprocess.py` – stratified train/val split (by quantization level and prompt length bin), PCA on gradient & curvature, VIF diagnostics (threshold 10). | FR‑004, SC‑001, SC‑004 | Writes split indices to disk. |
| **T027** | `code/validation/mipu_benchmark.py` – run a small RL reasoning task with (a) proxy MIPU loop (predictor) and (b) full‑hardware‑sync baseline; collect final scores. | FR‑006, FR‑007 | Produces paired scores for t‑test. |
| **T028** | `code/validation/mipu_benchmark.py` – compute paired t‑test (Bonferroni‑adjusted) on reasoning scores; if Shapiro‑Wilk rejects normality, fall back to Wilcoxon signed‑rank test. | FR‑006, SC‑003 | Stores `statistical_tests` section in `metrics.json`. |
| **T029** | `code/validation/mipu_benchmark.py` – measure latency of proxy vs. baseline; compute reduction % (target ≥ 90%). | SC‑002 | Writes `latency_reduction` to `metrics.json`. |
| **T030** | `tests/contract/` – contract validation against all YAML schemas. | All FRs (artifact conformity) | Run via `pytest -m contract`. |
| **T034** | `code/cli/measure_runtime.py` – wrap the entire pipeline, record total wall‑clock time, abort if > 6 h, store `runtime.json`. | SC‑005 | Guarantees computational feasibility. |
| **T031** | Documentation update – ensure all figures/tables reference single source of truth. | Principle IV | No code change. |
| **T032** | `quickstart.md` & `research.md` generation – auto‑populate with final metrics. | Deliverable completeness | No runtime effect. |

All tasks are ordered so that data download → feature extraction → ground‑truth generation → dataset validation → model training → evaluation → benchmark → reporting.
