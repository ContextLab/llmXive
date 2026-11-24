# Feature Specification: Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Feature Branch**: `001-predicting-the-impact-of-alloying-on-mag`  
**Created**: 2026-10-13  
**Status**: Draft  
**Input**: User description: “How do alloying composition and crystal structure determine saturation magnetization in bulk transition‑metal alloys, and which elemental descriptors carry the most predictive signal?”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Train & Evaluate Surrogate Model for Saturation Magnetization (Priority: P1) *(See US-1)*

A materials‑science researcher wants to obtain a predictive model for saturation magnetization from publicly available databases, so that they can assess model performance before using it for virtual screening.

**Why this priority**: This story delivers the core scientific value – a validated, quantitative surrogate that directly answers the research question.

**Independent Test**: Execute the end‑to‑end pipeline on the default public datasets and verify that the generated performance report (R², MAE, RMSE) is produced without manual intervention.

**Acceptance Scenarios**:

1. **Given** the pipeline is invoked with default parameters, **When** it downloads the Materials Project magnetic entries, **Then** a cleaned dataset (`data.csv`) containing **≥ 3 500** alloy records is saved.  
2. **Given** the cleaned dataset, **When** the training stage finishes, **Then** the evaluation stage reports **R² ≥ 0.80** for saturation magnetization on the held‑out test split **and** on an external validation set of **≥ 200** distinct alloys.  
3. **Given** the pipeline runs with default settings on the CI runner, **When** it completes, **Then** total wall‑clock execution time is **≤ 6 hours**.  

### User Story 2 – Inspect Elemental Descriptor Contributions (Priority: P2) *(See US-2)*

A researcher wishes to understand which elemental properties drive the predictions, so they can gain physical insight and guide future alloy design.

**Why this priority**: Interpretable results are essential for scientific acceptance and for informing hypothesis generation.

**Independent Test**: After a successful training run, request the feature‑importance report and verify that the top descriptors are listed with quantitative importance scores.

**Acceptance Scenarios**:

1. **Given** a completed training run, **When** the user runs the “report‑importance” command, **Then** a visual bar chart and a CSV file (`feature_importance.csv`) containing the ranked descriptors are produced, and **at least five** distinct elemental properties (e.g., atomic radius, d‑electron count) appear among the top‑ranked descriptors.

### User Story 3 – Predict Saturation Magnetization for New Candidate Alloys (Priority: P3) *(See US-3)*

A researcher has a novel alloy composition and crystal‑structure prototype and wants an instantaneous prediction of its magnetic performance to decide whether to synthesize it.

**Why this priority**: Enables direct application of the surrogate to accelerate discovery, the ultimate downstream use case.

**Independent Test**: Provide a single composition+structure JSON file to the “predict” CLI; verify that the tool returns a numeric prediction for saturation magnetization within **2 seconds** and that the output conforms to the JSON schema described in FR‑012.

**Acceptance Scenarios**:

1. **Given** a JSON input containing a valid composition string and space‑group/lattice parameters, **When** the prediction script is executed, **Then** it outputs a JSON object with fields `saturation_magnetization` (µ_B/atom) and `confidence_interval` (95 % CI), all within a wall‑clock time **≤ 2 seconds**.

---

### Edge Cases

- **Missing magnetic fields** – When an entry lacks `magnetic_moment`, the system **MUST discard the entry and log a warning**. The overall dataset size after discards must still meet the minimum threshold of **3 500** records, otherwise the pipeline aborts with an informative error.  
- **Duplicate alloy entries** – When multiple DFT calculations exist for the same composition/structure, the system **MUST keep the most recent calculation (based on `last_updated` timestamp)** and remove older duplicates, logging the number of duplicates removed. (See FR‑016)  
- **Extreme compositions** – For alloy formulas with **> 5 constituent elements**, the system **MUST compute elemental averages as usual**; if any constituent element is unknown to the `ElementProperty` featurizer, the entry is excluded and a warning is issued.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** (See US-1): System MUST retrieve all Materials Project entries where `magnetic_moment` is present by downloading the publicly available Materials Project bulk data archive (e.g., the Zenodo release) **without requiring an API key**. *(Curie temperature omitted due to lack of public data; see Assumptions.)*  
- **FR-002** (See US-1): System MUST ingest the Open Quantum Materials Database (OQMD) magnetic CSV release and merge it with the Materials Project data. OQMD entries lack `curie_temperature`; these records are retained for saturation‑magnetization modelling only.  
- **FR-003** (See US-1): System MUST clean the combined dataset by (a) discarding records missing composition strings or crystal‑structure metadata, (b) standardizing formulas with `pymatgen`, and (c) resolving duplicate entries by retaining the most recent calculation.  
- **FR-004** (See US-1): System MUST generate the following feature groups for each alloy (for the saturation‑magnetization target):  
  1. Fractional elemental abundances.  
  2. Element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus (using `matminer.ElementProperty`).  
  3. Crystal‑structure descriptors: space‑group number, lattice parameters (a, b, c, α, β, γ), and packing fraction.  
- **FR-005** (See US-1): System MUST train two regression models for saturation magnetization: a Random Forest Regressor (`n_estimators=300`, `max_depth=20`) and a Gradient Boosting Regressor (`learning_rate=0.05`, `n_estimators=500`).  
- **FR-006** (See US-1): System MUST perform hyper‑parameter tuning with `GridSearchCV` limited to 5‑fold cross‑validation and a total runtime **≤ 30 minutes** for the saturation‑magnetization target.  
- **FR-007** (See US-1): System MUST evaluate each trained model on an 80/20 internal split **and** on an external validation set of **≥ 200** distinct alloys, reporting R², MAE, and RMSE for saturation magnetization.  
- **FR-008** (See US-1): System MUST conduct a paired **Wilcoxon signed‑rank test** comparing residuals of each ensemble model against a linear regression baseline, applying a Bonferroni correction for the two comparisons (α = 0.05/2 = 0.025).  
- **FR-009** (See US-2): System MUST extract and store feature‑importance scores from the best‑performing model (by R²) for saturation magnetization, and produce a visual bar chart and CSV export.  
- **FR-010** (See US-1): System MUST log all random seeds (`np.random.seed(42)`, `random_state=42`) and store artifacts (`data.csv`, `model.pkl`, `metrics.json`, `feature_importance.csv`) as GitHub Actions artifacts.  
- **FR-011** (See US-1): System MUST complete the entire end‑to‑end pipeline within **6 hours** on a typical free‑tier CI runner (≈ 2 GB RAM, ≤ 10 GB SSD).  
- **FR-012** (See US-3): System MUST accept a single‑alloy JSON input and return a JSON response containing `saturation_magnetization` (µ_B/atom) and a `confidence_interval` for that prediction. The prediction call must finish in **≤ 2 seconds** on the CI runner. The response must conform to the following JSON schema:

```json
{
  "type": "object",
  "properties": {
    "saturation_magnetization": {
      "type": "number",
      "description": "Predicted saturation magnetization in µ_B per atom"
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
        }
      },
      "required": ["saturation_magnetization"]
    }
  },
  "required": ["saturation_magnetization", "confidence_interval"],
  "additionalProperties": false
}
```

- **FR-013** (See US-1): System MUST evaluate model generalization on an external hold‑out set of **≥ 200** distinct alloys that were not used during training or internal testing. The acquisition procedure is: (1) download the full Materials Project release **v2026.09**, (2) apply the same cleaning steps as for the training data, (3) filter to entries containing `magnetic_moment`, (4) exclude any alloy present in the internal splits (based on composition + space‑group), (5) randomly sample **200** remaining entries using a fixed random seed = 42; the seed must be logged. The same performance metrics (R², MAE, RMSE) as for the internal test set are reported.  
- **FR-014** (See US-1): System MUST produce a cleaned dataset containing at least **3 500** alloy records for the saturation‑magnetization modelling target after applying all cleaning and filtering steps.  
- **FR-015** (See US-1): When an entry lacks `magnetic_moment`, the system MUST discard the entry and log a warning.  
- **FR-016** (See US-1): When duplicate calculations exist for the same composition and crystal structure, the system MUST keep the most recent calculation (based on `last_updated`) and remove older duplicates, logging the number of duplicates removed.  

### Key Entities

- **AlloyRecord**: Represents a single bulk alloy entry; key attributes include `composition`, `spacegroup`, `lattice_parameters`, `magnetic_moment`, `source` (Materials Project or OQMD).  
- **FeatureVector**: Numerical representation derived from an `AlloyRecord`; includes elemental‑average properties and crystallographic descriptors.  
- **ModelArtifact**: Serialized trained model (`model.pkl`) together with hyper‑parameter metadata and evaluation metrics.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (See US-1): The Random Forest or Gradient Boosting model achieves **R² ≥ 0.80** for saturation magnetization on both the internal test split **and** the external validation set.  
- **SC-002** (See US-1): The paired Wilcoxon signed‑rank test (with Bonferroni correction α = 0.025) shows that the ensemble model’s residuals are significantly lower than those of the linear regression baseline (**p < 0.025** after correction).  
- **SC-003** (See US-2): Feature‑importance analysis identifies at least **five** elemental descriptors whose permutation‑importance scores exceed the mean importance of all descriptors by **≥ 10 %**.  
- **SC-004** (See US-3): A single‑alloy prediction request returns a JSON response conforming to the schema defined in FR‑012 within **≤ 2 seconds** wall‑clock time.  
- **SC-005** (See US-1): The end‑to‑end pipeline execution time on the CI runner is **≤ 6 hours**.  
- **SC-006** (See US-1): The cleaned dataset produced by the pipeline contains **≥ 3 500** records for the saturation‑magnetization target after all cleaning and filtering steps.  

## Assumptions

- **Dataset completeness** – The Materials Project release contains the field `magnetic_moment` for a sufficient number of bulk alloys; OQMD provides additional magnetic moment data but no Curie temperatures, which is acceptable because the scope is limited to saturation magnetization.  
- **Measurement validity** – Magnetic moments derived from DFT calculations in the source databases are assumed to have been validated against experimental benchmarks as reported in the original database publications.  
- **Observational inference** – Because the data are observational (no experimental randomization), all conclusions are framed as **associational** relationships between composition/structure and magnetic properties.  
- **Computational resources** – The free‑tier GitHub Actions runner provides ≤ 2 GB RAM and ≤ 10 GB SSD; hyper‑parameter grids are sized to respect a 30‑minute tuning budget, and the overall pipeline is expected to finish within **6 hours** on typical CI hardware.  
- **External validation availability** – An external set of **≥ 200** distinct alloys with magnetic moment measurements can be sourced from the Materials Project release v2026.09 as described in FR‑013.  
- **Curie temperature data** – No reliable open‑source Curie temperature data for bulk alloys are currently available; consequently the project focuses exclusively on saturation magnetization modeling.  

---  

*End of Specification*