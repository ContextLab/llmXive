# Feature Specification: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Feature Branch**: `PROJ-511-predicting-molecular-packing-efficiency`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description: “Develop a CPU‑only pipeline that extracts paired SMILES–packing‑coefficient data from the Crystallography Open Database, encodes SMILES with a frozen pre‑trained transformer, trains a lightweight regression model, and quantifies the predictive relationship between molecular topology and crystal packing efficiency.”

## Research Question

**Research Question**: How does molecular topology encoded in SMILES representations relate to crystal packing efficiency in organic molecules? (See US‑1)

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Build a reproducible SMILES‑packing dataset (Priority: P1)

A researcher wants to obtain a clean dataset of organic crystal structures with corresponding SMILES strings and packing coefficients so that downstream modelling can begin.

**Why this priority**: Without a reliable dataset the entire scientific question cannot be addressed; it is the foundation for all subsequent steps.

**Independent Test**: The pipeline can be run on a fresh CI runner and must output a CSV file containing ≥ 500 rows, each with a valid SMILES string and a numeric packing coefficient (0 < PC < 1).

**Acceptance Scenarios**:

1. **Given** the COD download URL and a filter “organic molecules < 50 atoms”, **when** the download‑and‑parse script is executed, **then** it creates a CSV `dataset.csv` with at least 500 complete records and logs any CIF files that failed parsing.
2. **Given** a CIF file that lacks explicit SMILES metadata, **when** the script invokes RDKit to generate a SMILES from the 3‑D geometry, **then** the generated SMILES is stored and flagged as “generated” in the CSV.

### User Story 2 – Train and evaluate a lightweight SMILES‑only predictor (Priority: P2)

A researcher wants to train a small regression model on the dataset and obtain quantitative performance metrics, including statistical significance, distinguishing between topology‑only predictions and a null baseline.

**Why this priority**: Demonstrates whether SMILES‑derived features contain predictive signal; this directly answers the research question.

**Independent Test**: Running the training script on the CSV from US‑1 must produce a model file (`model_primary.pt`) and a report containing MAE, Spearman ρ, and a permutation‑test p‑value for the SMILES‑only model.

**Acceptance Scenarios**:

1. **Given** `dataset.csv` and a frozen SMILES‑Transformer, **when** a 2‑layer MLP (≤ 100 k trainable parameters, dropout = 0.1 [2002.02247]) is trained on an 80/20 split, **then** the validation report shows MAE ≤ 0.05 (PC units), Spearman ρ reported, and a two‑sided permutation‑test p‑value ≤ 0.05 (with 10 000 shuffles, fixed seed = 42, parallelized).
2. **Given** the permutation‑test results, **when** the report is generated, **then** it includes the p‑value and notes whether the result is statistically significant at α = 0.05.

## Edge Cases

- What happens when a CIF file cannot be parsed (corrupt or missing atomic coordinates)?
- How does the system handle molecules that exceed the 50‑atom filter after SMILES generation?
- What if the calculated packing coefficient is > 1 or < 0 due to anomalous van der Waals volume sums?
- How does the pipeline behave when fewer than 500 valid records are obtained (e.g., after filtering)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download CIF files from the Crystallography Open Database (COD) filtered for organic molecules with ≤ 50 non‑hydrogen atoms, and MUST log download statistics. (See US‑1)
- **FR-002**: System MUST extract or generate a canonical SMILES string for each CIF using RDKit, and MUST record whether the SMILES was extracted or generated. Generation uses only bond‑connectivity information; no target‑related data (e.g., unit‑cell volume) is consulted. (See US‑1)
- **FR-003**: System MUST compute a **Packing Coefficient (PC)** for each crystal as  
  \[
  \text{PC} = \frac{\sum_{i}{V_{\text{vdW},i}}}{\text{Unit‑cell volume}}
  \]  
  where \(V_{\text{vdW},i}\) are atomic van der Waals volumes taken from the standard Bondi radii (Bondi, 1964, DOI:10.1021/j100785a001). PC is the regression target. (See US‑2)
- **FR-004**: System MUST encode each SMILES into a fixed‑length fingerprint vector using a pre‑trained SMILES‑Transformer (weights frozen) that runs on CPU only. (See US‑2)
- **FR-005**: System MUST train a single 2‑layer MLP regression model (≤ 100 k trainable parameters, dropout = 0.1 [2002.02247]) on the SMILES fingerprints to predict PC. The train/validation split is 80/20. (See US‑2)
- **FR-006**: System MUST evaluate the model on the validation set, reporting (a) Mean Absolute Error (MAE), (b) Spearman’s ρ, (c) results of a two‑sided permutation‑test p‑value computed with **10 000** shuffles, fixed random seed = 42, parallelized. Pearson’s r is reported only if the Shapiro‑Wilk test indicates normally distributed residuals. (See US‑2)
- **FR-007**: System MUST perform a Shapiro‑Wilk normality test on residuals and report the statistic and p‑value. (See US‑2)
- **FR-008**: System MUST produce a reproducible HTML report that includes dataset provenance, preprocessing steps, model architecture, all evaluation metrics, and the full source‑code version hash. Figures and statistics in the report are generated from data validated against `contracts/validation_report.schema.yaml`. (See US‑2)
- **FR-009**: System MUST record known confounders for each crystal (crystal lattice system, measurement temperature, presence of solvent molecules) and include them as covariates in any diagnostic analyses when available. (See US‑2)
- **FR-010**: System MUST compute the Packing Coefficient (PC) as defined in FR‑003. PC is the target variable. (See US‑2)
- **FR-011**: The COD dataset source URL (`) and exact version identifier shall be recorded and verified against the official COD repository. System MUST write a `source_verification.json` file containing the URL, version tag, and a SHA‑256 hash of the downloaded dataset, satisfying Constitution Principle II. (See US‑1)
- **FR-012**: Model checkpoints and validation reports shall conform to the schemas `contracts/model.schema.yaml` and `contracts/validation_report.schema.yaml` located in the repository. (See FR‑008)
- **FR-013**: System MUST enforce Success Criterion SC‑003 during evaluation, automatically checking that if Spearman ρ < 0.2 then the permutation‑test p‑value ≥ 0.05, and logging the outcome. (See US‑2)

### Key Entities *(include if feature involves data)*

- **Dataset**: CSV file containing `smiles`, `smiles_source` (extracted/generated), `packing_coefficient`, `unit_cell_volume`, `lattice_system`, `temperature_K`, `has_solvent`.
- **Model**: Serialized MLP weights (`model_primary.pt`) and the frozen transformer checkpoint (`transformer.pt`).
- **Report**: HTML document (`report.html`) summarizing results and diagnostics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The final dataset contains ≥ 500 complete (SMILES, packing coefficient) records with no missing values. (See US‑1)
- **SC-002**: The Primary Model validation report includes Spearman ρ and a permutation‑test p‑value ≤ 0.05, indicating statistical significance at the conventional α = 0.05 level. (See US‑2, FR‑006)
- **SC-003**: If Spearman ρ < 0.2, the permutation‑test p‑value is ≥ 0.05, confirming a null result. (See US‑2, FR‑013)
- **SC-005**: The entire end‑to‑end pipeline (download → report) completes in ≤ 6 hours on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM). This runtime bound ensures reproducibility within typical CI resource limits. (See US‑2)

## Assumptions

- The COD provides at least 500 organic crystal entries that satisfy the ≤ 50‑atom filter; if fewer are available, the pipeline will issue a warning and abort (research scope limited to N ≈ 500–1000).
- SMILES can be reliably generated from CIF geometry using RDKit; no stereochemistry ambiguities are expected for the filtered set.
- Standard Bondi van der Waals radii are appropriate for calculating atomic volumes; these radii are assumed to be valid for the organic molecules under study (see FR‑011).
- The pre‑trained SMILES transformer model (≈ a few hundred MB) fits within the free‑tier runner’s memory budget and runs in inference‑only mode on CPU. (See US‑1)
- No GPU or CUDA libraries are used; all libraries (RDKit, PyTorch‑CPU, scikit‑learn) are compatible with the runner’s environment.
- The permutation test (10 000 shuffles) is computationally tractable on the available CPU resources with parallelization; the implementation will complete within the overall 6‑hour pipeline budget.
- Recorded confounder metadata (crystal lattice system, temperature, solvent presence) are available in the COD CIF files for the selected entries.
