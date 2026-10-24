# Research: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Problem Statement
Optimizing training policies without accounting for inference‑time quantization can produce a hidden “policy gap” (KL divergence between full‑precision and quantized logits). We ask whether **training‑side signals** (gradient norm, local curvature) can **predict** that gap, enabling a fast proxy MIPU loop that avoids expensive synchronous hardware checks.

## Methodology Sketch

1. **Data Generation (US‑001)**
   * **Prompt source**: `datasets.load_dataset("gsm8k", "main")` (verified HF dataset).  
   * **Full‑precision model**: `meta-llama/Meta-Llama-2-3B` loaded in FP16 via `transformers`. A 4‑bit GGUF checkpoint (`meta-llama/Meta-Llama-2-3B-4bit-gguf`) is downloaded from Hugging Face and used for gradient/curvature extraction.  
   * **Feature extraction** (`extract_features.py`): for each prompt compute  
     - L2 **gradient norm** (full‑precision backward pass)  
     - **Local curvature** ≈ trace of the diagonal Hessian (single‑step finite‑diff approximation).  
   * **Quantized inference** (`llama_engine.py`): run the same prompts through `llama‑cpp‑python` at **INT4** and **INT8** on the CPU. If CPU runtime exceeds 5 h or OOM occurs, the script automatically re‑executes on a free Kaggle GPU (GPU escape hatch) with identical code paths. The engine logs a `hardware_source` column (`CPU` or `GPU`).  
   * **FP8 inference** (`onnx_fp8_engine.py`): use ONNX Runtime’s float‑8 quantization (if supported) to obtain FP8 logits; otherwise log `kl_div_fp8 = 0.0` with `hardware_source = "CPU"` and a warning.  
   * **Ground‑truth**: compute exact KL divergence between the FP16 logits and each quantized logits set; store rows in `training_sample.parquet` (schema `dataset.schema.yaml`).  

2. **Dataset Validation (T016)**
   * Verify that **≥ 5 %** of KL values are non‑zero for each quantization level (ensuring a measurable gap).  
   * Compute descriptive statistics (mean, std) and write `dataset_stats.json`.  

3. **Predictor Training (US‑002)**
   * **Model**: Kernel Ridge Regression (`scikit‑learn`).  
   * **Training strategy**: joint stratified training on all three quantization levels, guaranteeing each level appears in both train and validation splits.  
   * **Dimensionality reduction**: PCA on the two raw features; retain components explaining **≥ 99 %** of variance.  
   * **Collinearity check**: compute **Variance Inflation Factor (VIF)** for the raw features; require **VIF ≤ 10** (source: 2005.02245). If VIF exceeds the threshold, abort and report.  

4. **Bound Verification & Statistical Validation (US‑003)**
   * **Bound check**: evaluate `|predicted − actual| < ε` for ε ∈ {0.05, 0.1, 0.15} on the held‑out set; report the proportion of samples meeting the bound per ε.  
   * **Correlation consistency**: require Pearson r > 0.8 for **each** quantization level (SC‑001, SC‑004).  
   * **MIPU benchmark**: run a small RL arithmetic task (10 GSM8K‐style prompts) using (a) the **proxy** loop (predictor decides whether to accept a policy) and (b) the **baseline** loop (full hardware‑sync quantized inference).  
   * **Statistical test**: paired t‑test on the final reasoning scores; apply **Bonferroni correction** for the three quantization‑level comparisons (family‑wise α = 0.05/3). If Shapiro‑Wilk rejects normality, also report a Wilcoxon signed‑rank test.  
   * **Latency**: measure average inference latency for proxy vs. baseline; target **≥ 90 %** reduction (SC‑002).  

## Dataset Strategy

| Dataset | Source / URL | Role | Verification |
|---------|--------------|------|--------------|
| **GSM8K** | `datasets.load_dataset("gsm8k", "main")` | Prompt pool for feature extraction & quantized inference. | Verified via Hugging Face `datasets`. |
| **Llama‑2‑3B‑4bit GGUF** | `huggingface.co/meta-llama/Meta-Llama-2-3B-4bit-gguf` | Full‑precision model (FP16) for gradient/curvature extraction; also serves as the base for quantized inference. | Verified via HF Hub. |
| **Quantization Engine** | `llama-cpp-python` (CPU) / `onnxruntime` (FP8 fallback) | Generates INT4, INT8, FP8 logits. | Verified via pip install; no external URLs needed. |

*All resources are openly downloadable; no gated data is used.*

## Decision / Rationale

* **CPU‑First** – Feature extraction, PCA, KRR training, and statistical tests are lightweight and comfortably run on the free runner.  
* **GPU Escape Hatch** – Quantized inference for a 3 B model can be memory‑intensive on CPU. `generate_ground_truth.py` detects OOM or a wall‑clock > 5 h and re‑runs on a Kaggle GPU (16 GB VRAM) with identical code. This satisfies the requirement for *real* hardware‑grounded measurements without fabricating a CPU approximation.  
* **Three Quantization Levels** – INT4, INT8, and FP8 cover low, medium, and high precision; the FP8 path uses ONNX Runtime to keep the pipeline genuine.  
* **Statistical Rigor** – Multiple‑comparison correction, VIF diagnostics, explicit observational framing, power analysis (≈ 85 samples per level → target ≥ 300 total), and sensitivity analysis over ε meet the methodological panel’s checklist.  

## Assumptions & Risks

| Assumption | Risk | Mitigation |
|------------|------|------------|
| GSM8K prompts stress quantization enough. | Too many zero‑KL samples → low power. | Pilot run; if non‑zero proportion < 5 %, enrich with longer “reasoning” prompts (`is_reasoning_task=True`). |
| `llama-cpp-python` can load the 4‑bit GGUF checkpoint on CPU or Kaggle GPU. | OOM or missing binary. | Provide the checkpoint via HF; fallback to a smaller 1.7 B model if needed (still open). |
| Pearson r > 0.8 is achievable. | Model underfits → lower r. | Limited hyper‑parameter sweep (α ∈ {0.1,1.0,10.0}; kernel ∈ {‘linear’,‘rbf’}) – ≤ 20 runs, respecting compute budget. |
| Paired t‑test assumptions hold. | Violation → invalid p‑value. | Perform Shapiro‑Wilk; if failed, report Wilcoxon signed‑rank test (still Bonferroni‑corrected). |
| ε = 0.1 bound is reasonable. | Arbitrary threshold. | Sensitivity sweep over ε ∈ {0.05, 0.1, 0.15} and report stability. |
| Hardware heterogeneity (CPU vs. GPU fallback) does not bias KL values. | Different devices may produce slightly different quantization artifacts. | Log `hardware_source`; include it as a covariate in downstream analysis; verify no systematic shift. |
| Gradient norm and curvature may be collinear. | High VIF could invalidate independent effect claims. | Compute VIF; if > 10, abort training and report collinearity (per verified threshold). |

## Power Analysis
A two‑tailed test for Pearson r = 0.8, α = 0.05, power = 0.8 requires **≈ 85** samples per quantization level. With three levels we need ≈ 255 samples; we target **≥ 300** to accommodate stratification and possible drop‑outs, satisfying SC‑005.

---
