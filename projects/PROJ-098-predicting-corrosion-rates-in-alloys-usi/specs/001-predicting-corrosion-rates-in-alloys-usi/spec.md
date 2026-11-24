# Feature Specification: Predicting Corrosion Rates in Alloys Using Machine Learning on Public Datasets

**Feature Branch**: `001-predicting-corrosion-rates-in-alloys-usi`
**Created**: 2026-06-26
**Status**: Draft
**Input**: User description: "Predicting Corrosion Rates in Alloys Using Machine Learning on Public Datasets — identify compositional and environmental features determining corrosion rates, and quantify alloy-environment interactions, using interpretable CPU-only ML on public datasets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compile and characterize a unified public corrosion dataset (Priority: P1)

A materials scientist obtains a single cleaned, documented tabular dataset that merges public corrosion records containing alloy composition (elemental wt%), environmental parameters (pH, temperature, chloride concentration), measured corrosion rate (mm/year), and the metadata of each source record (electrolyte description, exposure/test method, alloy family, data source). The scientist can inspect per-record provenance and measurement-condition metadata to judge comparability across sources.

**Why this priority**: All downstream modeling, validation, and interpretation depend on a coherent, documented dataset. Without it, no research question can be answered.

**Independent Test**: Can be fully tested by running the data pipeline on the selected public sources and verifying row counts, per-variable availability, missingness rates, and provenance completeness against the documented data dictionary.

**Acceptance Scenarios**:

1. **Given** the selected public corrosion data sources, **When** the acquisition and cleaning pipeline runs, **Then** a single merged table is produced where every row carries composition (wt% for ≥3 named elements including Cr, Ni, or Fe as available), environment (pH, temperature, chloride), corrosion rate (mm/year), and a provenance field identifying source and test conditions.
2. **Given** rows with missing values in any required variable, **When** imputation runs, **Then** the imputation method (iterative imputation) and per-variable missingness rates are recorded in the data documentation.
3. **Given** heterogeneous source datasets, **When** units and variable definitions are harmonized, **Then** any record whose measurement conditions (electrolyte, exposure method) are undocumented is flagged as such rather than silently merged.

---

### User Story 2 - Train and validate interpretable corrosion-rate models (Priority: P2)

A corrosion engineer trains Random Forest and Gradient Boosting regressors on the unified dataset with CPU-only scikit-learn, evaluates them via 5-fold cross-validation plus a held-out [deferred] test set, and receives a comparison of the two model families including a paired statistical test across folds.

**Why this priority**: This delivers the predictive benchmark and generalization estimate that answers whether composition + environment predict corrosion rate.

**Independent Test**: Can be tested by running the training script and checking that cross-validation metrics, test-set metrics, and the paired fold-wise model comparison are all produced and reported.

**Acceptance Scenarios**:

1. **Given** the unified dataset with ≥100 usable rows, **When** model training runs, **Then** 5-fold cross-validation RMSE/R² for both model families and final held-out test-set metrics ([deferred] of data) are reported.
2. **Given** fold-wise RMSE values for both models, **When** the paired t-test is applied, **Then** the test statistic, p-value, and multiple-comparison correction across the family of hypothesis tests in the study are reported.
3. **Given** the 6-hour single-job compute budget, **When** hyperparameter search runs, **Then** the grid contains ≤50 combinations per model family and total training completes within the budget.

---

### User Story 3 - Quantify feature importance and alloy-environment interaction effects (Priority: P3)

A researcher obtains SHAP-based feature importance rankings and an explicit statistical comparison of models with versus without engineered interaction features (e.g., Cr×pH, Ni×temperature, Cr:Cl ratio), with physical plausibility discussion against known mechanisms such as Cr passivation.

**Why this priority**: This is the interpretive payoff of the study — identifying which features and interactions modulate corrosion resistance — and builds on US-1 and US-2.

**Independent Test**: Can be tested by running the analysis script and verifying the importance ranking table, the interaction-versus-main-effects model comparison, and the plausibility narrative are all produced.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** SHAP analysis runs, **Then** a ranked feature-importance table is produced covering all input features.
2. **Given** models trained with and without interaction features, **When** fold-wise performance is compared, **Then** the paired test of whether interactions improve predictive accuracy (with correction for multiple tests) is reported, framed associationally.
3. **Given** the top-ranked features, **When** the plausibility analysis is written, **Then** each top feature's direction of effect is discussed relative to documented corrosion mechanisms, and any implausible or unexpected ranking is explicitly flagged.

### Edge Cases

- **Missing or partially documented measurement conditions**: A source record lacks electrolyte or exposure-method metadata. The pipeline must flag it and report how many such records exist; the analysis must report results both with and without these records if they exceed 10% of the dataset.
- **A public dataset lacks a required variable** (e.g., no chloride concentration): the dataset must be excluded or the variable gap recorded; the spec must not assume availability — see NEEDS CLARIFICATION below.
- **Small effective dataset after cleaning** (<100 usable rows): the pipeline must report the count and switch to repeated cross-validation with an explicit acknowledgment of limited power rather than silently proceeding.
- **Highly skewed corrosion-rate distributions** (common in corrosion data): the pipeline must report distribution diagnostics and apply a documented transform (e.g., log) with sensitivity of conclusions to the transform choice.
- **Near-collinear engineered features** (e.g., Cr:Cl ratio vs. Cr and Cl main effects): a collinearity diagnostic must be reported and importance rankings for collinear features must be interpreted jointly, not as independent effects.
- **Model comparison is inconclusive** (no significant difference between model families or interaction benefit): the null result must be reported as a valid, informative outcome with power considerations stated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST acquire corrosion records from public repositories (Zenodo, HuggingFace Datasets, or GitHub) and produce a single merged dataset in which every row contains alloy composition in elemental wt%, environmental parameters (pH, temperature, chloride concentration), corrosion rate in mm/year, and provenance metadata including source dataset, electrolyte description, and test/exposure method where recorded. (See US-1)
- **FR-002**: The system MUST document, in a data dictionary, per-variable definitions, units, missingness rates, and the count and share of records with undocumented measurement conditions; records missing measurement-condition metadata must be flagged, not silently dropped. (See US-1)
- **FR-003**: The system MUST clean missing values via iterative imputation and normalize continuous environmental features, with the imputation and normalization choices recorded in the run documentation. (See US-1)
- **FR-004**: The system MUST encode alloy compositions as elemental weight percentages and generate interaction terms between key alloying elements (Cr, Ni, Fe) and environmental factors (pH, temperature), including at least the Cr:Cl derived ratio. (See US-1, US-3)
- **FR-005**: The system MUST train Random Forest and Gradient Boosting regressors using scikit-learn on CPU only, in default precision, with hyperparameter grids of ≤50 combinations per model family, completing the full analysis within one 6-hour job on a 2-core, ~7 GB RAM, ~14 GB disk runner with no GPU. (See US-2)
- **FR-006**: The system MUST evaluate models via 5-fold cross-validation and a held-out test set of [deferred] of the data, reporting RMSE and R² for both, with the test set used only for final reporting. (See US-2)
- **FR-007**: The system MUST compare the two model families with a paired t-test across folds and MUST apply a stated multiple-comparison correction (e.g., Holm–Bonferroni) across all hypothesis tests reported in the study, using α = 0.05 as the per-test significance level. (See US-2, US-3)
- **FR-008**: The system MUST run a sensitivity analysis over the significance threshold, reporting for α ∈ {0.01, 0.05, 0.10} which conclusions (model-family difference; interaction benefit) hold at each level, so that headline claims are not artifacts of the 0.05 cutoff. (See US-2, US-3)
- **FR-009**: The system MUST compute SHAP-based feature importance rankings for the best-performing model and report a collinearity diagnostic (e.g., variance inflation factors or feature-correlation matrix) for engineered interaction features. (See US-3)
- **FR-010**: The system MUST compare models with versus without interaction features via fold-wise paired testing, and MUST frame all findings associationally — no causal claims about alloying elements or environment, since the design is observational with no randomization. (See US-3)
- **FR-011**: The system MUST report a power/sample-size consideration: either an a-priori power statement for the paired fold-wise tests or an explicit acknowledgment of limited power if the usable dataset is small (deferred until the dataset size is known). (See US-2)
- **FR-012**: The system MUST package all data-processing scripts, model code, results tables/figures, and a requirements.txt specifying a CPU-only Python environment, so the full analysis reruns end-to-end within the 6-hour budget on a free-tier GitHub Actions runner. (See US-1, US-2, US-3)
- **FR-013**: The system MUST report results for both a model on main effects only and a model including interactions, with the variance explained by the top 2–4 features reported descriptively; a failure to reach the expected >60% variance-explained target must be reported as a valid negative result, not treated as project failure. (See US-3)
- **FR-014**: The system MUST record whether each source dataset's corrosion rates were measured under comparable conditions (electrolyte, exposure duration, test method) and, where conditions differ substantially, report a subgroup or condition-stratified analysis. (See US-1, US-3)

### Key Entities

- **Corrosion record**: one alloy-environment-measurement observation; attributes: elemental composition (wt%), pH, temperature, chloride concentration, corrosion rate (mm/year), provenance (source, electrolyte, test method, alloy family).
- **Feature set**: main-effect features (composition, environment) plus engineered interaction features (element×environment products, Cr:Cl ratio).
- **Model evaluation**: fold-wise and held-out metrics per model family and feature set; paired test statistics with multiplicity correction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values to the research phase.

- **SC-001**: Dataset completeness is measured as the share of rows in the merged dataset carrying all required variables (composition, pH, temperature, chloride, corrosion rate) plus provenance metadata, referenced against the data dictionary. (See US-1)
- **SC-002**: Generalization performance is measured as held-out test-set RMSE and R² for each model family, referenced against 5-fold cross-validation estimates to check for overfitting. (See US-2)
- **SC-003**: Model-family and interaction-effect conclusions are measured as paired fold-wise test p-values with multiplicity correction, referenced against the α sensitivity sweep in FR-008 to confirm robustness across α ∈ {0.01, 0.05, 0.10}. (See US-2, US-3)
- **SC-004**: Interpretability deliverable completeness is measured as the presence of a ranked SHAP importance table, a collinearity diagnostic, and a physical-plausibility discussion for every top-ranked feature, referenced against the analysis output checklist. (See US-3)
- **SC-005**: Reproducibility is measured as a single documented command sequence that reruns the full analysis end-to-end on a 2-core CPU-only runner within ≤6 hours and ≤7 GB RAM, referenced against the recorded run log. (See US-2)
- **SC-006**: Measurement-condition transparency is measured as the reported count and share of records with documented electrolyte and test method, referenced against FR-014's stratified analysis requirement. (See US-1)

## Assumptions

- Public corrosion datasets containing all required variables (elemental composition in wt%, pH, temperature, chloride concentration, and corrosion rate in mm/year) exist and are accessible from Zenodo, HuggingFace Datasets, or GitHub without authentication. [NEEDS CLARIFICATION: which specific public dataset(s) contain chloride concentration AND corrosion rate AND full composition? Most public corrosion tables omit at least one of these — the data-acquisition step must confirm variable availability before modeling commitments are finalized.]
- The study is observational: alloy compositions and environments are not randomly assigned, so all reported relationships are associational; no causal or moderation-effect claims will be made.
- The expected >60% variance-explained target from the idea is a hypothesis to be tested, not a completion criterion; null or negative results are valid outcomes.
- α = 0.05 is chosen as the conventional per-test significance level; because it is a convention rather than a domain-derived threshold, FR-008 requires the α-sensitivity sweep so conclusions are reported across {0.01, 0.05, 0.10}.
- The [deferred] held-out test split and 5-fold CV follow the idea's methodology sketch; if the usable dataset falls below 100 rows, repeated cross-validation replaces the single split and the power limitation is stated explicitly.
- Corrosion-rate distributions are assumed potentially right-skewed; a log transform is the default with sensitivity of conclusions to the transform reported.
- All compute runs on free-tier GitHub Actions CPU runners (2 cores, ~7 GB RAM, ~14 GB disk, ≤6 h, no GPU); scikit-learn tree ensembles and SHAP on a modest tabular dataset fit these limits. No deep learning, no large-model inference, no GPU-dependent methods.
- SHAP values are computed with a CPU-tractable explainer (e.g., TreeExplainer) on the trained ensembles; if dataset size makes exact Shapley computation prohibitive, a sampled-background approximation is used and documented.
- The full dataset (after merging and cleaning) is assumed to fit within ~7 GB RAM and ~14 GB disk; if larger, it is subsetted with the subsetting rule documented.
- Paper-stage handoff: manuscript formatting, PDF compilation, and publication are owned by the subsequent paper pipeline; this research stage's deliverables are the analysis, validation, measured tables/figures, and evidence summary, and none of the paper-stage deliverables are prerequisites for research completion.

## References

- Orbital Graph Convolutional Neural Network for Material Property Prediction (2020). Mohammadreza Karamad, Rishikesh Magar, Yuting Shi, Samira Siahrostami, Ian D. Gates, et al.. arXiv. [2008.06415](https://arxiv.org/abs/2008.06415)
- Influence of Heat Treatment on the Corrosion Behavior of Purified Magnesium and AZ31 Alloy (2017). Sohrab Khalifeh, T. David Burleigh. arXiv. [1706.08663](https://arxiv.org/abs/1706.08663)
