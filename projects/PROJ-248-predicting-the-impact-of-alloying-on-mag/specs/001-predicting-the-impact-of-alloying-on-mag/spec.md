# Feature Specification: Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Feature Branch**: `[###-feature-name]`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “How do alloying composition and crystal structure determine saturation magnetization and Curie temperature in bulk transition‑metal alloys, and which elemental descriptors carry the most predictive signal?”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Train & Evaluate Surrogate Models (Priority: P1)

A materials‑science researcher wants to obtain predictive models for saturation magnetization and Curie temperature from publicly available databases, so that they can assess model performance before using it for virtual screening.

**Why this priority**: This story delivers the core scientific value – a validated, quantitative surrogate that directly addresses the research question.

**Independent Test**: Execute the end‑to‑end pipeline on the default public datasets and verify that the generated performance report (R², MAE, RMSE) is produced without manual intervention.

**Acceptance Scenarios**:

1. **Given** the pipeline is invoked with default parameters, **When** it downloads the Materials Project and OQMD magnetic entries, **Then** a cleaned dataset (`data.csv`) containing **≥ 3 500** alloy records is saved.  
2. **Given** the cleaned dataset, **When** the training stage finishes, **Then** the evaluation stage reports **R² ≥ 0.80** for saturation magnetization and **R² ≥ 0.75** for Curie temperature on the held‑out test split **and** on an external validation set of ≥ 200 distinct alloys.  
3. **Given** the pipeline runs with default settings on the CI runner, **When** it completes, **Then** total wall‑clock execution time is **≤ 6 hours**.

---

### User Story 2 – Inspect Elemental Descriptor Contributions (Priority: P2)

A researcher wishes to understand which elemental properties drive the predictions, so they can gain physical insight and guide future alloy design.

**Why this priority**: Interpretable results are essential for scientific acceptance and for informing hypothesis generation.

**Independent Test**: After a successful training run, request the feature‑importance report and verify that the top‑10 descriptors are listed with quantitative importance scores.

**Acceptance Scenarios**:

1. **Given** a completed training run, **When** the user runs the “report‑importance” command, **Then** a visual bar chart and a CSV file (`feature_importance.csv`) containing the ranked descriptors are produced, and **at least five** distinct elemental properties (e.g., atomic radius, d‑electron count) appear among the highest‑ranked properties.

---

### User Story 3 – Predict Magnetic Properties for New Candidate Alloys (Priority: P3)

A researcher has a novel alloy composition and crystal‑structure prototype and wants an instantaneous prediction of its magnetic performance to decide whether to synthesize it.

**Why this priority**: Enables direct application of the surrogate to accelerate discovery, the ultimate downstream use case.

**Independent Test**: Provide a single composition+structure JSON file to the “predict” CLI; verify that the tool returns numeric predictions for both targets **within 2 seconds** and that the output conforms to the JSON schema described in FR‑012.

**Acceptance Scenarios**:

1. **Given** a JSON input containing a valid composition string and space‑group/lattice parameters, **When** the prediction script is executed, **Then** it outputs a JSON object with fields `saturation_magnetization` (µ_B/atom), `curie_temperature` (K), and `confidence_interval` ([deferred] CI for each), all within a wall‑clock time **≤ 2 seconds**.

---

### Edge Cases

- **Missing magnetic fields** – What happens when an entry lacks `magnetic_moment` or `curie_temperature`?  
  *System MUST discard the entry and log a warning; the overall dataset size must still meet the minimum threshold of **3 500** records, otherwise the pipeline aborts with an informative error.*

- **Duplicate alloy entries** – How does the system resolve multiple DFT calculations for the same composition/structure?  
  *System MUST keep the most recent calculation (based on `last_updated` timestamp) and remove older duplicates, logging the number of duplicates removed.*

- **Extreme compositions** – How are alloy formulas with > 5 constituent elements handled?  
  *System MUST compute elemental averages as usual; if any constituent element is unknown to the `ElementProperty` featurizer, the entry is excluded and a warning is issued.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve all Materials Project entries where `magnetic_type` ≠ `NM` **and** the fields `magnetic_moment` **and** `curie_temperature` are present via the public REST API.  
- **FR-002**: System MUST ingest the Open Quantum Materials Database (OQMD) magnetic CSV release and merge it with the Materials Project data. OQMD entries lack `curie_temperature`; these records are retained for saturation‑magnetization modelling but are excluded from any Curie‑temperature modelling or evaluation.  
- **FR-003**: System MUST clean the combined dataset by (a) discarding records missing composition strings or crystal‑structure metadata, (b) standardizing formulas with `pymatgen`, and (c) resolving duplicate entries by retaining the most recent calculation.  
- **FR-004**: System MUST generate the following feature groups for each alloy:  
  1. Fractional elemental abundances.  
  2. Element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus (using `matminer.ElementProperty`).  
  3. Crystal‑structure descriptors: space‑group number, lattice parameters (a, b, c, α, β, γ), and packing fraction.  
- **FR-005**: System MUST train two regression models per target (saturation magnetization, Curie temperature): a Random Forest Regressor (`n_estimators=300`, `max_depth=20`) and a Gradient Boosting Regressor (`learning_rate=0.05`, `n_estimators=500`).  
- **FR-006**: System MUST perform hyper‑parameter tuning with `GridSearchCV` limited to 5‑fold cross‑validation and a total runtime ≤ 30 minutes per target.  
- **FR-007**: System MUST evaluate each trained model on an 80/20 stratified internal split **and** on an external validation set of ≥ 200 distinct alloys, reporting R², MAE, and RMSE for both targets.  
- **FR-008**: System MUST conduct a paired two‑sample **Student’s t‑test** (two‑tailed) comparing residuals of each ensemble model against a linear regression baseline, applying a Bonferroni correction for the four comparisons (α = 0.05/4 = 0.0125).  
- **FR-009**: System MUST extract and store feature‑importance scores from the best‑performing model (by R²) for each target, and produce a visual bar chart and CSV export.  
- **FR-010**: System MUST log all random seeds (`np.random.seed(42)`, `random_state=42`) and store artifacts (`data.csv`, `model.pkl`, `metrics.json`, `feature_importance.csv`) as GitHub Actions artifacts.  
- **FR-011**: System MUST complete the entire end‑to‑end pipeline within **6 hours** on a typical CI runner (≈ 2 GB RAM, < 10 GB SSD). This runtime target is reflected in Success Criterion SC‑006.  
- **FR-012**: System MUST accept a single‑alloy JSON input and return a JSON response containing `saturation_magnetization` (µ_B/atom), `curie_temperature` (K), and a confidence interval for each. The prediction call must finish in **≤ 2 seconds** on the CI runner. The response must conform to the following JSON schema:

```json
{
  "type": "object",
  "properties": {
    "saturation_magnetization": {
      "type": "number",
      "description": "Predicted saturation magnetization in µ_B per atom"
    },
    "curie_temperature": {
      "type": "number",
      "description": "Predicted Curie temperature in Kelvin"
    },
    "confidence_interval": {
      "type": "object",
      "properties": {
        "saturation_magnetization": {
          "type": "array",
          "items": { "type": "number" },
          "minItems": 2,
          "maxItems": 2,
          "description": "[lower, upper] 95 % CI for saturation magnetization"
        },
        "curie_temperature": {
          "type": "array",
          "items": { "type": "number" },
          "minItems": 2,
          "maxItems": 2,
          "description": "[lower, upper] 95 % CI for Curie temperature"
        }
      },
      "required": ["saturation_magnetization", "curie_temperature"]
    }
  },
  "required": ["saturation_magnetization", "curie_temperature", "confidence_interval"],
  "additionalProperties": false
}
```

- **FR-013**: System MUST evaluate model generalization on an external hold‑out set of **≥ 200 distinct alloys** that were not used during training or internal testing. This set will be sourced from the Materials Project release **v2026.09** (DOI: 10.17188/xxxx). The acquisition procedure is: (1) download the full MP dataset for the specified release; (2) apply the same cleaning steps as for the training data; (3) filter to entries that contain both `magnetic_moment` and `curie_temperature`; (4) exclude any alloy present in the internal training or test splits (based on composition + space‑group); (5) randomly sample at least 200 remaining entries. The same performance metrics (R², MAE, RMSE) as for the internal test set are reported.  
- **FR-014**: System MUST log all random seeds (`np.random.seed(42)`, `random_state=42`) and store artifacts (`data.csv`, `model.pkl`, `metrics.json`, `feature_importance.csv`) as GitHub Actions artifacts.  
- **FR-015**: System MUST complete the entire end‑to‑end pipeline within **6 hours** on a typical CI runner (≈ 2 GB RAM, < 10 GB SSD). This runtime requirement is linked to Success Criterion SC‑006.  

### Key Entities *(include if feature involves data)*

- **AlloyRecord**: Represents a single bulk alloy entry; key attributes include `composition`, `spacegroup`, `lattice_parameters`, `magnetic_moment`, `curie_temperature`, `source` (Materials Project or OQMD).  
- **FeatureVector**: Numerical representation derived from an `AlloyRecord`; includes elemental‑average properties and crystallographic descriptors.  
- **ModelArtifact**: Serialized trained model (`model.pkl`) together with hyper‑parameter metadata and evaluation metrics.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Random Forest or Gradient Boosting model achieves **R² ≥ 0.80** for saturation magnetization on both the internal test split **and** the external validation set.  
- **SC-002**: The same ensemble approach achieves **R² ≥ 0.75** for Curie temperature on both the internal test split **and** the external validation set.  
- **SC-003**: The paired two‑sample t‑test (with Bonferroni correction α = 0.0125) shows that the ensemble model’s residuals are significantly lower than those of the linear regression baseline (**p < 0.0125** after correction).  
- **SC-004**: Feature‑importance analysis identifies at least **five** elemental descriptors whose permutation‑importance scores exceed the mean importance of all descriptors by **≥ 10 %**.  
- **SC-005**: A single‑alloy prediction request returns a JSON response conforming to the schema defined in FR‑012 within **≤ 2 seconds** wall‑clock time.  
- **SC-006**: The end‑to‑end pipeline execution time on the CI runner is **≤ 6 hours**.

## Assumptions

- **Dataset completeness** – Both the Materials Project and OQMD releases contain the fields `magnetic_moment`, composition strings, and full crystallographic data. *The OQMD magnetic CSV does **not** include a `curie_temperature` column; it provides magnetic moment (`magmom`) and magnetic ordering information but lacks Curie temperature data.*  
- **Measurement validity** – Magnetic moments and Curie temperatures derived from DFT calculations in the source databases are assumed to be validated against experimental benchmarks as reported in the original database publications.  
- **Observational inference** – Because the data are observational (no experimental randomization), all conclusions are framed as **associational** relationships between composition/structure and magnetic properties.  
- **Computational resources** – The free‑tier GitHub Actions runner provides ≤ 2 GB RAM and ≤ 10 GB SSD; hyper‑parameter grids are sized to respect a 30‑minute tuning budget, and the overall pipeline is expected to finish within **6 hours** on typical CI hardware.  
- **Descriptor independence** – Elemental averages are potentially collinear; the pipeline will compute variance‑inflation factors (VIF) and report any VIF > 5, but will not claim independent causal effects for highly collinear descriptors.  
- **External validation availability** – An external set of ≥ 200 distinct alloys with both magnetic moment and Curie temperature measurements can be sourced from the Materials Project release v2026.09 (DOI: 10.17188/xxxx) as described in FR‑013.  

---  

*End of Specification*
