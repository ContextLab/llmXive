# Research: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Executive Summary
We evaluate whether numerical instability ("flow‑map divergence") in a distilled video diffusion model correlates with **semantic** temporal discontinuity (scene cuts). The pipeline uses **human‑rated continuity scores** as independent ground truth, runs all inference on CPU‑only hardware, and reports only associational findings. The study strictly separates the *pipeline integrity test* (synthetic data) from the *scientific validation* (human data) to ensure validity.

## Dataset Strategy

### Verified Datasets
| Dataset | Source URL | Usage | Verification |
|---------|------------|-------|--------------|
| **UCF101 (continuous motion)** | `https://huggingface.co/datasets/flwrlabs/ucf101` | Provides clips with smooth action; used for the "continuous" stratum. | Verified (HF repo, direct download). |
| **MovieNet (scene cuts)** | `https://huggingface.co/datasets/MovieNet/movinet` | Contains frame‑level scene-cut annotations; used for the "cut" stratum. | Verified (HF repo, includes explicit cut labels). |
| **AnyFlow Model** | `https://huggingface.co/datasets/simbahuang/anyflow-p0-status/resolve/main/experiments/anyflow-aapt-go24h-20260712T0235/a-dynamics500-s0/manifests/a_checkpoint_manifest.json` | Frozen weights for ONNX conversion. | Verified. |

*All URLs have been programmatically verified by the Reference‑Validator Agent.*

### Data Acquisition & Stratification (FR‑001)
1. **Streaming download** via `datasets.load_dataset(..., streaming=True)`.  
2. **Stratified sampling**:  
   - A representative set of clips sampled from UCF101 (assumed continuous based on action class).  
   - 250 clips sampled from MovieNet where `has_cut == true` (verified scene cuts).  
3. **Clip format**: 16 frames, 30 fps, saved under `data/raw/video_clips/`.  
4. **Memory safety**: streaming + batch size = 10 ensures < 7 GB RAM.

### Ground‑Truth Annotation (FR‑002, FR‑010)
*Human annotation is performed **outside** CI on the curated clips.*  
- Two independent annotators rate each clip on a 5‑point Likert scale (1 = perfect continuity, 5 = maximal discontinuity) using a dedicated tool (e.g., Label Studio or Google Forms).  
- Scores are converted to a continuous `ContinuityScore` in `[0.0, 1.0]`.  
- The resulting CSV is uploaded to `data/raw/ground_truth.csv` and checksummed.  
- `annotation/validate_annotations.py` computes **Cohen's Kappa**; the pipeline aborts if κ < 0.81.  
- Disagreements (> 1 Likert point) are sent to a **third expert** via `annotation/adjudicate.py`, producing a final immutable `ground_truth.csv`.  
- The raw CSV is checksummed (`utils/checksums.py`) before any downstream computation (Principle VII).

## Methodology

### 1. Model Inference (FR‑003)
- Frozen AnyFlow weights are converted to ONNX Runtime (CPU) on‑the‑fly (`model/load_onnx.py`).  
- No GPU is used; all inference runs on the GitHub Actions runner.

### 2. Flow‑Map Divergence Calculation (FR‑004)
- **Baseline**: Explicit Euler integration with `N=500` steps (or reduced to `N=200` per FR‑009). Convergence defined as ΔMSE < 1e‑4 between successive N.  
- **Metric**: Normalized MSE across 16 frames, plus temporal features (kurtosis, clustering).  
- **Control analysis**: `analysis/control_analysis.py` runs a KS test comparing divergence distributions of the verified smooth (UCF101) vs. cut (MovieNet) groups and outputs a report validating the stratification.  
- **Null hypothesis test**: Fisher's r‑to‑z transformation (`analysis/fisher_r_to_z.py`) tests H₀: r = 0 at α = 0.05 as a distinct step.

### 3. Statistical Analysis (FR‑005, FR‑006, FR‑008, FR‑009, FR‑011, FR‑012)
- **Correlation**: Pearson (primary) and Spearman (ordinal) computed in `analysis/correlation.py`.  
- **Inverse‑Probability Weighting (IPW)** applied to correct the artificial 50/50 sampling when estimating population‑level effects. The ground truth is independent (human scores), so IPW is a valid correction for the sampling strategy.  
- **Logistic regression** (multivariate) predicts binary cut vs. continuous using divergence and temporal features.  
- **Sensitivity sweep** over thresholds {0.01, 0.05, 0.1} and Euler steps {500, 200, 100} (`analysis/sensitivity.py`).  
- **Power analysis** (`analysis/power_analysis.py`) confirms N=500 yields ≥ 80 % power for detecting r≈0.12; if the pre‑flight estimate exceeds 5.5 h, N is reduced to 200 and a pilot re‑run verifies r > 0.7 before full execution (FR‑009).  
- **Synthetic validation** (`analysis/synthetic_validation_subset.py`): generates a 50‑clip synthetic subset with known binary labels (using `hypothesis`), runs the full metric pipeline, and checks that false‑positive/false‑negative rates match hand‑calculated expectations within 0.01 absolute error (FR‑012).  
- **Fidelity check** (`analysis/fidelity_check.py`) adds Gaussian noise to latent vectors and confirms Pearson r changes ≤ 0.05 (Constitution VI).

### 4. Reporting
- Final report (`results/final_report.md`) contains Pearson r, Spearman ρ, p‑values, IPW‑adjusted logistic regression accuracy, control‑analysis KS statistics, sensitivity tables, and explicit statements that the relationship is **associational**, not causal (FR‑007, FR‑008).

## Decision Rationale: Compute Strategy
- **CPU‑first**: All heavy lifting (ONNX inference, Euler integration) runs on CPU; no GPU emulation.  
- **Streaming**: Guarantees < 7 GB RAM.  
- **Scalability**: If runtime exceeds budget, the pipeline automatically falls back to N=200 and re‑validates correlation stability.

## Two-Phase Validation Strategy
- **Pipeline Integrity Test**: Uses a synthetic subset (FR-012) with known labels to verify code correctness and error rates. This does *not* validate the scientific hypothesis.
- **Scientific Validation**: Uses independent human annotations (FR-002) to test the hypothesis. This is the only data used for the final correlation and regression results.