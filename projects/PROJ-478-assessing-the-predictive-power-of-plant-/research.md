# Research Notes: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

## Spec-Plan Divergence: Trait Imputation Strategy (FR-004 Override)

### Context
The project specification (Spec) and the project plan (Plan) contain a critical divergence regarding the handling of functional trait data for held-out species during Leave-One-Species-Out (LOSO) cross-validation.

### Specification Requirement (FR-004)
The Spec mandates that for the primary evaluation workflow, **known trait values** must be used for the held-out species. This ensures a rigorous, unbiased assessment of the model's ability to predict distribution based on actual biological characteristics, avoiding circularity where the model predicts traits it is then tested on.

> **Spec FR-004**: "Use known trait values for the held-out species during LOSO evaluation."

### Plan Strategy (Trait Imputation)
The project Plan proposes an alternative strategy: predicting (imputing) traits for the held-out species using a climate-niche model trained on the remaining N-1 species, and then using these *predicted* traits in the SDM. This approach aims to simulate a real-world scenario where trait data is missing, but it introduces a dependency chain that may inflate performance metrics or obscure the true predictive power of the traits themselves.

> **Plan Override**: "Predict traits for the held-out species using a climate-niche model trained on N-1 species."

### Implementation Decision
To ensure scientific validity and adherence to the primary specification requirements while still exploring the Plan's hypothesis:

1. **Primary Path (Spec-Compliant)**: The core LOSO workflow (`src/modeling/loso_cv.py`) is implemented to strictly use **known trait values** for the test species. This is the default behavior and the basis for the primary results reported in `results/stats_report.json`.
2. **Secondary Path (Plan Exploration)**: An optional branch in the LOSO workflow implements the trait imputation strategy. This allows for a comparative analysis to quantify the impact of trait uncertainty on SDM performance, but these results are clearly labeled as "Imputed Traits Analysis" and are not used for the primary scientific conclusions unless explicitly requested.

### Rationale
Using known traits (Spec FR-004) isolates the variable of interest: *Can functional traits improve SDMs beyond climate alone?*
Using imputed traits conflates two errors: the error in trait prediction and the error in distribution modeling. While scientifically interesting for a "data-scarce" scenario, it does not answer the primary research question as cleanly.

### Traceability
- **Spec Reference**: FR-004
- **Plan Reference**: Trait Imputation Strategy
- **Code Implementation**: `src/modeling/loso_cv.py` (Primary: Known Traits; Optional: Imputed Traits)
- **Report Reference**: `results/stats_report.json` (Primary results), `results/sensitivity_analysis.json` (Imputation comparison if run)

### Conclusion
This document serves as the formal record of the decision to prioritize Spec FR-004 (Known Traits) as the default implementation, treating the Plan's Imputation Strategy as an optional, secondary analysis. This ensures the project remains aligned with its core scientific objectives while maintaining flexibility for exploratory analysis.