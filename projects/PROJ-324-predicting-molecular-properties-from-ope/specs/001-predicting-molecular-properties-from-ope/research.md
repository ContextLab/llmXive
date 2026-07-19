# Research: Molecular Property Prediction Pipeline

## Research Question

Which **topological interaction signatures** (identified via 2D fingerprint bit-pairs) are most predictive of logP, aqueous solubility, and boiling point, and how do non-linear Random Forest models compare to additive fragment models (Crippen) in capturing non-additive deviations?

*Note: This research question is reframed to acknowledge that 2D fingerprints capture topological connectivity, not 3D conformational ensembles or steric hindrance. The study identifies statistical dependencies (topological signatures) that correlate with non-additive behavior, rather than claiming to discover physical mechanisms.*

## Dataset Strategy

### Verified Datasets

| Dataset Name | Source URL | Access Method | Fields | Status |
|--------------|------------|---------------|--------|--------|
| PubChem Compound | https://pubchem.ncbi.nlm.nih.gov/ | `pubchempy` (Python API) | SMILES, LogP, Solubility, Boiling Point, Molecular Weight, **Property Type (Experimental/Computed)** | **Verified** |
| Open Babel | https://openbabel.org/ | CLI (`obabel`) | Fingerprint generation (MACCS, ECFP4, FP2) | **Verified** |

### Dataset Selection Rationale

- **PubChem**: Selected because it provides a programmatic, open API (`pubchempy`) that allows downloading real molecular data without registration or credentials. It contains the required fields (SMILES, LogP, Solubility, Boiling Point) and, crucially, the **property type** (Experimental vs. Computed) needed to filter for ground truth.
- **Open Babel**: Selected as the standard tool for generating topological fingerprints (MACCS, ECFP4, FP2) from SMILES strings. It is available as a CLI tool, fitting the CPU-first constraint.

### Data Availability & Feasibility

- **Download**: `pubchempy` allows fetching records by CID or name. A script will fetch a large set of molecules with known properties.
- **Filtering**: The script will **prioritize 'Experimental' values**. If a property is only available as 'Computed' (e.g., XLogP3), it will be recorded but flagged.
- **Threshold**: If the dataset contains <50% 'Experimental' values for a target property, the analysis for that property will be restricted to "Model Consistency" (comparing RF vs. Crippen on computational data) and the limitation will be explicitly reported.
- **Size**: ~A representative set of molecules is well within the RAM and disk limits of the free-tier runner.
- **Streaming**: Not required for [deferred] rows, but the code will be designed to handle larger datasets via streaming if needed.

### Data Hygiene

- **Checksums**: All downloaded files will be checksummed and recorded in `state/`.
- **Raw Data**: Preserved unchanged in `data/raw/`.
- **Derived Data**: Written to `data/derived/` with documented derivation steps.

## Methodological Rigor

### Statistical Approach

- **Model**: Random Forest (RF) with nested cross-validation (5x2) to avoid overfitting and provide unbiased performance estimates.
- **Baseline**: Crippen additive fragment model (implemented in `baseline.py`).
- **Comparison**: Paired Wilcoxon signed-rank test on absolute errors to compare RF vs. Baseline.
- **Multiple Comparisons**: If testing multiple properties (LogP, Solubility, BP), apply Bonferroni correction to the alpha level.
- **Power**: With [deferred] samples, the study is well-powered to detect small effect sizes (Cohen's d > 0.1).
- **Local Non-Additivity Index**: A novel metric correlating the residual difference (RF - Crippen) with the presence of specific substructures (identified via RDKit SMARTS) to answer "Which substructures?".

### Measurement Validity

- **LogP/Solubility/BP**: **Experimental** values from PubChem are preferred. If only 'Computed' values (e.g., XLogP3) are available, the analysis is restricted to "Model Consistency" to avoid circular validation (using a computational estimate to validate a model against another computational estimate).
- **Threshold**: A quantitative threshold (>50% experimental data) ensures the research question remains valid. If not met, the claim of "non-additivity" is reframed as "deviation from the Crippen model".

### Causal Inference & Collinearity

- **Observational**: This is an observational study; claims are correlational, not causal.
- **Collinearity**: Fingerprint bits are often correlated (e.g., ECFP4 bits overlap). SHAP interaction values will be used to identify interacting bit pairs, acknowledging collinearity.
- **Construct Validity**: The study explicitly acknowledges that 2D fingerprints cannot capture 3D steric hindrance directly. "Substructure" mapping is a post-hoc interpretation of topological bits using RDKit SMARTS, serving as a statistical proxy for physical interactions.

## Compute Feasibility

- **CPU-First**: Random Forest and SHAP on a large-scale dataset are feasible on a limited number of CPU cores.
- **Open Babel**: CLI calls are efficient and do not require GPU.
- **Memory**: [deferred] rows x ~1000 features (fingerprint bits) is ~50MB, well within 7GB RAM.
- **Time**: Full pipeline (download, preprocess, train, analyze) estimated at <4 hours on free-tier runner.

## Decision/Rationale

- **Dataset**: PubChem via `pubchempy` is the only verified, open, programmatic source for the required fields, including the crucial 'Experimental/Computed' flag.
- **Model**: Random Forest is chosen for its ability to capture non-linear interactions and provide feature importance (SHAP).
- **Baseline**: Crippen is the standard additive fragment model for LogP, making it a suitable baseline for non-additivity analysis.
- **Compute**: CPU-first approach is feasible and aligns with the project's constraints. No GPU escape hatch is needed for this scale.
- **Mapping**: RDKit SMARTS matching is used to map topological bits to substructures, replacing the need for an external database.

## Unresolved Concerns Addressed

- **Measurement Uncertainty**: Defined as optional/derived. If PubChem does not provide a confidence float, the field is null, and FR-008 logs "Missing Confidence Data".
- **Chemical Rules Database**: Replaced with `rdkit` substructure matching (SMARTS patterns) for self-contained analysis.
- **Circular Validation**: Addressed by filtering for 'Experimental' values and enforcing a 50% threshold. If not met, analysis is restricted to "Model Consistency".
- **Construct Validity**: Addressed by reframing the research question to "topological interaction signatures" and explicitly acknowledging the limitations of 2D fingerprints.