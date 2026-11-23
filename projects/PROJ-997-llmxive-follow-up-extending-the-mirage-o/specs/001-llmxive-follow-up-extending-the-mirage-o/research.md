# Research: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Problem Statement
Optimizing training policies without accounting for inference‑time quantization can produce a hidden “policy gap” (KL divergence between full‑precision and quantized logits). We ask whether **training‑side signals** (gradient norm, local curvature) can **predict** that gap, enabling a fast proxy MIPU loop that avoids expensive synchronous CPU‑based hardware checks.

## Methodology Sketch

1. **Data Generation (US‑001)**
   * **Prompt source**: `datasets.load_dataset("gsm8k", "main")` (verified HF dataset).  
   * **Full‑precision model**: `meta-llama/Meta-Llama-2-3B-4bit-gguf` loaded in FP16 via `transformers`. This checkpoint is downloaded from Hugging Face and used **exclusively** for gradient/curvature extraction (FR‑001, Principle VII).  
   * **Feature extraction** (`extract_features.py`): for each prompt compute  
     - L2 **gradient norm** (full‑precision backward pass)  
     - **Local curvature** ≈ trace of the diagonal Hessian (single‑step finite‑diff approximation).  
   * **Quantized inference** (`llama_engine.py`): run the same prompts through `llama‑cpp‑python` at **INT4** and **INT8** **on the CPU**. The engine logs a `hardware_source` column that is always `"CPU"` (Principle VI).  
   * **FP8 inference** (`onnx_fp8_engine.py`): attempt FP8 logits via ONNX Runtime’s true float‑8 quantization (CPU). If the runtime lacks float‑8 support, the script **skips** FP8 generation and logs a warning; no synthetic rows are added.  
   * **Ground‑truth**: compute exact KL divergence between the FP16 logits and each quantized logits set; store rows in `training_sample.parquet` (schema `dataset.schema.yaml`).  

2. **Dataset Validation (T016)**
   * Verify that **≥ 5 %** of KL values are non‑zero for each *present* quantization level (ensuring a measurable gap).  
   * Compute descriptive statistics (mean, std) and write `dataset_stats.json`.  

3. **Predictor Training (US‑002)**
   * **Model**: Kernel Ridge Regression (`scikit‑learn`).  
   * **Training strategy**: joint stratified training on all available quantization levels (INT4, INT8, and FP8 if present), guaranteeing each level appears in both train and validation splits.  
   * **Dimensionality reduction**: PCA on the two raw features; retain components explaining **≥ 99 %** of variance.  
   * **Collinearity check**: compute **Variance Inflation Factor (VIF)** for the raw features; require **VIF ≤ 10** (source: 2005.02245). If VIF exceeds the threshold, abort and report.  

4. **Bound Verification & Statistical Validation (US‑003)**
   * **Bound check**: evaluate `|predicted − actual| < ε` for ε ∈ {0.05, 0.1, 0.15} on the held‑out set; report the proportion of samples meeting the bound per ε.  
   * **Correlation consistency**: require Pearson r > 0.8 for **each** quantization level that is present (INT4, INT8, optional FP8).  
   * **MIPU benchmark**: run a small RL arithmetic task with **≥ 100** GSM8K‑style prompts twice: (a) the **proxy** loop (predictor decides whether to accept a policy) and (b) the **baseline** loop (full CPU‑sync quantized inference).  
   * **Statistical test**: paired t‑test on the final reasoning scores; apply **Bonferroni correction** for the three quantization‑level comparisons (family‑wise α = 0.05/3). If Shapiro‑Wilk rejects normality, also report a **permutation test** (10 000 permutations).  
   * **Latency**: measure average inference latency for proxy vs. baseline; target **≥ 90 %** reduction (SC‑002).  

## Dataset Strategy

| Dataset | Source / URL | Role | Verification |
|---------|--------------|------|--------------|
| **GSM8K** | `datasets.load_dataset("gsm8k", "main")` | Prompt pool for feature extraction & quantized inference. | Verified via Hugging Face `datasets`. |
| **Llama‑2‑3B‑4bit‑GGUF** | `huggingface.co/meta-llama/Meta-Llama-2-3B-4bit-gguf` | Full‑precision model (FP16) for gradient/curvature extraction and as the base for CPU quantization. | Verified via HF Hub. |
| **Quantization Engine** | `llama-cpp-python` (CPU) / `onnxruntime` (CPU FP8 fallback) | Generates INT4, INT8, and optional FP8 logits. | Verified via pip install; no external URLs needed. |

*All resources are openly downloadable; no gated data is used.*

## Decision / Rationale

* **CPU‑Only** – Principle VI mandates that KL divergence be measured on a CPU quantized engine; therefore **no GPU off‑load** is permitted for this step.  
* **Optional FP8** – FP8 is included only if the CPU ONNX Runtime truly supports float‑8; otherwise we simply omit FP8 rows, preserving scientific integrity.  
* **Three Quantization Levels** – INT4, INT8, and (if available) FP8 provide low, medium, and high precision coverage required by SC‑004.  
* **Statistical Rigor** – Multiple‑comparison correction, VIF diagnostics, explicit observational framing, power analysis (≈ 300 samples → ≥ 80 % power), and sensitivity analysis over ε meet the methodological panel’s checklist.  

## Assumptions & Risks

| Assumption | Risk | Mitigation |
|------------|------|------------|
| GSM8K prompts stress quantization enough. | Too many zero‑KL samples → low power. | Pilot run; if non‑zero proportion < 5 %, enrich with longer “reasoning” prompts (`len(question.split()) > 20`). |
| `llama-cpp-python` can load the 4‑bit GGUF checkpoint on the CI CPU. | OOM or missing binary. | If OOM occurs, the pipeline aborts with a clear message; the researcher can reduce `--max_samples` or switch to a smaller 1.7 B model. |
| Pearson r > 0.8 is achievable. | Model underfits → lower r. | Limited hyper‑parameter sweep (α ∈ {0.1,1.0,10.0}; kernel ∈ {‘linear’,‘rbf’}) – ≤ 20 runs, respecting compute budget. |
| Paired t‑test assumptions hold. | Violation → invalid p‑value. | Perform Shapiro‑Wilk; if failed, also report permutation test. |
| ε = 0.1 bound is reasonable. | Arbitrary threshold. | Sensitivity sweep over ε ∈ {0.05, 0.1, 0.15} and report stability. |
| Hardware consistency (CPU only) eliminates device bias. | None – enforced by design. | `hardware_source` is fixed to `"CPU"`; any deviation aborts. |
| Gradient norm and curvature may be collinear. | High VIF could invalidate independent effect claims. | Compute VIF; if > 10, abort training and report collinearity (per verified threshold). |

## Power Analysis
A two‑tailed test for Pearson r = 0.8, α = 0.05 (Bonferroni‑adjusted), power = 0.8 requires **≈ 85** samples per quantization level. With three levels we need ≈ 255 samples; we target **≥ 300** to accommodate stratification and potential drop‑outs, satisfying SC‑005 while staying within the 6 h compute budget.

---
