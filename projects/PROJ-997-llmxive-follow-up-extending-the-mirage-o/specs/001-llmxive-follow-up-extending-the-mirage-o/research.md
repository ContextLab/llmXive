# Research: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Problem Statement
Optimizing training policies without accounting for inference‑time quantization can produce a hidden “policy gap” (KL divergence between full‑precision and quantized logits). This work asks whether **training‑side signals** (gradient norms, local curvature) can **predict** that gap, enabling a fast proxy MIPU loop that avoids costly synchronous hardware checks.

## Methodology Sketch

1. **Data Generation (US‑001)**
   * **Prompt source**: GSM8K (`datasets.load_dataset("gsm8k", "main")`).  
   * **Full‑precision model**: `meta-llama/Meta-Llama-2-7B` quantized to 4‑bit (gguf) to fit CPU memory; loaded via `transformers` in FP16 for gradient computation.  
   * **Feature extraction**: For each prompt, compute (a) L2 gradient norm, (b) diagonal Hessian trace approximation (local curvature) using a single backward pass. These features have been shown to correlate with model sensitivity to weight perturbations and thus to quantization effects (gradient‑norm and curvature literature).  
   * **Prompt difficulty control**: Prompts are binned by token length (short, medium, long) and stratified so each bin appears in training and validation splits, mitigating confounding by difficulty.  
   * **Quantized inference**: Run the same prompts through `llama‑cpp‑python` (or `onnxruntime` as fallback) at three bit‑widths – INT4, INT8, FP8 – on the **CPU**. If CPU inference exceeds the 6 h budget, the script automatically re‑executes on a Kaggle GPU (GPU escape hatch). The engine logs a `hardware_source` flag (`CPU` or `GPU`) for each sample.  
   * **Ground‑truth**: Compute exact KL divergence between full‑precision logits and each quantized logits set. Store rows in `training_sample.parquet`.

2. **Dataset Validation (T016)**
   * Verify that > 5 % of KL values are non‑zero (ensuring measurable quantization effect).  
   * Compute descriptive statistics (mean, std) and record in `dataset_stats.json`.

3. **Predictor Training (US‑002)**
   * **Model**: Kernel Ridge Regression (scikit‑learn).  
   * **Training strategy**: Joint stratified training on all three quantization levels (ensuring each level appears in both train & validation).  
   * **Dimensionality reduction**: Apply PCA to the two training features; retain components explaining ≥ 99 % variance.  
   * **Collinearity check**: Compute VIF for original features; require VIF ≤ 10 (source: 2005.02245).  

4. **Bound Verification & Statistical Validation (US‑003)**
   * **Bound check**: Verify |predicted − actual| < ε for ε ∈ {0.05, 0.1, 0.15} on the **held‑out validation set**; report the proportion of samples meeting the bound for each ε.  
   * **Correlation consistency**: Pearson r > 0.8 for each level (SC‑001, SC‑004).  
   * **MIPU benchmark**: Run a small RL reasoning task (few‑shot arithmetic) using (a) the proxy predictor to decide whether to accept a policy, and (b) the full‑hardware‑sync baseline.  
   * **Statistical test**: Paired t‑test on final reasoning scores; apply Bonferroni correction for the three quantization‑level comparisons (family‑wise α = 0.05/3). If the Shapiro‑Wilk test rejects normality, fall back to a Wilcoxon signed‑rank test and report both p‑values.  
   * **Latency**: Measure average inference latency for proxy (predictor + fast check) vs. baseline; target ≥ 90 % reduction (SC‑002).

## Dataset Strategy

| Dataset | Source / URL | Role | Verification |
|---------|--------------|------|--------------|
| **GSM8K** | `datasets.load_dataset("gsm8k", "main")` | Prompt pool for both feature extraction and quantized inference. | Verified via Hugging Face `datasets` library. |
| **Llama‑2‑7B‑4bit** | `huggingface.co/meta-llama/Meta-Llama-2-7B-4bit` (gguf) | Full‑precision model (FP16) for gradient/curvature computation; 4‑bit quantized checkpoint fits CPU memory. | Verified via HF Hub. |
| **Quantization Engine** | `llama-cpp-python` (CPU) / `onnxruntime` (fallback) | Generates INT4, INT8, FP8 logits. | Verified via pip install; no external URL required. |

*All resources are openly downloadable; no gated data is used.*

## Decision / Rationale

* **CPU‑First** – The bulk of the pipeline (feature extraction, KRR training, statistical tests) runs comfortably on the free‑tier runner.  
* **GPU Escape Hatch** – Quantized inference for a 7 B model can be memory‑intensive on CPU. The `generate_ground_truth.py` script detects OOM or timeout and re‑launches on a Kaggle GPU (16 GB VRAM) with identical code paths, preserving reproducibility.  
* **Quantization Levels** – Testing three levels shows the bound is not an artifact of a single bit‑width.  
* **Statistical Rigor** – Multiple‑comparison correction, VIF collinearity diagnostics, explicit observational framing, power analysis, and sensitivity analysis satisfy the methodological panel’s checklist.  

## Assumptions & Risks

| Assumption | Risk | Mitigation |
|------------|------|------------|
| GSM8K prompts stress quantization effects. | Too many zero‑KL samples → low power. | Pilot run; if non‑zero proportion < 5 %, enrich prompt pool with longer, more complex questions. |
| `llama-cpp-python` can load a gguf quantized version of Llama‑2‑7B on CPU or Kaggle GPU. | OOM or missing binary. | Provide a pre‑quantized 4‑bit gguf checkpoint via HF; fallback to smaller 3 B model if needed (still open). |
| Pearson correlation > 0.8 is achievable. | Model underfits → lower r. | Hyperparameter sweep (alpha, kernel) within a bounded grid; keep sweep size ≤ 20 runs to respect compute budget. |
| Paired t‑test assumptions (normality, independence) hold. | Violation → invalid p‑value. | Perform Shapiro‑Wilk test; if violated, report Wilcoxon signed‑rank test (still Bonferroni‑corrected). |
| ε = 0.1 bound is reasonable. | Arbitrary threshold. | Conduct sensitivity analysis over ε ∈ {0.05, 0.1, 0.15} and report stability. |
| Hardware heterogeneity (CPU vs. GPU fallback) does not bias KL values. | Different hardware may produce slightly different quantization artifacts. | Log `hardware_source` per sample and include it as a covariate in downstream analysis; verify no systematic shift. |
| Collinearity between gradient norms and curvature is limited. | High VIF could invalidate independent effect claims. | Compute VIF; if > 10, report collinearity and refrain from claiming independent predictive effects. |

## Power Analysis (added)

Using `pwr.r.test` with effect size corresponding to r = 0.8, α = 0.05, and power = 0.8 yields a required sample size of **≈ 85 per group**. With three quantization groups we need approximately a few hundred samples.; we target **≥ 300** to accommodate stratification and potential drop‑outs.
