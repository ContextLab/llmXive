# Research: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Problem Statement

Diffusion in alloys is a critical process in materials science, governing phenomena like creep, precipitation, and phase transformations. The activation energy ($Q$) for diffusion is often altered by the presence of solute atoms. This project aims to predict the shift in activation energy ($\Delta Q$) for FCC metals as a function of solute properties, specifically testing the hypothesis that atomic size mismatch is a primary driver, using **real experimental data**.

## Dataset Strategy

### Data Availability Analysis

The spec requires data from "Materials Project" and "NIST" regarding FCC self-diffusion.
**Constraint**: The provided "Verified datasets" block contains URLs for NIST 800-53 (security), FCC (regulations/comments), BCC (text), HCP (text), and CUDA (code). **None** of these verified URLs contain materials science diffusion data.

**Resolution**:
1.  **Real Data Hunt**: The plan **must** attempt to download a real, open-access FCC diffusion dataset from verified sources (e.g., Zenodo, OpenKIM open subset, UCI).
2.  **No Synthetic Data**: **No synthetic data will be generated** to simulate results. If no real data is found, the project halts with a "Data Unavailable" report. This avoids the circular validation of training on a generator and testing on the same generator.
3.  **Fallback**: If no open real data is found, the project is re-scoped to "Methodology Validation" using a **curated CSV from a verified open repository** (e.g., a specific Zenodo record containing real diffusion data). If even this is unavailable, the project is paused.

### Data Sources (Real Experimental Data)

| Dataset Component | Source/Method | Justification |
| :--- | :--- | :--- |
| **Atomic Properties** | `periodictable` library (v1.7+) | Standard, versioned source for radii/electronegativity. |
| **Diffusion Data** | Zenodo / OpenKIM Open Subset (Real Data Hunt) | Provides real experimental activation energies, crystal structures, and concentrations. |
| **Baseline Reference** | `data/reference/pure_metals_q.csv` (Curated) | Standard reference for $Q_{host}$ if dataset lacks 0 at.% rows. |
| **Validation** | `pytest` against physical constraints | Ensures data respects thermodynamic bounds (e.g., $Q > 0$). |

**Decision/Rationale**:
*   **CPU-First**: The data ingestion and subsequent models (RF, GB, Linear) are purely CPU-tractable. No GPU is required.
*   **Data Integrity**: The real data is downloaded with a fixed seed for any stochastic sampling (if needed) to ensure reproducibility (Constitution Principle I). The "ground truth" is the **experimental measurement**, not a generator.
*   **Risk Mitigation**: If the open dataset is too small (< 50 points), the study will be framed as an **exploratory pilot** with explicit power limitations, rather than a definitive study. This is scientifically honest and avoids the "meaningless power" fallacy of synthetic data.

## Statistical Rigor

### Methodology
1.  **Multiple Comparisons**: The project runs three models (RF, GB, Linear). Since the goal is prediction vs. inference, no family-wise error correction is strictly required for the *prediction* models. However, for the Linear Regression inference (FR-005), the p-value is reported for the specific hypothesis ($\beta_{size} \neq 0$).
2.  **Power Justification**: The power analysis will be performed on the **observed effect size** in the real dataset. If the dataset is small (N < 50), the plan will explicitly state that the study is "exploratory" and the power is limited, rather than fabricating a high-power claim. The study will not claim to "predict real-world phenomena" definitively if N is too small.
3.  **Causal Inference**: The spec explicitly states (Assumption) that the data is observational. Claims will be framed as **associational**. The Linear Regression coefficient indicates the *association* between size mismatch and activation energy shift, not a causal effect.
4.  **Measurement Validity**: Atomic radii from `periodictable` are standard proxies. The "size mismatch" descriptor is a well-established heuristic in materials science (Hume-Rothery rules).
5.  **Collinearity**: Size mismatch and electronegativity difference are often correlated. The plan will check Variance Inflation Factors (VIF). If VIF > 5, the Linear model will be interpreted with caution regarding independent effects, or a regularization technique (Ridge) will be used for inference stability.

## Compute Feasibility

*   **CPU-First**: All models (Random Forest, Gradient Boosting, Linear Regression) are available in `scikit-learn` and run efficiently on CPU.
*   **Memory**: With N < 500, memory usage will be < 100 MB.
*   **Time**: Grid search (5-fold CV) on < 500 points will take < 5 minutes.
*   **GPU Escape Hatch**: Not required. No transformer or diffusion models are used.

## Data Availability & Handling

*   **Streaming**: Not required for this dataset size (< 10 MB).
*   **Gated Data**: No gated data is planned. If the spec required ADNI or full Materials Project, this project would fail feasibility. The plan uses **open subsets** or **Zenodo** records.
*   **Data Hygiene**: The real data download writes a checksum to `data/curated/data_provenance.json`. No data is modified in place.

## Threshold Sensitivity Analysis

The sensitivity analysis defines "significant diffusion slowing" relative to the **real experimental variance** (error bars) in the dataset. If error bars are unavailable in the dataset, the plan uses the **model's RMSE** as a conservative estimate, explicitly labeled as such in the report. The threshold sweep (0.45–0.55 eV) is designed to validate that conclusions are robust to small variations in the definition of "significant," acknowledging that no universal physical threshold exists.