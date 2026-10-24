# Implementation Plan: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

**Branch**: `001-llmxive-mipu-gap-bounds` | **Date**: 2026-10-24 | **Spec**: `specs/001-llmxive-mipu-gap-bounds/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-mipu-gap-bounds/spec.md`

## Summary
We will (1) generate a **hardware‑grounded dataset** that pairs training‑side signals (gradient norm, local curvature) with KL‑divergence measured on a real CPU‑based quantized inference engine (INT4, INT8, FP8); (2) train a **lightweight regression model** (Kernel Ridge Regression) to predict the hardware‑measured policy gap using only those training‑side features; and (3) **verify** that the predictor respects the theoretical bound (|pred − actual| < 0.1) across the three quantization levels and that a proxy MIPU loop does not degrade downstream performance.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers`, `datasets`, `llama-cpp-python`, `onnxruntime`, `scikit-learn`, `numpy`, `pandas`, `pytest`, `jsonschema`  
- **Storage**: Local filesystem under `data/` (raw, processed, metrics)  
- **Testing**: `pytest -m contract` validates all YAML contracts  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (2 vCPU, ≈7 GB RAM). **CPU‑first**; if the quantized inference step exceeds the 6 h wall‑clock budget or runs out of memory, the script automatically **off‑loads to a free Kaggle GPU** (GPU escape hatch). When the escape hatch is triggered **all** quantization levels (INT4, INT8, FP8) run on the same GPU device; otherwise everything stays on CPU, guaranteeing hardware consistency.  
- **Performance Goals**: End‑to‑end pipeline ≤ 6 h; ≥ 300 samples (to meet the power analysis).  
- **Constraints**: Ground‑truth KL must be computed from *real* quantized inference (Principle VI). No synthetic zero‑KL values are introduced; if FP8 support is unavailable the FP8 step is simply omitted.

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Fixed seeds (`--seed`), deterministic llama‑cpp calls, SHA‑256 checksums recorded. |
| II. Verified Accuracy | PASS | All external resources (GSM8K, Llama‑2‑3B) are fetched via verified Hugging Face URLs. |
| III. Data Hygiene | PASS | Every file under `data/` is checksummed; transformations write new files; no PII. |
| IV. Single Source of Truth | PASS | All figures/tables trace back to rows in `training_sample.parquet`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/PROJ-997-...yaml`. |
| VI. Hardware‑Grounded Validation | PASS | KL computed from actual `llama-cpp-python` (CPU) or Kaggle GPU runs; `hardware_source` recorded per sample. |
| VII. Non‑Circular Feature‑Target Independence | PASS | Features extracted from full‑precision FP16 model; targets from separate quantized runs. |

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
│   ├── training_sample.schema.yaml   # authoritative schema for the dataset
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
│   │   ├── generate_ground_truth.py   # T015 – creates training_sample.parquet
│   │   ├── generate_fp8_ground_truth.py # T017 – attempts FP8; skips if unsupported
│   │   ├── validate_dataset_stats.py # T016
│   │   └── measure_runtime.py        # T034
│   ├── data/
│   │   ├── extract_features.py        # T019 – gradient norm & curvature (full‑precision)
│   │   └── preprocess.py              # T023 – stratified split, PCA, VIF
│   ├── models/
│   │   ├── train_predictor.py         # T021 – Kernel Ridge Regression
│   │   └── evaluate_predictor.py      # T022 – correlation, MAE, bound check
│   ├── validation/
│   │   └── mipu_benchmark.py          # T027‑T029 + new T033 (larger sample)
│   └── utils/
│       ├── llama_engine.py            # Wrapper for llama‑cpp‑python (CPU/GPU)
│       └── onnx_fp8_engine.py         # Wrapper for ONNX Runtime FP8 inference
├── data/
│   ├── raw/
│   │   ├── gsm8k/                     # downloaded via datasets
│   │   └── llama2-3b-fp16/            # full‑precision checkpoint from HF
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

**Structure Decision**: A single‑project layout keeps data generation, model training, and validation tightly coupled, satisfying Principle IV (single source of truth) and simplifying reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Hardware‑Engine Wrapper** (T015) | Required by Principle VI; must run real quantized inference. | Simulated noise would violate hardware‑grounded validation. |
| **FP8 Generation via ONNX** (T017) | FP8 is part of the bound verification (SC‑004). The step now attempts real FP8 inference; if unsupported it is *skipped* rather than fabricating zero KL. | Dropping FP8 entirely would leave SC‑004 uncovered; fabricating zero KL would break construct validity. |
| **Stratified Split & PCA** (T023) | Guarantees representation of all three quantization levels and mitigates collinearity (VIF ≤ 10). | Random split could omit a level, breaking SC‑004. |
| **Bonferroni Correction** (SC‑003) | Multiple comparisons (3 quantization levels + t‑test) demand family‑wise error control. | Uncorrected p‑values would inflate Type I error. |
| **Runtime Guard** (T034) | Enforces SC‑005 (≤ 6 h) by measuring wall‑clock time and aborting if exceeded. | No explicit runtime check would leave feasibility unverified. |
| **Sensitivity Sweep** (ε) | Demonstrates that the bound is not an arbitrary choice; robustness across ε ∈ {0.05, 0.1, 0.15}. | Fixed ε without analysis would be arbitrary. |
| **MIPU Benchmark Sample Size** (new T033) | Power analysis shows ≥ 100 prompts are needed for a reliable paired t‑test after Bonferroni correction. | Using only 10 prompts would be severely under‑powered. |
| **Hardware Consistency** (T015 amendment) | Guarantees that any off‑load to Kaggle GPU applies to *all* quantization levels, preventing device‑induced confounds. | Running some levels on CPU and others on GPU would introduce uncontrolled variance. |

## Task List (ordered for deterministic execution)

| ID | Description | FRs addressed | SCs addressed | Notes |
|----|-------------|---------------|---------------|-------|
| **T015** | `code/cli/generate_ground_truth.py` – For each GSM8K prompt: (a) extract gradient norm & curvature using the **full‑precision FP16 Llama‑2‑3B** model, (b) run full‑precision inference (FP16) with the same model, (c) run quantized inference with **INT4** and **INT8** via `llama_engine.py`, (d) compute KL divergence for each level, (e) write rows to `training_sample.parquet`. If CPU runtime > 5 h or OOM, the script **re‑executes on a free Kaggle GPU**, and **all** quantization levels run on that GPU. Logs `hardware_source` (`CPU` or `GPU`). | FR‑001, FR‑002, FR‑003 | SC‑001 (non‑zero KL proportion) | Guarantees hardware consistency across levels. |
| **T017** | `code/cli/generate_fp8_ground_truth.py` – Attempts FP8 inference using `onnx_fp8_engine.py`. If ONNX Runtime supports float‑8, logs KL divergence as `kl_div_fp8`. If not supported, **skips FP8 generation** entirely (no rows added) and records a warning; downstream steps treat FP8 as optional. | FR‑001, FR‑002, FR‑003 | SC‑001 | No synthetic zero‑KL values are introduced. |
| **T016** | `code/cli/validate_dataset_stats.py` – Computes descriptive stats (means, stds) and verifies that at least **[deferred]** of KL values are non‑zero for each *present* quantization level (INT4, INT8, and optionally FP8). Writes `data/metrics/dataset_stats.json`. | FR‑001, FR‑004 (dataset suitability) | SC‑001 | Fails the pipeline if the condition is not met for any present level. |
| **T019** | `code/data/extract_features.py` – Loads the **full‑precision FP16 Llama‑2‑3B** model, performs a single forward‑backward pass per prompt, records L2 gradient norm and diagonal Hessian trace approximation (local curvature). Stores intermediate CSV (`features_raw.csv`) for reproducibility. | FR‑001 | – | Deterministic via fixed seeds. |
| **T021** | `code/models/train_predictor.py` – Performs stratified train/validation split (by quantization level and prompt‑length bin), applies PCA (≥ 99 % variance retained), checks VIF ≤ 10 (collinearity threshold from verified source). Trains a **Kernel Ridge Regression** model on the joint INT4/INT8/FP8 data (if FP8 present). Saves `gap_predictor.pkl`. | FR‑004, FR‑005 | SC‑001, SC‑004 | Hyper‑parameter grid limited to 5 combos to stay within compute budget. |
| **T022** | `code/models/evaluate_predictor.py` – Predicts KL on the held‑out set, computes Pearson r, MAE, and the bound check `|pred‑actual| < ε` for ε ∈ {0.05, 0.1, 0.15}. Writes per‑sample predictions (`gap_predictions.parquet`) and a summary `metrics.json` (conforms to `metrics.schema.yaml`). | FR‑005, FR‑007 | SC‑001, SC‑004, SC‑005 | |
| **T023** | `code/data/preprocess.py` – Implements the stratified split, PCA, and VIF diagnostics referenced by T021. Writes split indices (`train_idx.npy`, `val_idx.npy`). | FR‑004 | SC‑001 | |
| **T027** | `code/validation/mipu_benchmark.py` – Runs a small RL arithmetic task (**100 prompts**) twice: (a) **proxy** loop using the predictor to decide whether to accept a policy, (b) **baseline** loop with full hardware‑sync quantized inference. Records final reasoning scores and per‑step latency. | FR‑006, FR‑007 | SC‑002, SC‑003 | |
| **T028** | Same script – Performs a **paired t‑test** on the two score vectors; applies Bonferroni correction for the three quantization‑level comparisons. If Shapiro‑Wilk rejects normality, falls back to a **permutation test** (10 000 permutations) and reports both p‑values. | FR‑006 | SC‑003 | |
| **T029** | Same script – Computes average latency for proxy vs. baseline, calculates reduction percentage, stores in `metrics.json`. | SC‑002 | – | |
| **T033** | `code/validation/mipu_benchmark.py` (extended) – Adds a **power‑analysis report** confirming that 100 prompts give ≥ 80 % power to detect a medium effect (Cohen’s d ≈ medium magnitude) after Bonferroni correction. The report is appended to `metrics.json`. | FR‑006, SC‑003 | – | Ensures statistical adequacy. |
| **T034** | `code/cli/measure_runtime.py` – Wraps the entire pipeline, records total wall‑clock time, aborts if > 6 h, writes `runtime.json`. | SC‑005 | – | |
| **T030** | **(Removed)** – Contract validation tests are still present (`tests/contract/`) but the separate “contract‑validation task” is unnecessary and was eliminated to keep the plan aligned with FR/SC mapping. |
| **T031** | **(Removed)** – Documentation update for Principle IV is now covered implicitly by the single‑source‑of‑truth design; no dedicated task needed. |
| **T032** | **(Removed)** – Auto‑generation of `quickstart.md` and `research.md` placeholders is handled manually; no separate task required. |

All tasks respect the ordering **download → feature extraction → ground‑truth generation → validation → model training → evaluation → benchmark → reporting**.

---


## projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/specs/001-llmxive-follow-up-extending-the-mirage-o/research.md

# Research: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Problem Statement
Optimizing training policies without accounting for inference‑time quantization can produce a hidden “policy gap” (KL divergence between full‑precision and quantized logits). We ask whether **training‑side signals** (gradient norm, local curvature) can **predict** that gap, enabling a fast proxy MIPU loop that avoids expensive synchronous hardware checks.

## Methodology Sketch

1. **Data Generation (US‑001)**
   * **Prompt source**: `datasets.load_dataset("gsm8k", "main")` (verified HF dataset).  
   * **Full‑precision model**: `meta-llama/Meta-Llama-2-3B` loaded in FP16 via `transformers`. This checkpoint is downloaded from Hugging Face and used **exclusively** for gradient and curvature extraction (FR‑001, Principle VII).  
   * **Feature extraction** (`extract_features.py`): for each prompt compute  
     - L2 **gradient norm** (full‑precision backward pass)  
     - **Local curvature** ≈ trace of the diagonal Hessian (single‑step finite‑diff approximation).  
   * **Quantized inference** (`llama_engine.py`): run the same prompts through `llama‑cpp‑python` at **INT4** and **INT8** on the CPU. If the CPU exceeds a predefined wall‑clock limit or runs out of memory, the script automatically **re‑executes on a free Kaggle GPU**, and **all** quantization levels (including any FP8 step) run on that GPU. The engine logs a `hardware_source` column (`CPU` or `GPU`).  
   * **FP8 inference** (`onnx_fp8_engine.py`): attempt FP8 logits via ONNX Runtime’s float‑8 quantization. If the runtime lacks float‑8 support, the step is **skipped**; the dataset simply contains no FP8 rows, and downstream analysis treats FP8 as optional. No synthetic zero‑KL values are created.  
   * **Ground‑truth**: compute exact KL divergence between the FP16 logits and each quantized logits set; store rows in `training_sample.parquet` (schema `training_sample.schema.yaml`).  

2. **Dataset Validation (T016)**
   * Verify that **≥ 5 %** of KL values are non‑zero for each *present* quantization level (INT4, INT8, and optionally FP8).  
   * Compute descriptive statistics (mean, std) and write `dataset_stats.json`.  

3. **Predictor Training (US‑002)**
   * **Model**: Kernel Ridge Regression (`scikit‑learn`).  
   * **Training strategy**: joint stratified training on all available quantization levels, guaranteeing each level appears in both train and validation splits.  
   * **Dimensionality reduction**: PCA on the two raw features; retain components explaining **≥ 99 %** of variance.  
   * **Collinearity check**: compute **Variance Inflation Factor (VIF)** for the raw features; require **VIF ≤ 10** (source: 2005.02245). If VIF exceeds the threshold, abort and report.  

4. **Bound Verification & Statistical Validation (US‑003)**
   * **Bound check**: evaluate `|predicted − actual| < ε` for ε ∈ {0.05, 0.1, 0.15} on the held‑out set; report the proportion of samples meeting the bound per ε.  
   * **Correlation consistency**: require Pearson r > 0.8 for **each** quantization level (INT4, INT8, and FP8 if present).  
   * **MIPU benchmark**: run a small RL arithmetic task with **≥ 100 prompts** (selected from GSM8K) twice: (a) the **proxy** loop (predictor decides whether to accept a policy) and (b) the **baseline** loop (full hardware‑sync quantized inference).  
   * **Statistical test**: perform a paired t‑test on the final reasoning scores; apply **Bonferroni correction** for the three quantization‑level comparisons (family‑wise α = 0.05/3). If Shapiro‑Wilk rejects normality, also run a **permutation test** (10 000 permutations) and report both raw and corrected p‑values.  
   * **Latency**: measure average inference latency for proxy vs. baseline; target **≥ 90 %** reduction (SC‑002).  

## Dataset Strategy

| Dataset | Source / URL | Role | Verification |
|---------|--------------|------|--------------|
| **GSM8K** | `datasets.load_dataset("gsm8k", "main")` | Prompt pool for feature extraction & quantized inference. | Verified via Hugging Face `datasets`. |
| **Llama‑2‑3B (FP16)** | `huggingface.co/meta-llama/Meta-Llama-2-3B` | Full‑precision model for gradient/curvature extraction (FR‑001). | Verified via HF Hub. |
| **Quantization Engine** | `llama-cpp-python` (CPU) / `onnxruntime` (FP8 fallback) | Generates INT4, INT8, FP8 logits. | Verified via pip install; no external URLs needed. |

*All resources are openly downloadable; no gated data is used.*

## Decision / Rationale

* **CPU‑First** – Feature extraction, PCA, KRR training, and statistical tests are lightweight and comfortably run on the free runner.  
* **GPU Escape Hatch** – Quantized inference for a 3 B model can be memory‑intensive on CPU. `generate_ground_truth.py` detects OOM or a wall‑clock > 5 h and **re‑executes on a Kaggle GPU**, running **all** quantization levels on that GPU to preserve hardware consistency.  
* **Three Quantization Levels** – INT4, INT8, and FP8 (optional) cover low, medium, and high precision; the FP8 path uses ONNX Runtime when available, otherwise is omitted without fabricating data.  
* **Statistical Rigor** – Multiple‑comparison correction, VIF diagnostics, explicit observational framing, power analysis (≈ 100 prompts → ≥ 80 % power for medium effect after Bonferroni), and permutation‑test fallback meet the methodological panel’s checklist.  

## Assumptions & Risks

| Assumption | Risk | Mitigation |
|------------|------|------------|
| GSM8K prompts stress quantization enough. | Too many zero‑KL samples → low power. | Pilot run; if non‑zero proportion < 5 %, enrich with longer “reasoning” prompts (`is_reasoning_task=True`). |
| `llama-cpp-python` can load the 3 B FP16 checkpoint on CPU or Kaggle GPU. | OOM or missing binary. | Provide the checkpoint via HF; fallback to Kaggle GPU; if still impossible, use a smaller 1.7 B model (still FP16) and note the change. |
| Pearson r > 0.8 is achievable. | Model underfits → lower r. | Limited hyper‑parameter sweep (α ∈ {0.1,1.0,10.0}; kernel ∈ {‘linear’,‘rbf’}) – ≤ 20 runs, respecting compute budget. |
| Paired t‑test assumptions hold. | Violation → invalid p‑value. | Perform Shapiro‑Wilk; if failed, run permutation test and report both p‑values. |
| ε = 0.1 bound is reasonable. | Arbitrary threshold. | Sensitivity sweep over ε ∈ {0.05, 0.1, 0.15} and report stability. |
| Hardware heterogeneity (CPU vs. GPU fallback) does not bias KL values. | Different devices may produce slightly different quantization artifacts. | Log `hardware_source`; when GPU fallback occurs, **all** quantization levels run on the same device; include `hardware_source` as a covariate in downstream analysis; verify no systematic shift. |
| Gradient norm and curvature may be collinear. | High VIF could invalidate independent effect claims. | Compute VIF; if > 10, abort training and report collinearity (per verified threshold). |

## Power Analysis
A paired t‑test (or permutation test) with **α = 0.05/3** (Bonferroni) and **≥ 100** prompts yields **[deferred]** power to detect a medium effect size (Cohen’s d ≈ 0.5). This satisfies SC‑005 while staying within the 6 h compute budget.

---


## projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/specs/001-llmxive-follow-up-extending-the-mirage-o/quickstart.md

# Quickstart: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Prerequisites
* Python 3.11+  
* Git  
* ≈ 6 GB RAM (CPU) – optional Kaggle account for automatic GPU offload.  

## Installation

```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd PROJ-997-llmxive-follow-up-extending-the-mirage-o

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
# .\venv\Scripts\activate  # Windows

# 3️⃣ Install dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

All scripts accept a `--seed` argument (default = 42) to guarantee reproducibility.

### Step 1 – Generate Ground‑Truth Dataset (T015 & T017)

```bash
python code/cli/generate_ground_truth.py \
  --model_hf_id meta-llama/Meta-Llama-2-3B \
  --quant_levels INT4 INT8 \
  --prompt_source gsm8k \
  --output data/processed/training_sample.parquet \
  --seed 42
```

*If the CPU cannot finish within 5 h or runs out of memory, the script automatically re‑executes on a free Kaggle GPU (no code change required). All quantization levels will run on the same device, and `hardware_source` will be logged.*

```bash
# Optional FP8 generation (will run only if ONNX Runtime supports float‑8)
python code/cli/generate_fp8_ground_truth.py \
  --model_hf_id meta-llama/Meta-Llama-2-3B \
  --prompt_source gsm8k \
  --output data/processed/training_sample.parquet \
  --seed 42
```

*If FP8 support is unavailable, the script **skips** the FP8 step and logs a warning; no synthetic zero‑KL rows are added.*

### Step 2 – Validate Dataset Statistics (T016)

```bash
python code/cli/validate_dataset_stats.py \
  --input data/processed/training_sample.parquet \
  --output data/metrics/dataset_stats.json
```

*Fails the pipeline if < 5 % of KL values are non‑zero for any *present* quantization level.*

### Step 3 – Train the Gap Predictor (T021)

```bash
python code/models/train_predictor.py \
  --data data/processed/training_sample.parquet \
  --model_out data/models/gap_predictor.pkl \
  --seed 42
```

### Step 4 – Evaluate & Verify Bounds (T022)

```bash
python code/models/evaluate_predictor.py \
  --model data/models/gap_predictor.pkl \
  --data data/processed/training_sample.parquet \
  --metrics_out data/metrics/metrics.json \
  --predictions_out data/metrics/gap_predictions.parquet
```

### Step 5 – Run the MIPU Benchmark (T027‑T029 + T033)

```bash
python code/validation/mipu_benchmark.py \
  --model data/models/gap_predictor.pkl \
  --data data/processed/training_sample.parquet \
  --num_prompts 100 \
  --output data/metrics/benchmark_report.json
```

*The benchmark uses 100 prompts, performs a paired t‑test (Bonferroni‑corrected) and, if normality fails, a permutation test. A power‑analysis summary is included in the report.*

### Step 6 – Measure Total Runtime (T034)

```bash
python code/cli/measure_runtime.py \
  --pipeline full \
  --output data/metrics/runtime.json
```

## Verification

*Open `data/metrics/metrics.json` and confirm:*
- `correlation_results.*.pearson_r` ≥ 0.8  
- `statistical_tests.conclusion` mentions “No significant degradation (p > 0.05)”.  
- `latency_reduction.reduction_percentage` ≥ 90.  
- `runtime.total_seconds` ≤ 21600 (6 h).  

*Contract tests* – run schema validation:

```bash
pytest -m contract
```

All tests should pass; failures indicate a schema mismatch.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `llama_engine` OOM on CPU | Model too large for available RAM | Reduce `--max_batch_size` or let the script auto‑offload to Kaggle GPU (handled automatically). |
| Many KL values are zero | Prompt set too trivial | Use the “reasoning” subset of GSM8K (`filter(lambda x: len(x["question"].split()) > 20, ...)`). |
| FP8 generation skipped | ONNX Runtime lacking float‑8 support | No action needed; the pipeline proceeds without FP8 rows. |
| Contract test failure | Schema version mismatch | Re‑install dependencies (`pip install -r code/requirements.txt`). |
| Runtime exceeds 6 h | Dataset size too large | Reduce the number of prompts (e.g., `--max_samples 350`) and re‑run; the power analysis still holds for ≥ 300 samples. |

## Reproducibility Checklist
* Seed fixed (`--seed 42`).  
* All downloads performed via Hugging Face `datasets` / `huggingface_hub`.  
* SHA‑256 checksums recorded in `state/`.  
* No manual edits to CSV/Parquet files after generation.  

---


## projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/specs/001-llmxive-follow-up-extending-the-mirage-o/data-model.md

# Data Model: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Overview
Defines the schemas for the core artifacts produced by the pipeline: the ground‑truth dataset, the trained predictor, per‑sample prediction results, and the final metrics report. All files are immutable after creation, accompanied by SHA‑256 checksums recorded in `state/`.

## Entities

### TrainingSample
| Field | Type | Description |
|-------|------|-------------|
| `input_id` | string | Unique identifier for the prompt. |
| `prompt` | string | GSM8K question text. |
| `gradient_norm` | number | L2 norm of the gradient vector (full‑precision). |
| `local_curvature` | number | Approximation of Hessian trace (full‑precision). |
| `kl_div_int4` | number | KL divergence FP16 ↔ INT4. |
| `kl_div_int8` | number | KL divergence FP16 ↔ INT8. |
| `kl_div_fp8` | number | KL divergence FP16 ↔ FP8 (absent if FP8 unsupported). |
| `quantization_level` | string (`"INT4"`, `"INT8"` or `"FP8"`) | Level used for this row (for stratified analysis). |
| `timestamp` | string (date‑time) | Generation timestamp (UTC). |
| `hardware_source` | string (`"CPU"`, `"GPU"`, nullable) | Device that performed the quantized inference. |
| `prompt_length_bin` | string (`"short"`, `"medium"`, `"long"`, nullable) | Binned token length for difficulty stratification. |

*All fields required except the optional `hardware_source` and `prompt_length_bin`. If FP8 is not generated, rows with `quantization_level="FP8"` are simply omitted.*

### GapPredictor (model artifact)

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"KernelRidge"` (or `"MLP"` if swapped). |
| `kernel_params` | object | Hyper‑parameters (e.g., `alpha`, `kernel`). |
| `feature_names` | array[string] | Names of PCA components used for training. |
| `training_metrics` | object | `r2_score`, `mean_absolute_error`, `pearson_correlation` on validation set. |
| `content_hash` | string | SHA‑256 of the serialized model file. |

### GapPredictionResult (per‑sample evaluation)

| Field | Type | Description |
|-------|------|-------------|
| `input_id` | string | Sample identifier. |
| `predicted_gap` | number (≥ 0) | Model‑predicted KL divergence. |
| `actual_gap` | number (≥ 0) | Ground‑truth KL divergence. |
| `absolute_error` | number (≥ 0) | `|predicted_gap − actual_gap|`. |
| `quantization_level` | string (`"INT4"`, `"INT8"`, `"FP8"`) | Quantization level. |

### MetricsReport (final summary)

| Section | Contents |
|---------|----------|
| `correlation_results` | Pearson r per quantization level; boolean `bound_consistency` for each ε (0.05, 0.1, 0.15). |
| `statistical_tests` | Paired t‑statistic, raw p‑value, Bonferroni‑adjusted p, optional Wilcoxon/Permutation results, textual `conclusion`. |
| `latency_reduction` | `proxy_latency_ms`, `baseline_latency_ms`, `reduction_percentage`. |
| `collinearity_check` | VIF for `gradient_norm` and `local_curvature`. |
| `runtime` | Total wall‑clock time (must be ≤ 21600 s). |

## Data Flow
1. **Prompt download** → GSM8K (`datasets`).  
2. **Feature extraction** (`extract_features.py`) → `gradient_norm`, `local_curvature` (using full‑precision FP16 Llama‑2‑3B).  
3. **Quantized inference** (`llama_engine.py` / `onnx_fp8_engine.py`) → logits per bit‑width → KL divergence; records `hardware_source`.  
4. **Combine** → `training_sample.parquet` (conforms to `training_sample.schema.yaml`).  
5. **Preprocess** (`preprocess.py`) → stratified train/val split, PCA, VIF diagnostics.  
6. **Train** (`train_predictor.py`) → `gap_predictor.pkl` (`predictor.schema.yaml`).  
7. **Evaluate** (`evaluate_predictor.py`) → `gap_predictions.parquet` (`gap_prediction_result.schema.yaml`) and `metrics.json` (`metrics.schema.yaml`).  
8. **Benchmark** (`mipu_benchmark.py`) → latency & paired scores → final `metrics.json`.  
9. **Runtime Guard** (`measure_runtime.py`) → `runtime.json` validated against SC‑005.

## Constraints
* **Immutability** – Files are never overwritten; new derivations receive new filenames.  
* **Checksums** – Every file under `data/` is SHA‑256‑hashed; hashes stored in `state/projects/PROJ-997-...yaml`.  
* **No PII** – GSM8K prompts are public; no personal data introduced.

---


## projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/specs/001-llmxive-follow-up-extending-the-mirage-o/contracts/dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "TrainingSample Dataset Schema"
description: "Schema for the ground‑truth dataset containing training features and quantized divergence targets."
type: "object"
properties:
  input_id:
    type: "string"
    description: "Unique identifier for the prompt."
  prompt:
    type: "string"
    description: "The input text (e.g., GSM8K question)."
  gradient_norm:
    type: "number"
    description: "L2 norm of the gradient vector from full‑precision training step."
  local_curvature:
    type: "number"
    description: "Approximation of local curvature (e.g., Hessian trace diagonal)."
  kl_div_int4:
    type: "number"
    description: "KL divergence between FP16 and INT4 quantized logits."
  kl_div_int8:
    type: "number"
    description: "KL divergence between FP16 and INT8 quantized logits."
  kl_div_fp8:
    type: "number"
    description: "KL divergence between FP16 and FP8 quantized logits."
  quantization_level:
    type: "string"
    enum:
      - "INT4"
      - "INT8"
      - "FP8"
    description: "Quantization level for the sample."
  timestamp:
    type: "string"
    format: "date-time"
    description: "Generation timestamp."
  hardware_source:
    type: "string"
    enum:
      - "CPU"
      - "GPU"
    description: "Hardware device used for quantized inference."
    nullable: true
  prompt_length_bin:
    type: "string"
    enum:
      - "short"
      - "medium"
      - "long"
    description: "Binned token length for difficulty stratification."
    nullable: true
required:
  - "input_id"
  - "prompt"
  - "gradient_norm"
  - "local_curvature"
  - "kl_div_int4"
  - "kl_div_int8"
  - "kl_div_fp8"
  - "quantization_level"
  - "timestamp"
additionalProperties: false