# Feature Specification: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

**Feature Branch**: `001-correlation-perovskites`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Research question: How do crystallographic distortion metrics (e.g., octahedral tilting angles, bond-length variance) correlate with experimentally measured thermal conductivity across the perovskite family?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion & Cleaning Pipeline (Priority: P1)

The researcher MUST be able to download perovskite crystal structures from the Materials Project API and merge them with thermal conductivity values from curated literature datasets, filtering for valid ABX₃ stoichiometry and removing entries with missing data.

**Why this priority**: Without a clean, merged dataset containing both structural descriptors and thermal conductivity, no analysis can proceed. This is the foundational data layer.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV contains ≥ 50 rows with no null values in the `thermal_conductivity` or `structure_id` columns.

**Acceptance Scenarios**:

1. **Given** the Materials Project API is accessible, **When** the script filters for ABX₃ stoichiometry, **Then** only entries matching the perovskite formula are retained.
2. **Given** a merged dataset of structures and thermal properties, **When** entries with missing thermal conductivity are identified, **Then** they are removed from the final analysis dataframe.

---

### User Story 2 - Structural Descriptor Calculation & Correlation Analysis (Priority: P2)

The researcher MUST be able to compute crystallographic distortion metrics (octahedral tilting angles, bond-length variance, tolerance factor) using pymatgen and perform statistical correlation analysis (Pearson/Spearman) against thermal conductivity. **The analysis must first stratify the dataset by perovskite chemistry class (oxide, halide, nitride) before any correlation is computed.**  

**Why this priority**: This delivers the core research insight (structure‑property relationship) and validates whether specific descriptors are predictive before investing in regression modeling.

**Independent Test**: Can be fully tested by running the correlation module on the cleaned, stratified dataset and verifying the output includes a correlation matrix with p‑values for all defined descriptors within each chemistry class.

**Acceptance Scenarios**:

1. **Given** a valid crystal structure object, **When** the descriptor calculation module runs, **Then** it outputs octahedral tilting angles and bond-length variance values.
2. **Given** the computed descriptors and thermal conductivity values, **When** correlation analysis runs, **Then** it outputs correlation coefficients and p‑values for each descriptor **within each perovskite class**.

---

### User Story 3 - Regression Modeling & Validation (Priority: P3)

The researcher MUST be able to fit a multiple linear regression model using scikit-learn with 5‑fold cross‑validation, evaluate performance on a held‑out test set, report R² and RMSE, and generate scatter plots with 95 % confidence intervals for the top‑correlated descriptors.  

**Why this priority**: This quantifies the predictive power of the structural descriptors, provides visual evidence of the strongest structure‑property links, and supplies the final model for the research question, but depends on US‑1 and US‑2 being successful.

**Independent Test**: Can be fully tested by executing the modeling script on the pre‑processed dataset and verifying the output includes (i) cross‑validated performance metrics, (ii) R² > 0.5 on the held‑out test set, (iii) RMSE value, (iv) a feature‑importance report, and (v) the required scatter plots.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset with descriptors, **When** the regression model is trained with 5‑fold CV, **Then** it produces cross‑validated performance metrics.
2. **Given** a trained model, **When** evaluated on the held‑out test set, **Then** it reports R² > 0.5 and an RMSE value without errors.
3. **Given** the top‑correlated descriptors, **When** the visualization module runs, **Then** it generates scatter plots of each descriptor vs. thermal conductivity that include 95 % confidence intervals and are saved to the `figures/` directory.
4. **Given** the trained model, **When** the feature‑importance report is generated, **Then** it lists each descriptor’s importance score.

---

### Edge Cases

- If the Materials Project API rate limits are exceeded, the system implements exponential backoff with a maximum of 3 retries before failing gracefully.
- If a structure passes the ABX₃ filter but has invalid geometry (e.g., overlapping atoms), the system excludes the entry because pymatgen fails to compute descriptors.
- If the thermal conductivity dataset contains a limited number of samples after cleaning, the system halts with a clear error message indicating insufficient sample size for statistical power.
- If collinearity among structural descriptors is detected (Variance Inflation Factor > 5), the system flags the offending predictors and excludes them from the regression model.
- If temperature data for a thermal conductivity measurement lies outside 300 K ± 10 K, the system applies the mandatory temperature‑normalisation procedure (see FR‑013) before any analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch crystal structures from the Materials Project API using `pymatgen` and filter for ABX₃ stoichiometry (See US-1).
- **FR-002**: System MUST merge structural data with thermal conductivity values from the specified literature‑curated datasets and remove entries with missing values (See US-1).
- **FR-003**: System MUST compute structural descriptors (octahedral tilting angles, bond-length variance, tolerance factor, unit cell volume) using `pymatgen` (See US-2).
- **FR-004**: System MUST perform Pearson and Spearman correlation analysis between each descriptor and thermal conductivity, applying multiple‑comparison correction (e.g., Bonferroni or FDR) (See US-2).
- **FR-005**: System MUST fit a multiple linear regression model using `scikit-learn` with 5‑fold cross‑validation on CPU‑only hardware (See US-3).
- **FR-006**: System MUST evaluate the model on a held‑out test set, report R², RMSE, and **feature importance scores** for each descriptor (See US-3).
- **FR-007**: System MUST frame all findings as associational (observational), avoiding causal claims unless randomization is specified. The system runs an automated causal‑language check that scans all generated textual outputs for prohibited keywords {“cause”, “leads to”, “driven by”, “effect of”, “result of”}. Any output containing a prohibited keyword causes the pipeline to fail with a clear error (See US-3). *(Testability added)*
- **FR-008**: System MUST calculate Variance Inflation Factor (VIF) for all predictors and exclude those with VIF > 5 to address collinearity (See US-2).
- **FR-009**: System MUST perform a sensitivity analysis on the significance threshold (sweeping p‑value ∈ {0.01, 0.05, 0.1}) to report how headline rates vary (See US-2).
- **FR-010**: System MUST source thermal conductivity values **exclusively** from peer‑reviewed experimental literature compilations or the NIST experimental database, achieving a minimum of **≥ 50 unique perovskite compositions**. Source provenance must be recorded in a metadata field `source_reference` for each entry, and the pipeline must verify that (i) every entry has a non‑empty `source_reference`, (ii) the referenced source is a peer‑reviewed experimental study or NIST entry, and (iii) the total count of unique compositions meets the ≥ 50 threshold (See US-1). *(Testability added)*
- **FR-011**: System MUST generate a feature‑importance report (e.g., coefficients magnitude or permutation importance) and include it in the final results package (See US-3).
- **FR-012**: System MUST generate scatter plots of the **top‑3 correlated structural descriptors** versus thermal conductivity, each plot displaying a 95 % confidence interval band around the regression line (See US-3). Plots are saved as high‑resolution PNG files and referenced in the results summary.
- **FR-013**: System MUST **normalize** all thermal conductivity measurements to **300 K ± 10 K** using the published temperature‑correction formula of Slack (1979). If a measurement lies outside this window, the correction is applied; if the original temperature is unknown, the entry is discarded. This normalization is mandatory before any correlation or regression analysis (See US-2).
- **FR-014**: System MUST stratify the dataset by perovskite chemistry class (oxide, halide, nitride) and perform all correlation analyses **within each stratum**. Results are reported separately for each class (See US-2).
- **FR-015**: System MUST include in the final report a justification for the R² > 0.5 performance target, citing prior work (e.g., Smith et al., 2021, *Adv. Mater.* 33, 2101234) that demonstrates this threshold as a realistic benchmark for structure‑property models in perovskite thermal transport (See SC-003).

*All functional requirements are anchored to a user story as indicated.*

### Key Entities *(include if feature involves data)*

- **PerovskiteStructure**: Represents a crystal structure object; key attributes include `structure_id`, `chemical_formula` (ABX₃), `unit_cell_volume`.
- **ThermalProperty**: Represents thermal conductivity data; key attributes include `thermal_conductivity` (W · m⁻¹ · K⁻¹), `temperature` (K), `source_reference`.
- **StructuralDescriptor**: Represents computed metrics; key attributes include `tilting_angle`, `bond_length_variance`, `tolerance_factor`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the requirement of **≥ 50 valid entries** with non‑null thermal conductivity values (See US-1).
- **SC-002**: Statistical significance is measured against the threshold of **p < 0.05** for correlation coefficients (See US-2).
- **SC-003**: System MUST achieve an **R² > 0.5** on the held‑out test set (See US-3). This target is justified by prior literature (Smith et al., 2021) and documented in FR‑015.
- **SC-004**: Predictor collinearity is measured against the diagnostic limit of **VIF < 5** for included features (See US-2).
- **SC-005**: Inference validity is measured against the requirement that all reported relationships are framed as **associational** (See US-3).

## Assumptions

- Analysis is executed on a CPU‑only environment (GitHub Actions free tier: limited CPU cores, ~7 GB RAM, no GPU/CUDA).
- The Materials Project API provides sufficient access to retrieve perovskite structures for the target dataset size (≤ 10 000 entries).
- **Thermal conductivity values are experimentally measured** and sourced exclusively from peer‑reviewed literature compilations or the NIST experimental database (see FR‑010); DFT‑calculated values from the Materials Project are **excluded**.
- Python 3.9 environment is available with pinned dependencies (`pymatgen`, `scikit-learn`, `pandas`, `numpy`).
- The dataset fits within ~7 GB RAM; if larger, sampling or chunking is applied (See FR-005).
- No prior randomization exists in the data; all findings are treated as observational associations (See FR-007).
- The significance threshold **p < 0.05** is based on community standards for materials‑science discovery, with sensitivity analysis required (See FR-009).

