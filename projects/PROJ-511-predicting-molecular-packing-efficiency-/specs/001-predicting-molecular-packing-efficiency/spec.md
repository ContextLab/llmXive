# Feature Specification: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Feature Branch**: `PROJ-511-predicting-molecular-packing-efficiency`
**Created**: 2026-06-29
**Status**: Draft
**Input**: User description: “Develop a CPU‑only pipeline that extracts paired SMILES–packing‑coefficient data from the Crystallography Open Database, encodes SMILES with a frozen pre‑trained transformer, trains a lightweight regression model, and quantifies the predictive relationship between molecular topology and crystal packing efficiency.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Build a reproducible SMILES‑packing dataset (Priority: P1)

A researcher wants to obtain a clean dataset of organic crystal structures with corresponding SMILES strings and packing coefficients so that downstream modelling can begin.

**Why this priority**: Without a reliable dataset the entire scientific question cannot be addressed; it is the foundation for all subsequent steps.

**Independent Test**: The pipeline can be run on a fresh CI runner and must output a CSV file containing ≥ 500 rows, each with a valid SMILES string and a numeric packing coefficient.

**Acceptance Scenarios**:

1. **Given** the COD download URL and a filter “organic molecules < 50 atoms”, **when** the download‑and‑parse script is executed, **then** it creates a CSV `dataset.csv` with at least 500 complete records and logs any CIF files that failed parsing.
2. **Given** a CIF file that lacks explicit SMILES metadata, **when** the script invokes RDKit to generate a SMILES from the 3‑D geometry, **then** the generated SMILES is stored and flagged as “generated” in the CSV.

### User Story 2 – Train and evaluate a lightweight predictor (Priority: P2)

A researcher wants to train a small regression model on the dataset and obtain quantitative performance metrics, including statistical significance.

**Why this priority**: Demonstrates whether SMILES‑derived features contain predictive signal; this directly answers the research question.

**Independent Test**: Running the training script on the CSV from US‑1 must produce a model file and a report containing MAE, Pearson r, Spearman ρ, and a permutation‑test p‑value.

**Acceptance Scenarios**:

1. **Given** `dataset.csv` and a frozen SMILES‑transformer, **when** the 2‑layer MLP is trained on an [deferred]/20 % split, **then** the validation report shows MAE ≤ 0.10 (CAPE units), Pearson r ≥ 0.4, Spearman ρ ≥ 0.4, and a two‑sided permutation‑test p‑value ≤ 0.05 (with 10 000 shuffles).
2. **Given** the observed Pearson r, **when** a permutation test with a sufficiently large number of iterations is performed, **then** the report includes a two‑sided p‑value indicating whether the correlation exceeds chance. *(Note: the full 10 000‑shuffle test is also performed and reported for final inference.)*

### User Story 3 – Assess robustness to threshold choices (Priority: P3)

A researcher wants to know whether the conclusions are sensitive to the arbitrary definition of “high packing efficiency”.

**Why this priority**: Guarantees that any claim about predictive strength is not driven by a single, undocumented cutoff.

**Independent Test**: Executing the sensitivity script must sweep the high‑packing threshold over {0.5, 0.6, 0.7} and output a table of correlation and MAE for each, together with a summary of variation.

**Acceptance Scenarios**:

1. **Given** the trained model and validation predictions, **when** the threshold sweep is run, **then** the output shows that Pearson r varies by no more than ±0.05 across the three thresholds and that the permutation‑test p‑values remain below the conventional significance threshold (or above 0.05 for a null result).

---

### Edge Cases

- What happens when a CIF file cannot be parsed (corrupt or missing atomic coordinates)?
- How does the system handle molecules that exceed the 50‑atom filter after SMILES generation?
- What if the calculated packing coefficient is > 1 or < 0 due to anomalous van der Waals volume sums?
- How does the pipeline behave when fewer than 500 valid records are obtained (e.g., after filtering)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download CIF files from the Crystallography Open Database (COD) filtered for organic molecules with ≤ 50 non‑hydrogen atoms, and MUST log download statistics. (See US-1)
- **FR-002**: The system MUST extract or generate a canonical SMILES string for each CIF using RDKit, and MUST record whether the SMILES was extracted or generated. Generation uses only bond‑connectivity information; no target‑related data (e.g., unit‑cell volume) is consulted. (See US-1)
- **FR-003**: The system MUST compute a **raw packing coefficient** for each crystal as

 \[
 \text{PC}_{\text{raw}} = \frac{\text{Unit‑cell volume}}{\sum_{i}{V_{\text{vdW},i}}}
 \]

 where \(V_{\text{vdW},i}\) are atomic van der Waals volumes taken from the standard set of Bondi radii (see FR‑018). This metric is retained **only for diagnostic reporting**; it is **explicitly excluded as a regression target**.
- **FR-004**: The system MUST encode each SMILES into a fixed‑length fingerprint vector using a pre‑trained SMILES‑Transformer (weights frozen) that runs on CPU only **and** MUST augment this representation with 3‑D geometry descriptors (radius of gyration, asphericity, principal moments of inertia) derived from the CIF coordinates. (See US-2)
- **FR-005**: The system MUST train a 2‑layer MLP regression model with ≤ 100 k trainable parameters on the combined fingerprint + 3‑D descriptor vectors to predict the composition‑adjusted packing efficiency (CAPE), using an [deferred]/20 % train/validation split, and MUST store the trained weights. (See US-2)
- **FR-006**: The system MUST evaluate the trained model on the validation set, reporting (a) Mean Absolute Error (MAE), (b) Pearson correlation coefficient r **and** Spearman’s ρ between predicted and observed CAPE, (c) results of a Shapiro‑Wilk normality test on CAPE residuals, and (d) a two‑sided permutation‑test p‑value computed with **10 000** label shuffles. (See US-2)
- **FR-007**: The system MUST perform a sensitivity analysis that sweeps the “high‑packing” threshold over the set {0.5, 0.6, 0.7} and MUST report the resulting r, ρ, MAE, and p‑values for each threshold. The thresholds are justified by the typical range of packing coefficients reported in crystallography literature (≈ 0.5–0.8). (See US-3)
- **FR-008**: The system MUST apply a Bonferroni correction for the three threshold‑specific hypothesis tests and MUST indicate whether any corrected p‑value remains below 0.05. (See US-3)
- **FR-009**: The system MUST compute variance‑inflation‑factor (VIF) diagnostics on **all** predictor variables (fingerprint dimensions, 3‑D descriptors, and recorded confounders) and MUST flag any feature with VIF > 5. (See US-2)
- **FR-010**: The system MUST produce a reproducible HTML report that includes dataset provenance, preprocessing steps, model architecture, all evaluation metrics, and the full source code version hash. Figures and statistics in the report are generated from data validated against `contracts/validation_report.schema.yaml`. (See US-2)
- **FR-011**: The system MUST compute a composition‑adjusted packing efficiency (CAPE) defined as

 \[
 \text{CAPE} = \frac{\text{Packing Coefficient}}{\frac{1}{N_{\text{atoms}}}\sum_{i}{V_{\text{vdW},i}}}
 \]

 where \(N_{\text{atoms}}\) is the number of non‑hydrogen atoms. CAPE normalises for molecular size, allowing geometric effects to be compared across molecules of differing size. Residual compositional signal is modelled explicitly via atom‑type count features, and a partial‑correlation analysis will be reported to demonstrate that predictive performance is not driven solely by composition. (See US-2)
- **FR-012**: The system MUST compute additional 3‑D geometry descriptors (radius of gyration, asphericity, principal moments of inertia) for each molecule and include them in the feature matrix. (See US-2)
- **FR-013**: The system MUST record known confounders for each crystal (crystal lattice system, measurement temperature, presence of solvent molecules) and include them as covariates in VIF diagnostics and model training. (See US-2)
- **FR-014**: The system MUST perform a partial‑correlation analysis between predicted CAPE and observed CAPE while controlling for atom‑type composition features, and report the adjusted correlation coefficient. (See US-2)
- **FR-015**: The system MUST compute Spearman’s rank correlation ρ and conduct a Shapiro‑Wilk test on CAPE residuals to verify assumptions underlying Pearson’s r. (See US-2)
- **FR-016**: The permutation‑test in FR‑006 shall use **10 000** shuffles to achieve a minimum p‑value resolution of 0.0001. (See US-2)
- **FR-017**: The COD dataset source URL (`) and version identifier shall be recorded and verified against the official COD repository to satisfy Constitution Principle II (Verified Accuracy). (See US-1)
- **FR-018**: Atomic van der Waals radii are taken from Bondi, A. (1964) *J. Phys. Chem.*, 68, 441–452, DOI:10.1021/j100785a001, satisfying Constitution Principle II. (See FR‑003)
- **FR-019**: Model checkpoints and validation reports shall conform to the schemas `contracts/model.schema.yaml` and `contracts/validation_report.schema.yaml`, respectively, and references to these contracts shall be included in the documentation. (See FR‑010)

### Key Entities *(include if feature involves data)*

- **Dataset**: CSV file containing `smiles`, `smiles_source` (extracted/generated), `packing_coefficient`, `cape`, `unit_cell_volume`, `radius_of_gyration`, `asphericity`, `principal_moments`, `lattice_system`, `temperature_K`, `has_solvent`.
- **Model**: Serialized MLP weights (`model.pt`) and the frozen transformer checkpoint (`transformer.pt`).
- **Report**: HTML document (`report.html`) summarizing results and diagnostics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The final dataset contains ≥ 500 complete (SMILES, packing coefficient) records with no missing values. (See US-1)
- **SC-002**: The validation Pearson correlation coefficient satisfies r ≥ 0.4 **and** the Bonferroni‑corrected permutation‑test p‑value ≤ 0.05, indicating a statistically significant positive relationship between SMILES‑derived features and CAPE. (See US-2)
- **SC-003**: If r < 0.2, the permutation‑test p‑value is ≥ 0.05, confirming a lack of predictive signal (null result). (See US-2)
- **SC-004**: Across the high‑packing thresholds {0.5, 0.6, 0.7}, the variation in Pearson r is ≤ ±0.05, demonstrating robustness of the predictive signal. (See US-3)
- **SC-005**: The entire end‑to‑end pipeline (download → report) completes in ≤ 6 hours on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM). (See US-2)

## Assumptions

- The COD provides at least 500 organic crystal entries that satisfy the ≤ 50‑atom filter; if fewer are available, the pipeline will issue a warning and abort (research scope limited to N ≈ 500–1000).
- SMILES can be reliably generated from CIF geometry using RDKit; no stereochemistry ambiguities are expected for the filtered set.
- Standard Bondi van der Waals radii are appropriate for calculating atomic volumes; these radii are assumed to be valid for the organic molecules under study (see FR‑018).
- The pre‑trained SMILES transformer model (≈ a few hundred MB) fits within the free‑tier runner’s memory budget and runs in inference‑only mode on CPU.
- No GPU or CUDA libraries are used; all libraries (RDKit, PyTorch‑CPU, scikit‑learn) are compatible with the runner’s environment.
- The permutation test (10 000 shuffles) is computationally tractable on the available CPU resources; if runtime exceeds a predefined time threshold, the number of permutations may be reduced to a lower, computationally feasible quantity (recorded as a deviation).
- Recorded confounder metadata (lattice system, temperature, solvent presence) are available in the COD CIF files for the selected entries.

The COD archive does **not** guarantee that every entry contains a SMILES string. Some CIF records include an optional `_chemical_structure_SMILES` tag when the depositor provides it, but the majority of structures lack this tag. Consequently, the pipeline must be prepared to generate a canonical SMILES from the 3‑D coordinates using RDKit whenever the SMILES field is absent.
