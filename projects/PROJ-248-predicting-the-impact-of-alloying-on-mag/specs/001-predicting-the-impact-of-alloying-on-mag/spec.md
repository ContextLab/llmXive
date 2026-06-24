# Feature Specification: Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Feature Branch**: `[###-feature-name]`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “How do alloying composition and crystal structure determine saturation magnetization and Curie temperature in bulk transition‑metal alloys, and which elemental descriptors carry the most predictive signal?”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Train & Evaluate Surrogate Models (Priority: P1)

A materials‑science researcher wants to obtain predictive models for saturation magnetization and Curie temperature from publicly available databases, so that they can assess model performance before using it for virtual screening.

**Why this priority**: This story delivers the core scientific value – a validated, quantitative surrogate that directly addresses the research question.

**Independent Test**: Execute the end‑to‑end pipeline on the default public datasets and verify that the generated performance report (R², MAE, RMSE) is produced without manual intervention.

**Acceptance Scenarios**:

1. **Given** the pipeline is invoked with default parameters, **When** it downloads the Materials Project and OQMD magnetic entries, **Then** a cleaned dataset (`data.csv`) containing ≥ 3 500 alloy records is saved.  
2. **Given** the cleaned dataset, **When** the training stage finishes, **Then** the evaluation stage reports R² ≥ 0.80 for saturation magnetization and R² ≥ 0.75 for Curie temperature on the held‑out [deferred] test split.

---

### User Story 2 – Inspect Elemental Descriptor Contributions (Priority: P2)

A researcher wishes to understand which elemental properties drive the predictions, so they can gain physical insight and guide future alloy design.

**Why this priority**: Interpretable results are essential for scientific acceptance and for informing hypothesis generation.

**Independent Test**: After a successful training run, request the feature‑importance report and verify that the top‑10 descriptors are listed with quantitative importance scores.

**Acceptance Scenarios**:

1. **Given** a completed training run, **When** the user runs the “report‑importance” command, **Then** a visual bar chart and a CSV file (`feature_importance.csv`) containing the ranked descriptors are produced, and At least five distinct elemental properties (e.g., atomic radius, d‑electron count) appear among the highest‑ranked properties.

---

### User Story 3 – Predict Magnetic Properties for New Candidate Alloys (Priority: P3)

A researcher has a novel alloy composition and crystal‑structure prototype and wants an instantaneous prediction of its magnetic performance to decide whether to synthesize it.

**Why this priority**: Enables direct application of the surrogate to accelerate discovery, the ultimate downstream use case.

**Independent Test**: Provide a single composition+structure JSON file to the “predict” CLI; verify that the tool returns numeric predictions for both targets within 2 seconds.

**Acceptance Scenarios**:

1. **Given** a JSON input containing a valid composition string and space‑group/lattice parameters, **When** the prediction script is executed, **Then** it outputs a saturation‑magnetization value (µ_B/atom) and a Curie‑temperature (K) together with a confidence interval, all within a wall‑clock time ≤ 2 seconds.

---

### Edge Cases

- **Missing magnetic fields** – What happens when an entry lacks `magnetic_moment` or `curie_temperature`?  
  *System MUST discard the entry and log a warning; the overall dataset size must still meet the minimum threshold of 3 000 records, otherwise the pipeline aborts with an informative error.*

- **Duplicate alloy entries** – How does the system resolve multiple DFT calculations for the same composition/structure?  
  *System MUST keep the most recent calculation (based on `last_updated` timestamp) and remove older duplicates, logging the number of duplicates removed.*

- **Extreme compositions** – How are alloy formulas with > 5 constituent elements handled?  
  *System MUST compute elemental averages as usual; if any constituent element is unknown to the `ElementProperty` featurizer, the entry is excluded and a warning is issued.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve all Materials Project entries where `magnetic_type` ≠ `NM` **and** the fields `magnetic_moment` **and** `curie_temperature` are present via the public REST API.  
- **FR-002**: System MUST ingest the Open Quantum Materials Database (OQMD) magnetic CSV release and merge it with the Materials Project data, preserving all columns needed for feature construction.  
- **FR-003**: System MUST clean the combined dataset by (a) discarding records missing composition strings or crystal‑structure metadata, (b) standardizing formulas with `pymatgen`, and (c) resolving duplicate entries by retaining the most recent calculation.  
- **FR-004**: System MUST generate the following feature groups for each alloy:  
  1. Fractional elemental abundances.  
  2. Element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus (using `matminer.ElementProperty`).  
  3. Crystal‑structure descriptors: space‑group number, lattice parameters (a, b, c, α, β, γ), and packing fraction.  
- **FR-005**: System MUST train two regression models per target (saturation magnetization, Curie temperature): a Random Forest Regressor (`n_estimators=300`, `max_depth=20`) and a Gradient Boosting Regressor (`learning_rate=0.05`, `n_estimators=500`).  
- **FR-006**: System MUST perform hyper‑parameter tuning with `GridSearchCV` limited to 5‑fold cross‑validation and a total runtime ≤ 30 minutes per target.  
- **FR-007**: System MUST evaluate each trained model on an 80/20 stratified split, reporting R², MAE, and RMSE for both targets.  
- **FR-008**: System MUST conduct a paired two‑sample t‑test comparing residuals of each ensemble model against a linear regression baseline, applying a Bonferroni correction for the two targets (α = 0.05/2 = 0.025).  
- **FR-009**: System MUST extract and store feature‑importance scores from the best‑performing model (by R²) for each target, and produce a visual bar chart and CSV export.  
- **FR-010**: System MUST log all random seeds (`np.random.seed(42)`, `random_state=42`) and store artifacts (`data.csv`, `model.pkl`, `metrics.json`, `feature_importance.csv`) as GitHub Actions artifacts.  
- **FR-011**: System MUST complete the entire pipeline within a single 6‑hour GitHub Actions job on the free‑tier runner (≤ 2 GB RAM, < 10 GB SSD usage).  

### Key Entities *(include if feature involves data)*

- **AlloyRecord**: Represents a single bulk alloy entry; key attributes include `composition`, `spacegroup`, `lattice_parameters`, `magnetic_moment`, `curie_temperature`, `source` (Materials Project or OQMD).  
- **FeatureVector**: Numerical representation derived from an `AlloyRecord`; includes elemental‑average properties and crystallographic descriptors.  
- **ModelArtifact**: Serialized trained model (`model.pkl`) together with hyper‑parameter metadata and evaluation metrics.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Random Forest or Gradient Boosting model achieves **R² ≥ 0.80** for saturation magnetization on the held‑out test set.  
- **SC-002**: The same ensemble approach achieves **R² ≥ 0.75** for Curie temperature on the held‑out test set.  
- **SC-003**: The paired t‑test (with Bonferroni correction) shows that the ensemble model’s residuals are significantly lower than those of the linear regression baseline (**p < 0.01** after correction).  
- **SC-004**: Feature‑importance analysis identifies at least **five** elemental descriptors whose permutation‑importance scores exceed the mean importance of all descriptors by **≥ 10 %**.  

## Assumptions

- **Dataset completeness** – Both the Materials Project and OQMD releases contain the fields `magnetic_moment`, `curie_temperature`, composition strings, and full crystallographic data. *[NEEDS CLARIFICATION: does the OQMD magnetic CSV include `curie_temperature`?]*  
- **Measurement validity** – Magnetic moments and Curie temperatures derived from DFT calculations in the source databases are assumed to be validated against experimental benchmarks as reported in the original database publications.  
- **Observational inference** – Because the data are observational (no experimental randomization), all conclusions are framed as **associational** relationships between composition/structure and magnetic properties.  
- **Computational resources** – The free‑tier GitHub Actions runner provides ≤ 2 GB RAM and ≤ 10 GB SSD; hyper‑parameter grids are sized to respect a 30‑minute tuning budget.  
- **Descriptor independence** – Elemental averages are potentially collinear; the pipeline will compute variance‑inflation factors (VIF) and report any VIF > 5, but will not claim independent causal effects for highly collinear descriptors.  

---  

*End of Specification*
