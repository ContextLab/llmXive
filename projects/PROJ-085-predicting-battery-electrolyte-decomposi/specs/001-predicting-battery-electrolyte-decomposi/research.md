# Research: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

## Problem Statement

The goal is to predict the **thermodynamic stability** (decomposition energy, $E_{decomp}$) of battery electrolytes (e.g., EC, DMC, LiPF6) under varying electrochemical potentials. The challenge lies in:
1.  **Data Availability**: Sourcing ground-state DFT descriptors (HOMO, LUMO, bond lengths) and total energies for specific electrolyte species from literature, **AND** ensuring the same molecules have experimental onset potentials for validation.
2.  **Label Construction**: Deriving synthetic labels for decomposition energy using the formula $E_{decomp} = E_{products} - E_{reactants} - nF\phi$. This label represents **thermodynamic stability**, not experimental kinetic onset.
3.  **Leakage Prevention**: Ensuring that features used for prediction (e.g., HOMO, bond lengths) are NOT mathematically identical to the target. **Identity features (`reactant_energy`, `product_energy`) are excluded from the input feature set entirely before any model training.**
4.  **Validation**: Assessing the correlation between thermodynamic predictions and experimental kinetic onset potentials, while explicitly acknowledging the physics gap. **No bias correction is applied.**

## Dataset Strategy

The project relies on a **manually curated, literature-sourced dataset** of real battery electrolytes. **No synthetic data generation is permitted.**

### Gap Analysis
-   **Required Variables**: HOMO, LUMO, bond lengths, `reactant_energy`, `product_energy`, potential ($\phi$), experimental onset (for validation).
-   **Available Public Sources**:
    -   `matchbench/semi-homo`: General HOMO data, not specific to battery electrolytes or lacking total energies. **Not suitable.**
    -   `proteinea/remote_homology`: Protein homology, irrelevant.
    -   `Lumos` datasets: Text/LLM evaluation, irrelevant.
    -   `CUDA` datasets: GPU engineering logs, irrelevant.
-   **Conclusion**: The provided verified dataset list **does not** contain the specific battery electrolyte data required. **No public dataset exists for this specific combination.**

### Strategy Adjustment
Per the specification's "Assumptions" section and the need for real physics:
1.  **Manual Curation**: We will extract a small dataset (n ~ 20-50) of common electrolytes (EC, DMC, LiPF6) from **published computational chemistry papers** (e.g., *Journal of Physical Chemistry C*, *Electrochimica Acta*) where DFT energies and experimental onsets are reported for the **same molecules**.
2.  **Verified Source Requirement**: The pipeline **must** identify specific peer-reviewed papers with DOIs that contain the required variables. **If no such paper is found, the pipeline halts with a "Data Scarcity" report.** **No synthetic data will be generated.**
3.  **Static Artifact**: This curated data will be saved as a static CSV (`data/raw/literature_subset.csv`) and checksummed. This is the **canonical source** for this project.

### Data Sources (Cited Literature)
The following papers are **candidates** for the manual curation step. The pipeline will halt if these specific papers (or equivalent verified sources) are not found:
-   **Candidate 1**: *Search for papers containing DFT energies (HOMO/LUMO/Total) AND experimental onset for EC, DMC, or LiPF6.* (e.g., specific papers from *J. Phys. Chem. C* or *Electrochim. Acta*).
-   **Note**: The exact values are not listed here but will be extracted and stored in `data/raw/literature_subset.csv` only after the DOI and content are verified.

## Methodological Rigor

### Statistical Approach
-   **Model**: Random Forest Regressor (Scikit-learn).
-   **Validation**: 5-fold Cross-Validation stratified by potential level ($\phi$).
-   **Collinearity**: Variance Inflation Factor (VIF) calculation. Any predictor pair with VIF ≥ 10 is flagged.
-   **Leakage Detection (FR-010)**: **Partial Correlation Analysis**.
    -   **Order of Operations**: 1) Calculate Target. 2) **Drop Identity Features** (`reactant_energy`, `product_energy`) from input. 3) Calculate Partial Correlation between *remaining* features and target.
    -   **Rejection Rule**: If partial correlation > 0.9, the feature is **rejected**.
    -   **Residual Check**: If the remaining feature set still shows partial correlation > 0.9, the pipeline halts.
    -   **Consequence**: The model trains ONLY on non-identity features (e.g., HOMO, LUMO, bond lengths). If all features are rejected, the study reports "No viable non-identity features found."
-   **Multiple Comparisons**: Permutation importance is calculated for all features. If multiple potential levels are tested, family-wise error rate (FWER) correction is applied to the significance of feature shifts.
-   **Causal Framing**: All results are framed as **associational**. No causal claims are made.

### Physics Gap & Bias Correction
-   **Physics Gap**: Acknowledged that DFT thermodynamic stability ($E_{decomp}$) $\neq$ Experimental kinetic onset.
-   **Bias Correction**: **None**. A linear offset cannot account for non-linear kinetic barriers. The plan explicitly reports the raw correlation coefficient between thermodynamic predictions and kinetic onsets as a measure of association, not a corrected prediction.

### Power and Sample Size
-   **Limitation**: The sample size (n ~ 20-50) is small.
-   **Acknowledgement**: The plan explicitly states that the power to detect small effect sizes is limited. Results are treated as a **feasibility study** rather than a definitive predictive model.

## Risk Assessment

1.  **Data Scarcity**: The literature subset may be too small or lack experimental onset data for the same molecules.
    -   *Mitigation*: If n < 10 or no intersection exists, the study concludes with a "Data Scarcity" finding.
2.  **Feature Rejection**: Partial correlation may reject all features, or residual correlation may remain high.
    -   *Mitigation*: The plan handles this by halting and reporting "No viable features" or "Residual Identity Detected," which is a valid scientific outcome.
3.  **Weak Correlation**: The correlation between thermodynamic and kinetic stability may be weak.
    -   *Mitigation*: The plan explicitly reports this as a limitation.
4.  **Validation Impossible**: If the intersection of training molecules and experimental data is empty.
    -   *Mitigation*: The pipeline halts with a "Validation Impossible" report, satisfying the requirement to not fake validation.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Manual Literature Curation** | No public dataset contains the required variables. Synthetic data is scientifically invalid for this task. |
| **Rejection of Identity Features** | To prevent circular validation (target = linear combination of inputs), features with partial correlation > 0.9 are rejected. **Identity features are dropped before input.** |
| **Residual Correlation Check** | To ensure the remaining features are not still mathematically tied to the target, a residual check is performed. |
| **No Bias Correction** | A linear offset cannot bridge the non-linear physics gap between thermodynamics and kinetics. |
| **Associational Claims Only** | Observational data (DFT calculations) without random assignment of potentials. |
| **VIF Threshold of 10** | Standard threshold for multicollinearity; aligns with spec requirement. |
| **Partial Correlation Threshold of 0.9** | Strict threshold to ensure no mathematical identity leakage. |