# Research: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## 1. Research Question & Hypothesis

**Primary Question (Reframed)**: Can a model learn the *simulation logic* mapping spectroscopic data to chemical reaction yields in a DFT-simulated regime, and can attention mechanisms identify the specific spectral regions responsible for this mapping?

**Hypothesis**: A multi-head attention model utilizing concatenated spectral, fingerprint, and condition inputs will significantly outperform baselines (fingerprint-only, spectrum-only, condition-only) on a leakage-free test set. Attention weights will align with the *simulated* functional group injection points.

**Critical Caveat**: Due to the lack of verified experimental paired spectra/yield data, the hypothesis that "spectroscopic data provides an *independent* predictive signal" is **not testable** in this regime. The plan includes a "Circularity Check" to reject this claim if the simulation is too deterministic.

## 2. Dataset Strategy

We will construct a composite dataset from open, programmatic sources. **Crucially, we will NOT use datasets requiring credentials (e.g., ADNI, HCP) or those without verified sources.**

### 2.1 Verified Datasets

| Dataset | Type | Verified URL | Usage Strategy |
|:--- |:--- |:--- |:--- |
| **DFT (Simulated Spectra)** | Simulated Spectra, Yield | ` | **Primary and Only Source.** We will use DFT-simulated spectra paired with computed yields. This aligns with the spec's "Simulated Validation Report" path. |
| **NIST (Reference)** | Functional Group Freq | **NO VERIFIED URL** | **Versioned Reference Module.** No verified programmatic dataset exists for the specific functional group frequencies required by FR-012. The plan implements a "Versioned Reference Module": a hard-coded, checksummed local JSON file (`src/data/nist_refs.json`) containing literature values for common functional groups (e.g., C=O, O-H, C-H). This file is generated once, checksummed, and stored in the repo. The `src/utils/nist_refs.py` module loads this file by hash. If the hash mismatches, the pipeline halts. This satisfies FR-012 without fabricating a non-existent URL. |

### 2.2 Data Integration Plan

1. **Single-Source Strategy**: We will **NOT** attempt to join USPTO and DFT datasets. The join strategy is deemed infeasible due to the lack of paired data at scale. We will use *only* the DFT dataset (sdmattpotter/dftest61523) for training and evaluation.
2. **Handling Missing Data**: If a reaction lacks NMR but has IR, the NMR channel will be masked (zero-filled with a mask vector) as per the "Edge Cases" in the spec.
3. **Dataset Size**: We will stream the DFT dataset (`streaming=True`) and sample a subset of [deferred] reactions to fit within 7GB RAM. This ensures the full pipeline runs within the designated time limit.

### 2.3 Dataset Feasibility Check

* **Variable Fit**: The DFT dataset contains simulated spectra (IR/Raman) and yields. It lacks explicit "reaction conditions" (solvent, catalyst) in the standard schema.
 * *Mitigation*: We will extract solvent/catalyst information from the DFT metadata (if available) or treat "reaction conditions" as a latent variable derived from the reaction template.
* **No Circular Validation**: By splitting strictly on reaction templates (FR-002), we ensure no template appears in both train and test.
* **Simulated Data Integrity (FR-015)**: We will perform the FR-015 check: verify that simulated spectra are not deterministic functions of fingerprints alone.
 * *Metric*: Train an MLP on fingerprints to predict the spectrum.
 * *Threshold*: If R² > 0.95, the "independent signal" hypothesis is **rejected** and flagged in `data/artifacts/integrity_report.json`.
 * *Output*: `data/artifacts/integrity_report.json` (contains R², threshold, and pass/fail status).

## 3. Methodology & Statistical Rigor

### 3.1 Model Architecture (FR-003)

* **Input**: Concatenation of `[Flattened Spectrum (IR+NMR), ECFP4 Vector, Condition Embedding]`.
* **Attention**: Multi-head self-attention layers (multiple heads) to allow the model to focus on specific wavenumbers/shifts.
* **Output**: Scalar yield (0-100).
* **Optimization**: Adam (LR=1e-3), Batch Size=32, Max Epochs=10, Early Stopping on Val RMSE (Patience=3).
* **CPU Feasibility**: The model will use `torch.float32` (default) but with a reduced hidden dimension (e.g., 64-128) to ensure training completes in <6 hours on 2 vCPU.

### 3.2 Baselines (FR-005)

1. **Fingerprint-Only**: MLP on ECFP4.
2. **Spectrum-Only**: MLP on flattened spectra.
3. **Condition-Only**: MLP on condition embeddings.
4. **Null Model**: Mean yield prediction.

### 3.3 Evaluation Metrics & Tests

* **Primary Metrics**: RMSE, MAE, R² (FR-005).
* **Statistical Significance (FR-006, SC-002)**: Paired t-test on absolute errors between Attention Model and best Baseline. **Bonferroni correction** applied for multiple comparisons (3 baselines).
* **Statistical Power & Effective Sample Size**:
 * *Calculation*: Count unique `reaction_template_id`s in the test set (N_templates).
 * *Threshold*: If N_templates < 50, the t-test is **suppressed**. The report will switch to reporting Mean Absolute Error (MAE) differences and 95% Confidence Intervals (bootstrapped) instead of p-values.
 * *Output*: `data/artifacts/power_analysis.json` (contains N_templates, power estimate, and test validity flag).
* **Permutation Test (FR-008, SC-004)**: Shuffle yield labels multiple times; retrain. Expect R² < 0.05.
* **Collinearity Check (FR-016)**: Compute Variance Inflation Factor (VIF) between spectral and fingerprint inputs. Flag if VIF > 5.
 * *Non-Linear Check*: Train a Random Forest to predict spectra from fingerprints. If RF R² > 0.8, the relationship is highly non-linear and VIF is insufficient. Report in `data/artifacts/nonlinear_check.json`.

### 3.4 Interpretability (FR-007, SC-003)

* **Attention Visualization**: Extract attention weights for the final layer. Map to spectral axis.
* **Peak Validation (Reframed)**: Identify top attention peaks. Compare wavenumbers to *simulated functional group injection points* (verified via simulation metadata).
 * *Success Criterion*: ≥80% of peaks within ±50 cm⁻¹ of simulated injection points.
 * *Null Baseline*: Generate a null distribution of attention maps by shuffling spectrum labels (keeping structure fixed) and re-training. The top peaks must be significantly higher (p < 0.05 via permutation test) than the 95th percentile of the null attention map.
 * *Literature Check*: Compare top peaks against the **Versioned Reference Module** (`src/data/nist_refs.json`). If a peak aligns with a literature value (e.g., C=O stretch at 1700 cm⁻¹), it is flagged as "Literature Validated". If the NIST module is unavailable or the peak does not align, the result is reported as "Simulation Validated Only".
* **Sensitivity Analysis (FR-009)**: Vary the attention threshold (90th, 95th, 99th percentile) to ensure identified regions are stable.
 * *Output*: `data/artifacts/sensitivity_analysis.json` (contains results for each threshold).

## 4. Compute Feasibility & Escape Hatch

* **CPU-First**: The entire pipeline (preprocessing, training, evaluation) is designed for CPU.
 * *Strategy*: Use `streaming=True` for data loading to avoid OOM. Use a small batch size (32) and limited epochs (10).
 * *Model Size*: Hidden size ≤ 128, 2-3 attention layers.
* **GPU Escape Hatch**: If the DFT dataset requires heavy DFT simulation (not just loading), or if the model fails to converge on CPU within 6h:
 * *Plan*: The execution script will detect `CUDA` availability. If not, it will proceed with the scaled CPU model. If the user explicitly requests a larger model, the script will attempt to offload to a Kaggle GPU (scaled to sufficient VRAM capacity, low-bit quantization).
 * *Decision*: For this plan, we **do not** plan a GPU run. The CPU-scaled approach is sufficient for the scientific question (proof of concept + interpretability).

## 5. Limitations & Assumptions

* **Data Source**: Reliance on DFT-simulated spectra may not perfectly reflect experimental noise. This is mitigated by the "Simulated Validation Report" requirement.
* **Condition Encoding**: If solvent/catalyst data is missing from the DFT dataset, the "condition" input will be a simplified reaction-type embedding.
* **Power**: Sample size may limit the power to detect small effect sizes in the t-test. We will report the achieved power or confidence intervals.
* **Circularity**: The "independent signal" claim is not testable with DFT data if the simulation is too deterministic. The plan includes a "Circularity Check" to reject the hypothesis if R² > 0.95.
* **NIST Reference**: No verified programmatic dataset exists for the specific functional group frequencies required. We use a versioned, checksummed local JSON file (`src/data/nist_refs.json`) as a "Versioned Reference Module".
* **DFT Generation Infeasibility**: Generating DFT spectra for USPTO reactions is computationally infeasible and is **NOT** part of the plan.