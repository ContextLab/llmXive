# Implementation Plan: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

**Branch**: `001-llmxive-mipu-gap-bounds` | **Date**: 2026-10-24 | **Spec**: `specs/001-llmxive-mipu-gap-bounds/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-mipu-gap-bounds/spec.md`

## Summary
We will (1) generate a **CPU‑only, hardware‑grounded dataset** that pairs full‑precision training signals (gradient norm, local curvature) with KL‑divergence measured by a **CPU‑based quantized inference engine** (INT4, INT8, and optional FP8); (2) train a **lightweight Kernel Ridge Regression** model to predict the hardware‑measured policy gap using only those training‑side features; and (3) **verify** that the predictor respects the theoretical bound (|pred − actual| < 0.1) across the three quantization levels and that a proxy MIPU loop does not degrade downstream performance.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers`, `datasets`, `llama-cpp-python`, `onnxruntime`, `scikit-learn`, `numpy`, `pandas`, `pytest`, `jsonschema`  
- **Storage**: Local filesystem under `data/` (raw, processed, metrics)  
- **Testing**: `pytest -m contract` validates all YAML contracts  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (2 vCPU, ≈7 GB RAM). **CPU‑first** – all steps run on the CPU; no GPU off‑load is permitted for the KL‑divergence computation (Principle VI).  
- **Performance Goals**: End‑to‑end pipeline ≤ 6 h; ≥ 300 samples (to satisfy SC‑005).  
- **Constraints**: Ground‑truth KL must be computed **exclusively** on the CPU quantized engine; the `hardware_source` column is fixed to `"CPU"`; FP8 is generated only if ONNX Runtime supports true float‑8; otherwise the dataset simply omits FP8 rows (no synthetic zero‑KL values).  

## Constitution Check

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Fixed seeds, deterministic llama‑cpp calls, SHA‑256 checksums recorded. |
| II. Verified Accuracy | PASS | All external resources (GSM8K, Llama‑2‑3B‑4bit‑GGUF) are fetched via verified Hugging Face URLs. |
| III. Data Hygiene | PASS | Every file under `data/` is checksummed; transformations write new files; no PII. |
| IV. Single Source of Truth | PASS | All figures/tables trace back to rows in `training_sample.parquet`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/PROJ-997-...yaml`. |
| VI. Hardware‑Grounded Validation | PASS | KL computed from **CPU‑only** `llama-cpp-python` runs; `hardware_source` is always `"CPU"`. |
| VII. Non‑Circular Feature‑Target Independence | PASS | Features extracted from full‑precision model; targets from independent CPU quantized runs. |

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
│   ├── training_sample.schema.yaml
│   ├── gap_prediction_result.schema.yaml
│   ├── metrics.schema.yaml
│   └── predictor.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

### Source Code (single‑project layout)

```
projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/
├── code/
│   ├── __init__.py
│   ├── cli/
│   │   ├── generate_ground_truth.py   # T015 – CPU‑only KL generation
│   │   ├── generate_fp8_ground_truth.py # T017 – optional FP8 (CPU only)
│   │   ├── validate_dataset_stats.py # T016 – dataset sanity check
│   │   └── measure_runtime.py        # T034 – wall‑clock guard
│   ├── data/
│   │   ├── extract_features.py        # T019 – gradient & curvature
│   │   └── preprocess.py              # T023 – split, PCA, VIF
│   ├── models/
│   │   ├── train_predictor.py         # T021 – Kernel Ridge Regression
│   │   └── evaluate_predictor.py      # T022 – correlation, bound check
│   ├── validation/
│   │   └── mipu_benchmark.py          # T027‑T029 + T033
│   └── utils/
│       ├── llama_engine.py            # Wrapper for llama‑cpp‑python (CPU)
│       └── onnx_fp8_engine.py         # Wrapper for ONNX Runtime FP8 (CPU)
├── data/
│   ├── raw/
│   │   ├── gsm8k/                     # downloaded via datasets
│   │   └── llama2-3b-4bit-gguf/       # 4‑bit GGUF checkpoint from HF
│   ├── processed/
│   │   └── training_sample.parquet
│   └── metrics/
│       ├── dataset_stats.json
│       ├── metrics.json
│       ├── benchmark_report.json
│       └── runtime.json
├── tests/
│   └── contract/                     # contract validation tests
├── requirements.txt
└── state/
    └── projects/PROJ-997-...yaml      # artifact hashes, timestamps
```

**Structure Decision**: A single‑project layout keeps data generation, model training, and validation tightly coupled, satisfying Principle IV and simplifying reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **CPU‑only Quantization Wrapper** (T015) | Required by Principle VI; must measure KL on a real CPU engine. | Simulated GPU off‑load would violate hardware‑grounded validation. |
| **Optional FP8 via ONNX (T017)** | FP8 is part of SC‑004; we attempt real FP8 on CPU, but skip gracefully if unsupported. | Dropping FP8 entirely would leave SC‑004 uncovered; fabricating zero‑KL would break construct validity. |
| **Stratified Split & PCA** (T023) | Guarantees representation of all quantization levels and mitigates collinearity (VIF ≤ 10). | Random split could omit a level, breaking SC‑004. |
| **Bonferroni Correction** (SC‑003) | Multiple comparisons (3 quantization levels + t‑test) demand family‑wise error control. | Uncorrected p‑values would inflate Type I error. |
| **Runtime Guard** (T034) | Enforces SC‑005 (≤ 6 h) by measuring wall‑clock time and aborting if exceeded. | No explicit runtime check would leave feasibility unverified. |
| **Sensitivity Sweep over ε** (bound) | Demonstrates that the 0.1 tolerance is not arbitrary; we report stability for ε ∈ {0.05, 0.1, 0.15}. | Fixed ε without analysis would be arbitrary. |
| **Power‑analysis Report** (T033) | Shows ≥ 80 % power for a paired t‑test with ≥ 100 prompts after Bonferroni correction. | Using only 10 prompts would be severely under‑powered. |
| **Hardware Consistency** (T015 amendment) | Guarantees all KL measurements are performed on the CPU, eliminating device‑induced confounds. | Allowing mixed CPU/GPU would violate Principle VI. |

## Task List (ordered for deterministic execution)

| ID | Description | FRs addressed | SCs addressed | Notes |
|----|-------------|---------------|---------------|-------|
| **T015** | `code/cli/generate_ground_truth.py` – For each GSM8K prompt: (a) extract gradient norm & curvature using the **full‑precision FP16 Llama‑2‑3B‑4bit‑GGUF** model, (b) run full‑precision inference (FP16) on CPU, (c) run quantized inference with **INT4** and **INT8** via `llama_engine.py` (CPU only), (d) compute KL divergence for each level, (e) write rows to `training_sample.parquet`. If CPU OOM occurs, the script **fails** with a clear error message; the user must reduce sample size or switch to a smaller model. | FR‑001, FR‑002, FR‑003 | SC‑001 (non‑zero KL proportion) | `hardware_source` is always `"CPU"`. |
| **T017** | `code/cli/generate_fp8_ground_truth.py` – Attempts FP8 inference using `onnx_fp8_engine.py` (CPU only). If ONNX Runtime supports float‑8, KL divergence is computed and rows with `quantization_level="FP8"` are added; otherwise the script logs a warning and **does not create FP8 rows**. | FR‑001, FR‑002, FR‑003 | SC‑001 | No synthetic zero‑KL values are introduced. |
| **T016** | `code/cli/validate_dataset_stats.py` – Computes descriptive statistics and verifies that **≥ 5 %** of KL values are non‑zero for each *present* quantization level (INT4, INT8, FP8 if present). Writes `data/metrics/dataset_stats.json`. | FR‑001, FR‑004 (dataset suitability) | SC‑001 | Fails the pipeline if the condition is not met. |
| **T019** | `code/data/extract_features.py` – Loads the **full‑precision FP16 Llama‑2‑3B‑4bit‑GGUF** model, performs a single forward‑backward pass per prompt, records L2 gradient norm and a diagonal‑Hessian trace approximation. Stores intermediate CSV (`features_raw.csv`) for reproducibility. | FR‑001 | – | Deterministic via fixed seeds. |
| **T021** | `code/models/train_predictor.py` – Stratified train/validation split (by quantization level and prompt‑length bin), PCA (≥ 99 % variance retained), VIF diagnostic (require VIF ≤ 10). Trains a **Kernel Ridge Regression** model on all available levels (INT4, INT8, optional FP8). Saves `gap_predictor.pkl`. | FR‑004, FR‑005 | SC‑001, SC‑004 | Hyper‑parameter grid limited to 5 combos to stay within compute budget. |
| **T022** | `code/models/evaluate_predictor.py` – Predicts KL on the held‑out set, computes Pearson r, MAE, and the bound check `|pred‑actual| < ε` for ε ∈ {0.05, 0.1, 0.15}. Writes per‑sample predictions (`gap_predictions.parquet`) and a summary `metrics.json` (conforms to `metrics.schema.yaml`). | FR‑005, FR‑007 | SC‑001, SC‑004, SC‑005 | |
| **T023** | `code/data/preprocess.py` – Implements the stratified split, PCA, and VIF diagnostics referenced by T021. Writes split indices (`train_idx.npy`, `val_idx.npy`). | FR‑004 | SC‑001 | |
| **T027** | `code/validation/mipu_benchmark.py` – Runs a small RL arithmetic task with **≥ 100** prompts twice: (a) **proxy** loop (predictor decides whether to accept a policy) and (b) **baseline** loop (full CPU‑sync quantized inference). Records final reasoning scores and per‑step latency. | FR‑006, FR‑007 | SC‑002, SC‑003 | |
| **T028** | Same script – Performs a **paired t‑test** on the two score vectors; applies **Bonferroni correction** for the three quantization‑level comparisons. If Shapiro‑Wilk rejects normality, also runs a **permutation test** (10 000 permutations) and reports both p‑values. | FR‑006 | SC‑003 | |
| **T029** | Same script – Computes average latency for proxy vs. baseline, calculates reduction percentage, stores in `metrics.json`. | SC‑002 | – | |
| **T033** | Extension of `mipu_benchmark.py` – Adds a **power‑analysis report** confirming that 100 prompts give ≥ 80 % power to detect a medium effect (Cohen’s d ≈ 0.5) after Bonferroni correction. The report is appended to `metrics.json`. | FR‑006, SC‑003 | – | Ensures statistical adequacy. |
| **T034** | `code/cli/measure_runtime.py` – Wraps the entire pipeline, records total wall‑clock time, aborts if > 6 h, writes `runtime.json`. | SC‑005 | – | |
| **T030** | (Removed) – Contract validation tests remain but are not a separate task. |
| **T031** | (Removed) – Documentation updates are covered in the plan itself. |
| **T032** | (Removed) – Quickstart/research generation are manual artifacts, not tasks. |

All tasks respect the ordering **download → feature extraction → ground‑truth generation → validation → model training → evaluation → benchmark → reporting**.

---
