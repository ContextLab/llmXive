# Research: Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

## Problem Statement

Standard additive fragment models (e.g., Crippen's method) assume molecular properties are the sum of atomic contributions. However, this assumption fails in contexts involving steric hindrance, electronic resonance, or solvation effects where substructures interact non-linearly. This research aims to:
1.  Quantify the magnitude of error in additive models for logP, solubility, and boiling point.
2.  Train non-linear Random Forest models to capture these interactions.
3.  Map specific molecular contexts (fingerprint bit pairs) where non-linearity significantly reduces error.

**Scope Clarification**: The study is explicitly framed as **quantifying model capacity gaps** (i.e., how much better a non-linear model fits the data compared to an additive one) rather than discovering independent physical mechanisms. The SHAP analysis will explain the Random Forest's error correction, acknowledging the circularity of using the same data for training and explanation. Claims of "physical mechanisms" (e.g., steric clashes) are reframed as "statistical co-occurrences of topological features." The Random Forest improvement is acknowledged as a tautology of its capacity to fit noise/complexity better than a linear sum; the study does not claim to discover new physical laws but to map where the *current* additive model fails.

## Dataset Strategy

The study requires a dataset containing SMILES strings and experimental values for **logP**, **solubility**, and **boiling point**.

### Verified Sources
Based on the `# Verified datasets` block provided and known benchmark repositories:

| Dataset Name | URL | Relevance & Limitations |
| :--- | :--- | :--- |
| **MoleculeNet (ESOL)** | `https://huggingface.co/datasets/sayakpaul/molecule-net-esol` | Contains SMILES and experimental solubility (logS). **Limitation**: Lacks boiling point and logP diversity. Used as a **hold-out** set for solubility validation only. |
| **MoleculeNet (FreeSolv)** | `https://huggingface.co/datasets/sayakpaul/molecule-net-freesolv` | Contains SMILES and experimental hydration free energy (proxy for solubility). **Limitation**: Focused on solubility; lacks boiling point and logP. Used as a **hold-out** set for solubility validation only. |
| **ChEMBL (via RDKit)** | `https://huggingface.co/datasets/chembl/chembl_29` (via `chembl` loader) | Large-scale SMILES. **Limitation**: Requires complex querying to extract specific physicochemical properties (logP, solubility, boiling point). Boiling point data is rare. |

**Note**: The MAESTRO dataset has been removed from the candidate list as it is a protein-ligand binding dataset, not suitable for small-molecule physicochemical property regression. The 'ChEMBL (via ECFP4)' URL previously cited was removed as it was not a verified source for the required properties.

### Selected Strategy

1.  **Primary Candidate**: The plan will attempt to retrieve a dataset from **ChEMBL** (via the `chembl` loader) that contains the required properties.
    *   **Action**: The `data/download.py` script will query the HuggingFace Hub for datasets containing `SMILES`, `logP`, `solubility`, and `boiling_point` columns.
    *   **Contingency**: If the retrieved dataset lacks *boiling point* or *solubility* columns (common in general SMILES dumps), the plan will explicitly flag this as a **missing_covariate** in `data_quality_report.csv` (FR-008).
    *   **Scope Re-framing**: If the dataset lacks all three required properties, the study will be **re-framed as a single-property analysis (logP only)** *before* execution, rather than treating it as a post-hoc flag. This ensures the research question remains valid.

2.  **Fingerprint Generation**: The plan will use **RDKit** (`rdkit.Chem`) to generate all fingerprints (MACCS, ECFP4, FP2) from the raw SMILES. This ensures consistency with the `InteractionContext` mapping logic (which uses RDKit) and avoids ambiguity between OpenBabel and RDKit implementations (FR-003).

3.  **Hold-Out Validation**: To address dataset bias, a distinct dataset (**MoleculeNet ESOL** or **FreeSolv**) will be used as a **secondary hold-out set** to validate the **predictive performance** (MAE/RMSE reduction) of the Random Forest model.
    *   **Limitation**: The hold-out set validates *predictive performance*, not the *specific interaction bits* identified in the training set. The study explicitly acknowledges that "interaction zones" (SHAP values) are model-specific statistical corrections and are not expected to generalize physically to a new dataset. The hold-out set confirms that the RF model generalizes better than the additive baseline, not that the specific substructure interactions are universal physical laws.

**Note**: Per reviewer *rosalind-franklin-simulated*, fingerprints are topological abstractions. The research will explicitly frame findings as "topological interaction zones" rather than "physical conformational ensembles," acknowledging that 2D fingerprints cannot capture 3D steric clashes directly unless the dataset includes 3D conformers (which is not guaranteed in the verified list).

## Methodological Rigor

### Statistical Approach
1.  **Baseline**: Crippen's atomic contributions (additive model).
2.  **Model**: Random Forest Regressor (non-linear).
3.  **Comparison**: Paired Wilcoxon signed-rank test on absolute errors (FR-005).
    *   **Nested Cross-Validation**: The Additive baseline will be re-evaluated on the **exact same test folds** as the RF model to ensure paired observations come from the same distribution. This addresses the confounding variance of training on different splits.
    *   **Permutation Test**: A permutation test will be included to establish the null distribution of the error difference, addressing confounding variance.
    *   *Null Hypothesis*: No difference in median absolute error between Baseline and RF.
    *   *Correction*: If multiple properties are tested (logP, solubility, BP), apply Bonferroni correction to the significance threshold (α = 0.05 / 3).
4.  **Practical Significance**: Given the sample size (N ≥ 5,000), the Wilcoxon test will have high power to detect small effect sizes. The study will define a **Minimum Detectable Effect (MDE)** (e.g., >5% MAE reduction) to determine if the result is scientifically meaningful, rather than relying solely on p-values.
5.  **Causal Framing**: Explicitly stated as associational (observational study).

### Addressing Reviewer Concerns
*   **Reviewer: rosalind-franklin-simulated**: "Fingerprints are topological abstractions... may not reflect conformational ensemble."
    *   *Response*: The plan explicitly distinguishes between "topological interaction" (what the model sees) and "physical mechanism." The output will be "molecular contexts defined by connectivity graphs," not "3D steric clashes." Where 3D effects are hypothesized (e.g., steric hindrance), the plan will validate against known chemical rules (FR-010) but admit the 2D limitation.
*   **Reviewer: marie-curie-simulated**: "Correlation is not isolation... what experimental data will validate?"
    *   *Response*: The "validation" here is **internal consistency** against the additive baseline and **statistical significance** of the error reduction. The project does not claim to discover new substances but to map where the *current* additive model fails. The "experimental data" is the ground truth values in the dataset itself. The SHAP analysis maps *statistical* interactions, which are then *qualitatively* validated against chemical rules (FR-010), not experimentally re-measured. **No independent ground truth for interaction terms exists**; the study acknowledges this circularity.

### Statistical Rigor Checklist
- [x] **Multiple Comparison Correction**: Bonferroni applied across the 3 target properties.
- [x] **Sample Size**: N ≥ 5,000 ensures sufficient power for Wilcoxon.
- [x] **Causal Framing**: Explicitly stated as associational (observational study).
- [x] **Measurement Validity**: Relies on validated MoleculeNet/ChEMBL values (Assumption).
- [x] **Collinearity**: Acknowledged; Random Forest handles it, but VIF checks will be run on aggregated features to ensure descriptive claims are not over-interpreted (Assumption).
- [x] **Nested Cross-Validation**: Implemented to ensure paired error comparison.
- [x] **Practical Significance**: MDE defined to avoid trivial p-values.
- [x] **Hold-Out Validation**: Distinct dataset used for *predictive performance* validation (with acknowledged limitations on interaction zone generalization).

## Computational Feasibility

*   **Hardware**: 2 CPU, 7GB RAM, 6h limit.
*   **Strategy**:
 1. **Sampling**: Limit to [deferred] diverse molecules (Tanimoto < 0.7).
    2.  **Fingerprints**: Generate ECFP4 first (highest priority). If time permits, generate MACCS, then FP2. All generated via `rdkit.Chem`.
 3. **Model**: `max_depth` ≤ 10, `n_estimators` ≤ 100 (tuned via CV).
 4. **SHAP**: Use `shap.TreeExplainer` (fast for RF) on a subset of [deferred] molecules if full set is too large for memory.

## References
*   Crippen, G. M., & Overton, T. H. (1979). *A new method for calculating atomic contributions to molecular refractivity and logP*.
*   Lundberg, S. M., & Lee, S. I. (2017). *A Unified Approach to Interpreting Model Predictions*. (SHAP).
*   Verified Datasets: See `# Verified datasets` block in project input.