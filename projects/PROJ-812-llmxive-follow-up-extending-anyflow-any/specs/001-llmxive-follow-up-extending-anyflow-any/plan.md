# Implementation Plan: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Branch**: `001-llmxive-follow-up-extending-anyflow-any` | **Date**: 2026-08-22 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-anyflow-any/spec.md`

## Summary

This feature implements a CPU-tractable experimental pipeline to validate the hypothesis that "flow-map divergence" (numerical instability in the AnyFlow video diffusion model) correlates with semantic temporal discontinuities (scene cuts) in video data. The plan executes a stratified download of video clips from UCF101 and DAVIS, a rigorous manual pixel-space annotation process with dual-annotator reliability checks, CPU-only latent trajectory inference using the AnyFlow model (ONNX Runtime), and rigorous statistical analysis (Pearson/Spearman correlation, t-tests, logistic regression, and sensitivity sweeps) to quantify the relationship. The implementation strictly adheres to the 2-core CPU/7GB RAM constraints of the GitHub Actions free tier, employing runtime fallbacks (N=200 steps) if the baseline N=500 exceeds time budgets.

**Key Revisions**: 
- **Annotation Protocol**: Added mandatory dual-annotator pilot and calibration phase to ensure ground truth reliability (addressing methodology concerns).
- **Statistical Rigor**: Explicitly prioritized Spearman correlation for ordinal data while justifying Pearson for -point scales via the assumption of approximate interval scaling; added t-test for correlation significance and control analysis for group differences.
- **Data Integrity**: Replaced dataset URLs with verified raw video sources and direct model weight links; added FFmpeg dependency for video decoding.
- **Metric Definition**: Clarified that sensitivity sweeps test robustness, not redefine the metric; acknowledged baseline approximation limits and the mathematical dependency of the metric on N.
- **Reliability Protocol**: Defined a full-dataset reliability protocol (A subset of dual-annotated data) to adjust power analysis.
- **Control Experiments**: Added specific control experiments to distinguish video-induced vs. model-induced stiffness.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `onnxruntime`, `datasets` (Hugging Face), `pandas`, `scikit-learn`, `scipy`, `numpy`, `opencv-python-headless` (requires `ffmpeg`), `h5py`, `statsmodels`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `artifacts/`)  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Research Pipeline / CLI  
**Performance Goals**: Full pipeline (500 clips) ≤ 6 hours on 2 vCPU, 7GB RAM.  
**Constraints**: CPU-only execution; no CUDA; strict memory cap (7GB); no GPU offloading for the core metric (as per spec FR-002/FR-005); manual annotation is a human-in-the-loop step (scripted interface provided).  
**Scale/Scope**: A dataset of video clips (16 frames @ 30fps); -clip pilot for runtime estimation; threshold sweeps; baseline resolution sweeps.

## Constitution Check

| Principle | Compliance Status | Action Required |
|-----------|-------------------|-----------------|
| **I. Reproducibility** | **Compliant** | Pin `requirements.txt`; seed random state in `code/`; use canonical Hugging Face URLs for datasets. |
| **II. Verified Accuracy** | **Compliant** | All dataset URLs cited in `research.md` are from the verified list. Pre-flight URL validation added to `download.py` to re-verify citations. |
| **III. Data Hygiene** | **Compliant** | `data/raw` (downloaded clips) immutable; `data/processed` (scores/metrics) derived with checksums; PII scan on `data/`. |
| **IV. Single Source of Truth** | **Compliant** | Final report pulls stats directly from `data/processed/correlation_results.csv` and `data/processed/sensitivity_report.csv`. |
| **V. Versioning Discipline** | **Compliant** | Artifacts hashed in `state.yaml`; `code/` scripts versioned with content hashes. |
| **VI. Latent Trajectory Fidelity** | **Compliant** | Plan explicitly uses frozen AnyFlow weights (verified source); ONNX conversion logic documented; correlation stability check ($\pm 0.05$) implemented in `analysis.py` and logged to `variance_report.csv`. |
| **VII. Temporal Continuity Ground Truth** | **Compliant** | Manual scores (pixel-only) stored in `data/raw/ground_truth.csv` before any inference; correlation strictly between this and divergence. Dual-annotator Kappa check ensures reliability. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-anyflow-any/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters (N=500, thresholds)
│   ├── download.py            # FR-001: Stratified download from UCF101/DAVIS; Pre-flight URL check
│   ├── annotate.py            # FR-002: CLI for manual scoring (Likert rubric); captures annotator_id/timestamp
│   ├── inference.py           # FR-003/FR-004: CPU-only AnyFlow latent extraction & divergence calc
│   ├── analysis.py            # FR-005/FR-006: Correlation, regression, sensitivity sweeps, t-tests, stability check
│   ├── validate.py            # FR-009/FR-010: Pilot runtime check, variance/Kappa checks; generates variance_report.csv
│   └── report.py              # FR-007/FR-008: Final report generation; links variance_report.csv
├── data/
│   ├── raw/                   # Downloaded video clips, ground_truth.csv, calibration_scores.csv
│   ├── processed/             # divergence_metrics.csv, sensitivity_report.csv, variance_report.csv, correlation_results.csv
│   └── checksums.txt          # SHA256 hashes of raw/processed
├── tests/
│   ├── unit/                  # Metric logic, file I/O
│   └── integration/           # End-to-end pipeline on 10 clips
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (Option 1) is selected. This is a linear research pipeline (Download → Annotate → Inference → Analysis) without a web service or mobile component. The separation of `data/raw` and `data/processed` enforces the Data Hygiene principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Manual Annotation Step** | Ground truth must be pixel-based, not model-derived (FR-002). | Automated metrics (e.g., optical flow) would introduce circular logic and violate the "Temporal Continuity Ground Truth" principle. |
| **Dual-Annotator Pilot** | Required to quantify inter-annotator reliability (Kappa) and ensure ground truth validity (Methodology Concern). | Single annotator risks high measurement error, capping observable correlation and invalidating power analysis. |
| **Calibration Phase** | Ensures annotators can distinguish cuts from motion before the main run (Methodology Concern). | Untrained annotators may confuse model instability with semantic cuts, invalidating the ground truth. |
| **Runtime Fallback Logic (N=200)** | FR-009 requires dynamic adjustment if N=500 exceeds 5.5h. | A static N=500 plan risks timeout failure; dynamic fallback ensures feasibility within CI limits. |
| **Bimodal Analysis Branch** | FR-010 mandates Fisher's Exact Test if data is bimodal (0.0/1.0) with N≥50. | Standard correlation assumes continuous variance; ignoring bimodality would violate statistical rigor. |
| **Stability Check (Const VI)** | Constitution VI requires correlation stability within ±0.05. | Without this check, numerical artifacts could mimic semantic instability. |
| **Reliability Protocol** | Power analysis requires a known reliability coefficient. | Extrapolating pilot Kappa to the full dataset without verification is statistically unsound. |
| **Control Experiments** | To distinguish video-induced vs. model-induced stiffness. | Comparing groups within the same model does not isolate the source of stiffness. |

## Statistical Analysis Plan (Detailed)

1.  **Data Validation**:
    *   **Variance Check**: Calculate variance of `ContinuityScore`. If < 0.05 and not bimodal (Hartigan's Dip Test p >= 0.05), halt with "Insufficient Variance".
    *   **Bimodality Check**: If bimodal (Dip Test p < 0.05) and N >= 50, proceed to Fisher's Exact Test. Binarization rule: Score >= 3 (5-point scale) = 1 (discontinuous), < 3 = 0 (continuous). If data is skewed but not perfectly bimodal, the threshold is set to the **median** (pre-registered).
 * **Reliability Check**: Calculate Cohen's Kappa on the pilot subset (≥ 0.81 required). Calculate reliability on the [deferred] full-dataset dual-annotation subset to adjust effective sample size for power analysis.
2.  **Correlation Analysis**:
    *   **Primary**: Spearman Rank Correlation (robust to ordinal data).
    *   **Secondary**: Pearson Correlation. **Justification**: Treats the 5-point Likert scale as approximately interval data, a common psychometric practice. The assumption is explicitly stated in the report.
    *   **Significance**: Perform t-test on Pearson coefficient ($H_0: r=0$) with $\alpha=0.05$.
3.  **Control Analysis**:
    *   **Group Comparison**: Compare divergence scores between "continuous" (Score < 3) and "discontinuous" (Score >= 3) groups using Mann-Whitney U test (non-parametric) or t-test if normality holds.
    *   **Model-Induced Stiffness Control**: Run the metric on a known stable video (static image) with a known unstable model configuration (if available) to distinguish video-induced vs. model-induced stiffness.
4.  **Regression**:
    *   **Multivariate Logistic Regression**: Predict discontinuity type using divergence features (kurtosis, clustering).
    *   **Collinearity Check**: Calculate VIF. If VIF > 5 for any feature, drop it. If all features are definitionally related to the primary metric, run regression with only the primary divergence score.
5.  **Sensitivity Analysis**:
    *   Sweep thresholds {, representative low value, 0.1} and baseline resolutions {, 200, 100}.
    *   **Note**: The primary metric is fixed at N=500. The sweep tests the robustness of the *correlation* to the baseline resolution, acknowledging that the metric value itself is mathematically dependent on N.
    *   Report FP/FN rates for each combination.
6.  **Stability Check (Const VI)**:
    *   Perturb latent inputs with Gaussian noise ($\sigma=0.01$).
    *   Re-calculate correlation. If $|r_{original} - r_{perturbed}| > 0.05$, flag as "Unstable".
7.  **Reporting**:
    *   Generate `variance_report.csv` (from `validate.py`).
    *   Generate `correlation_results.csv` and `sensitivity_report.csv` (from `analysis.py`).
    *   `report.py` embeds `variance_report.csv` into the final text.

## Data Availability & Feasibility

*   **Datasets**: UCF101 (HF subset) and DAVIS 2017 (Official HF video archive). Both are verified, open, and directly downloadable.
*   **Model**: AnyFlow PyTorch weights (direct `.pt` file on HF). Conversion to ONNX is performed once during setup.
*   **Compute**: 2 vCPU, 7GB RAM.
    *   **Pilot**: 30 clips with N=500. If projected time > 5.5h, switch to N=200.
    *   **Memory**: Batch processing (fixed-size batches), streaming video loading, garbage collection after each batch.
    *   **Dependencies**: `ffmpeg` installed on runner (via `requirements.txt` system deps) for video decoding.

## Decision/Rationale

*   **Why Dual-Annotator Pilot?** To ensure ground truth reliability. Measurement error in the dependent variable (Continuity Score) attenuates correlation. A Kappa < 0.81 indicates the ground truth is too noisy to detect the hypothesized effect.
*   **Why Spearman Primary?** The ground truth is ordinal (Likert). Spearman is the statistically correct choice. Pearson is reported for completeness and comparability with prior literature, with the justification that 5-point scales often approximate interval data.
*   **Why Control Analysis?** To explicitly test if divergence differs between groups, addressing the "model-induced stiffness" concern.
*   **Why Sensitivity Sweep?** To verify that the correlation is robust to the choice of baseline resolution (N), ensuring the result is not an artifact of a specific discretization.
*   **Why Median Binarization?** To avoid post-hoc p-hacking. The threshold is pre-registered as the median for skewed data.
