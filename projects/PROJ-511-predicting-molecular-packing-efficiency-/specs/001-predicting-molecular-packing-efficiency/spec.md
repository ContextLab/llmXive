# Feature Specification: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Feature Branch**: `PROJ-511-predicting-molecular-packing-efficiency`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description: “Develop a CPU‑only pipeline that extracts paired SMILES–packing‑coefficient data from the Crystallography Open Database, encodes SMILES with a frozen pre‑trained transformer, trains a lightweight regression model, and quantifies the predictive relationship between molecular topology and crystal packing efficiency.”

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 – Build a reproducible SMILES‑packing dataset (Priority: P1)

A researcher wants to obtain a clean dataset of organic crystal structures with corresponding SMILES strings and packing coefficients so that downstream modelling can begin.

**Why this priority**: Without a reliable dataset the entire scientific question cannot be addressed; it is the foundation for all subsequent steps.

**Independent Test**: The pipeline can be run on a fresh CI runner and must output a CSV file containing ≥ 500 rows, each with a valid SMILES string and a numeric packing coefficient (0 < PC < 1).

**Acceptance Scenarios**:

1. **Given** the COD download URL and a filter “organic molecules < 50 atoms”, **when** the download‑and‑parse script is executed, **then** it creates a CSV `dataset.csv` with at least 500 complete records and logs any CIF files that failed parsing.
2. **Given** a CIF file that lacks explicit SMILES metadata, **when** the script invokes RDKit to generate a SMILES from the 3‑D geometry, **then** the generated SMILES is stored and flagged as “generated” in the CSV.

### User Story 2 – Train and evaluate a lightweight predictor (Priority: P2)

A researcher wants to train a small regression model on the dataset and obtain quantitative performance metrics, including statistical significance, distinguishing between topology-only and geometry-assisted predictions.

**Why this priority**: Demonstrates whether SMILES‑derived features contain predictive signal; this directly answers the research question.

**Independent Test**: Running the training script on the CSV from US‑1 must produce two model files (SMILES-only and Full) and a report containing MAE, Spearman ρ, and a permutation‑test p‑value for the SMILES-only model.

**Acceptance Scenarios**:

1. **Given** `dataset.csv` and a frozen SMILES‑transformer, **when** the 2‑layer MLP is trained on an 80/20 split, **then** the SMILES-only validation report shows MAE ≤ 0.05 (PC units), Spearman ρ ≥ 0.3, and a two‑sided permutation‑test p‑value ≤ 0.05 (with 10 000 shuffles, parallelized).
2. **Given** the observed Spearman ρ, **when** a permutation test with 10 000 shuffles is performed (with a 4-hour timeout), **then** the report includes a two‑sided p‑value indicating whether the correlation exceeds chance. If the timeout is reached, the deviation is logged and the achieved p-value resolution is reported.

### User Story 3 – Assess robustness to threshold choices (Priority: P3)

A researcher wants to know whether the conclusions are sensitive to the arbitrary definition of “high packing efficiency”.

**Why this priority**: Guarantees that any claim about predictive strength is not driven by a single, undocumented cutoff.

**Independent Test**: Executing the sensitivity script must sweep the high‑packing threshold over {0.5, 0.6, 0.7} and output a table of correlation and MAE for each, together with a summary of variation.

**Acceptance Scenarios**:

1. **Given** the trained SMILES-only model and validation predictions, **when** the threshold sweep is run, **then** the output shows that Spearman ρ varies by no more than ±0.05 across the three thresholds and that the permutation‑test p‑values remain below the conventional significance threshold (or above 0.05 for a null result).

---

### Edge Cases

- What happens when a CIF file cannot be parsed (corrupt or missing atomic coordinates)?
- How does the system handle molecules that exceed the 50‑atom filter after SMILES generation?
- What if the calculated packing coefficient is > 1 or < 0 due to anomalous van der Waals volume sums?
- How does the pipeline behave when fewer than 500 valid records are obtained (e.g., after filtering)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download CIF files from the Crystallography Open Database (COD) filtered for organic molecules with ≤ 50 non‑hydrogen atoms, and MUST log download statistics. (See US-1)
- **FR-002**: System MUST extract or generate a canonical SMILES string for each CIF using RDKit, and MUST record whether the SMILES was extracted or generated. Generation uses only bond‑connectivity information; no target-related data (e.g., unit‑cell volume) is consulted. (See US-1)
- **FR-003**: System MUST compute a **Packing Coefficient (PC)** for each crystal as:
  \[
  \text{PC} = \frac{\sum_{i}{V_{\text{vdW},i}}}{\text{Unit‑cell volume}}
  \]
  where \(V_{\text{vdW},i}\) are atomic van der Waals volumes taken from the standard set of Bondi radii, implemented via `rdkit.Chem.rdMolDescriptors.GetAtomicVdWVolume` (or equivalent RDKit constant mapping). PC is the regression target. (See US-2)
- **FR-004**: System MUST encode each SMILES into a fixed‑length fingerprint vector using a pre‑trained SMILES‑Transformer (weights frozen) that runs on CPU only. System MUST ALSO compute 3‑D geometry descriptors (radius of gyration, asphericity, principal moments of inertia) and atom‑type count features derived from the CIF coordinates. These 3‑D features are used **only** for the "Full Model" baseline; the "Primary Model" uses **only** the SMILES fingerprint. (See US-2)
- **FR-005**: System MUST train two 2‑layer MLP regression models with ≤ 100 k trainable parameters: (a) the **Primary Model** using only SMILES fingerprints, and (b) the **Full Model** using SMILES fingerprints + 3‑D descriptors. Both models predict PC. The train/validation split is 80/20. (See US-2)
- **FR-006**: System MUST evaluate both models on the validation set, reporting (a) Mean Absolute Error (MAE), (b) Spearman’s ρ (primary metric) and Pearson’s r (secondary), (c) results of a Shapiro‑Wilk normality test on residuals (diagnostic only), and (d) a two‑sided permutation‑test p‑value computed with **10 000** shuffles for the Primary Model. (See US-2)
- **FR-007**: System MUST perform a sensitivity analysis that sweeps the “high‑packing” threshold over the set {0.5, 0.6, 0.7} and MUST report the resulting Spearman ρ, MAE, and p‑values for each threshold. The thresholds are justified by the typical range of packing coefficients reported in crystallography literature (≈ 0.5–0.8). (See US-3)
- **FR-008**: System MUST apply a Bonferroni correction for the sensitivity analysis thresholds in US-3. (See US-3)
- **FR-009**: System MUST compute variance‑inflation‑factor (VIF) diagnostics on **all predictor variables** (including SMILES fingerprint dimensions and atom‑type counts) **after** the full feature matrix is generated (post FR-004). (See US-2)
- **FR-010**: System MUST produce a reproducible HTML report that includes dataset provenance, preprocessing steps, model architecture (Primary and Full), all evaluation metrics, and the full source code version hash. Figures and statistics in the report are generated from data validated against `contracts/validation_report.schema.yaml`. (See US-2)
- **FR-011**: System MUST compute the Packing Coefficient (PC) as defined in FR-003. PC is the target variable. (See US-2)
- **FR-012**: System MUST record known confounders for each crystal (crystal lattice system, measurement temperature, presence of solvent molecules) and include them as covariates in VIF diagnostics if available. (See US-2)
- **FR-013**: System MUST perform a Feature Ablation analysis comparing the Primary Model (SMILES only) and Full Model (SMILES + 3D) to quantify the specific contribution of 3‑D descriptors versus 2‑D topology. (See US-2)
- **FR-014**: System MUST compute Spearman’s rank correlation ρ and conduct a Shapiro‑Wilk test on PC residuals to verify assumptions. Pearson’s r is reported only if residuals are normally distributed; otherwise, Spearman’s ρ is the primary metric. (See US-2)
- **FR-015**: The permutation‑test in FR-006 shall use **10 000** shuffles with a fixed random seed (42) and **must** use parallelization (e.g., joblib). If runtime exceeds 4 hours, the system MUST stop, log a "deviation" event, and report the p-value based on the completed shuffles. (See US-2)
- **FR-016**: The COD dataset source URL (https://www.crystallography.net/cod/) and version identifier shall be recorded and verified against the official COD repository to satisfy Constitution Principle II (Verified Accuracy). System MUST write a `source_verification.json` file containing the URL, version, and a hash of the downloaded dataset. (See US-1)
- **FR-017**: Atomic van der Waals radii are taken from Bondi, A. (1964) *J. Phys. Chem.*, 68, 441–452, DOI:10.1021/j100785a001, implemented via `rdkit.Chem.rdMolDescriptors.GetAtomicVdWVolume`, satisfying Constitution Principle II. (See FR‑003)
- **FR-018**: Model checkpoints and validation reports shall conform to the schemas `contracts/model.schema.yaml` and `contracts/validation_report.schema.yaml`, respectively, and references to these contracts shall be included in the documentation. (See FR‑010)
- **FR-019**: System MUST perform a power analysis that accounts for the empirical distribution of PC (via bootstrapping) rather than assuming bivariate normality, to ensure ≥ 90% power to detect ρ ≥ 0.3. (See US-2)
- **FR-020**: System MUST implement streaming inference for the SMILES‑Transformer to prevent OOM errors on the 7GB RAM limit, using a batch size ≤ 50. (See US-1)
- **FR-021**: System MUST explicitly generate and include "atom‑type count features" in the feature matrix before VIF calculation (FR-009) and Feature Ablation (FR-013). (See US-2)

### Key Entities *(include if feature involves data)*

- **Dataset**: CSV file containing `smiles`, `smiles_source` (extracted/generated), `packing_coefficient`, `unit_cell_volume`, `radius_of_gyration`, `asphericity`, `principal_moments`, `lattice_system`, `temperature_K`, `has_solvent`, `atom_type_counts`.
- **Model**: Serialized MLP weights (`model_primary.pt`, `model_full.pt`) and the frozen transformer checkpoint (`transformer.pt`).
- **Report**: HTML document (`report.html`) summarizing results and diagnostics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The final dataset contains ≥ 500 complete (SMILES, packing coefficient) records with no missing values. (See US-1)
- **SC-002**: The Primary Model validation Spearman correlation coefficient satisfies ρ ≥ 0.3 **and** the Bonferroni‑corrected permutation‑test p‑value ≤ 0.05, indicating a statistically significant positive relationship between SMILES‑derived features and PC. (See US-2)
- **SC-003**: If ρ < 0.2, the permutation‑test p‑value is ≥ 0.05, confirming a lack of predictive signal (null result). (See US-2)
- **SC-004**: Across the high‑packing thresholds {0.5, 0.6, 0.7}, the variation in Spearman ρ is ≤ ±0.05, demonstrating robustness of the predictive signal. (See US-3)
- **SC-005**: The entire end‑to‑end pipeline (download → report) completes in ≤ 6 hours on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM). (See US-2)
- **SC-006**: If the permutation test exceeds the 4-hour timeout, the report explicitly logs the deviation and the achieved p-value resolution. (See US-2)

## Assumptions

- The COD provides at least 500 organic crystal entries that satisfy the ≤ 50‑atom filter; if fewer are available, the pipeline will issue a warning and abort (research scope limited to N ≈ 500–1000).
- SMILES can be reliably generated from CIF geometry using RDKit; no stereochemistry ambiguities are expected for the filtered set.
- Standard Bondi van der Waals radii are appropriate for calculating atomic volumes; these radii are assumed to be valid for the organic molecules under study (see FR‑017).
- The pre‑trained SMILES transformer model (≈ a few hundred MB) fits within the free‑tier runner’s memory budget and runs in inference‑only mode on CPU, using streaming inference (FR-020).
- No GPU or CUDA libraries are used; all libraries (RDKit, PyTorch‑CPU, scikit‑learn) are compatible with the runner’s environment.
- The permutation test (10 000 shuffles) is computationally tractable on the available CPU resources with parallelization; if runtime exceeds 4 hours, the system logs a deviation and reports the achieved p-value resolution (FR-015).
- Recorded confounder metadata (crystal lattice system, temperature, solvent presence) are available in the COD CIF files for the selected entries.

The COD archive does **not** guarantee that every entry contains a SMILES string. Some CIF records include an optional `_chemical_structure_SMILES` tag when the depositor provides it, but the majority of structures lack this tag. Consequently, the pipeline must be prepared to generate a canonical SMILES from the 3‑D geometry using RDKit whenever the SMILES field is absent.