# Research: Predicting Molecular Properties from Quantum Chemical Calculations with Limited Computational Resources

## Executive Summary

This research validates the hypothesis that semi-empirical quantum chemical descriptors (DFTB) can predict molecular conformational energies with accuracy comparable to high-level DFT (B3LYP) while reducing computational cost by at least 10x. The study addresses the "physical model discipline" critique by acknowledging the limitations of gas-phase calculations and explicitly incorporating solvent/hydration parameters where available in the verified datasets, or by flagging this as a systematic uncertainty.

## Dataset Strategy

The project relies on the following verified datasets. **Note**: Where the spec requires specific properties (e.g., "post-task anxiety" equivalent in chemistry) not present in the verified sources, the plan explicitly states the mismatch and adapts the methodology rather than fabricating data.

| Dataset Name | Verified URL | Purpose | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **MAESTRO 2004 SYNTH** | ` | Primary source for DFT-calculated reference energies and SMILES. | **Verified**: Contains SMILES and DFT-calculated conformational energies (kcal/mol). |
| **DFT Test Set** | ` | Subset for high-level DFT benchmarking. | **Verified**: Contains DFT-calculated properties. Used to validate the high-level baseline. |
| **Semi-HOMO** | ` | Reference for HOMO/LUMO ranges. | **Verified**: Contains HOMO energies. Used for sanity checks on DFTB outputs. |
| **DFT23** | ` | Additional DFT validation data. | **Verified**: Contains DFT descriptors. |

**Gap Analysis & Mitigation**:
- **Hydration/Solvent Data**: The verified datasets (MAESTRO, DFT23) primarily contain gas-phase or implicit-solvent DFT calculations. Explicit "hydration shell" data (as requested by the Rosalind Franklin review) is not present in the verified URLs.
- **Mitigation**: The plan will explicitly state in the `research.md` and final paper that the model predicts *gas-phase* conformational energies. The absence of explicit hydration parameters is a fundamental limitation of the dataset, not a mitigable uncertainty. Where the dataset allows, implicit solvent models (e.g., SMD) will be invoked in the Psi4/DFTB+ step if supported by the verified data schema. If not, the limitation is clearly documented, and the "physical model" claim is restricted to the conditions of the data.
- **Experimental vs. Computational Ground Truth**: The original spec referenced "experimental barrier values". However, the verified datasets only provide DFT-calculated energies. The study is therefore framed as a **DFTB vs. DFT comparison**, where the DFT value serves as the "high-level baseline" or "reference truth" for the purpose of this computational study. No claims of experimental accuracy are made.

## Methodology

### 1. Data Ingestion & Preprocessing
- **Source**: Download `MAESTRO_2004_SYNTH.zip` from the verified URL.
- **Parsing**: Extract SMILES and DFT-calculated reference energies.
- **Cleaning**: Apply IQR method to detect and flag outliers in DFT-calculated energies.
- **Subsetting**: Select a representative subset (minimum 30 molecules) for high-level DFT calculations.

### 2. Descriptor Generation
- **Semi-Empirical (DFTB+)**:
 - Use DFT-optimized geometries (from the subset) for all DFTB+ calculations.
 - Compute HOMO, LUMO, Mulliken charges, Mayer bond orders.
 - **Constraint**: Run on CPU; stream molecules to avoid RAM overflow.
- **High-Level (Psi4)**:
 - Optimize geometries at DFT level (B3LYP/def2-SVP) for the subset.
 - Compute same descriptors.
 - **Constraint**: Restricted to the subset (≤ 30 molecules) to fit within 6h runtime.

### 3. Model Training & Evaluation
- **Algorithm**: Random Forest Regressor (scikit-learn).
- **Training**: Two models trained on the *same* subset:
 1. Model A: Trained on DFTB descriptors.
 2. Model B: Trained on DFT descriptors.
- **Validation**: 5-fold cross-validation.
- **Metric**: Mean Absolute Error (MAE) against DFT-calculated reference energies.
- **Statistical Test**: Bootstrap resampling on per-fold MAE values to generate a % confidence interval for the MAE difference.

### 4. Sensitivity & Feature Analysis
- **Feature Importance**: Extract top descriptors from Model A.
- **Sensitivity Sweep**: Vary feature importance threshold over multiple percentiles; report MAE degradation.
- **Collinearity Check**: Report correlation matrix for predictors; acknowledge if descriptors are definitionally related.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: If multiple hypothesis tests are run (e.g., comparing different subsets), a Bonferroni correction or similar family-wise error rate control will be applied.
- **Power Analysis**: Given the small subset size (n=30), the plan acknowledges limited statistical power. The study is framed as an *exploratory comparison* rather than a definitive power-validated trial.
- **Causal Claims**: No causal claims are made. Results are strictly associational (correlation between descriptors and conformational energies).
- **Measurement Validity**: DFTB and DFT methods are standard; validation against DFT-calculated energies is the primary metric of validity.
- **Collinearity**: If HOMO/LUMO are highly correlated with other electronic descriptors, independent effects will not be claimed; descriptive statistics will be reported.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (multiple CPU cores, 7GB RAM, 14GB Disk).
- **Strategy**:
 - DFTB+ and Psi4 invoked via system binaries with CPU flags.
 - Data streamed in batches (e.g., a small fixed number of molecules) for descriptor generation.
 - Random Forest models trained on the small subset (≤ 30 molecules) to ensure sub-minute training times.
 - No GPU usage; no large language models.
- **Runtime**: Estimated < 4 hours (allowing A duration of several hours for DFT on a subset, A short duration for DFTB, A dedicated period for modeling.).

## Computational Approximation Validation

The DFT-calculated reference energy is a computational approximation, not an independent experimental truth. The comparison between DFTB and DFT models is a validation of the semi-empirical method's ability to reproduce the high-level DFT results, not a validation against physical ground truth. This limitation is explicitly acknowledged in the final paper.