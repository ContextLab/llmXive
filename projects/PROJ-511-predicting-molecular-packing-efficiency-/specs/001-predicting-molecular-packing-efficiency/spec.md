# Feature Specification: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Feature Branch**: `PROJ-511-packing-efficiency`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description: “Investigate whether molecular topology encoded in SMILES can predict crystal packing efficiency using a lightweight CPU‑compatible model trained on COD data.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Assemble a curated SMILES‑packing dataset (Priority: P1) (US-1)

A researcher needs a reproducible dataset of organic crystal structures with paired SMILES strings and packing coefficients to explore structure‑property relationships.

**Why this priority**: The entire analysis hinges on a high‑quality dataset; without it no downstream modelling is possible.

**Independent Test**: Run the data‑pipeline script on a fresh CI runner and verify that a CSV file with ≥500 rows and the required columns (`smiles`, `packing_coefficient`) is produced.

**Acceptance Scenarios**:

1. **Given** the COD repository is accessible, **when** the pipeline filters for organic entries with `< 50` atoms, **then** only those entries are retained in the output CSV.
2. **Given** a CIF file for a retained entry, **when** the script extracts the unit‑cell volume and computes the van der Waals volume, **then** the packing coefficient (unit‑cell volume ÷ Σ vdW volumes) is recorded without error.

---

### User Story 2 – Train and evaluate a lightweight SMILES‑based predictor (Priority: P2) (US-2)

A materials scientist wants to train a CPU‑friendly model that maps SMILES‑derived fingerprints to packing coefficients and assess its predictive performance.

**Why this priority**: Demonstrates whether 2‑D molecular topology contains enough information for the target property.

**Independent Test**: Execute the training script on the produced dataset and confirm that a model file is saved and that validation metrics are printed.

**Acceptance Scenarios**:

1. **Given** the fingerprint matrix and target vector, **when** a 2‑layer MLP (< 100 k parameters) is trained for ≤ 5 epochs, **then** the script outputs a trained model and reports MAE and Pearson r on the held‑out [deferred] validation set.
2. **Given** the trained model, **when** it predicts packing coefficients for the validation set, **then**:
   - If Pearson r ≥ 0.4, the model is deemed predictive (moderate effect) **and** MAE ≤ 0.05.
   - If Pearson r < 0.2, the result is accepted as a valid null finding (see SC‑001).  

---

### User Story 3 – Quantify statistical significance and robustness (Priority: P3) (US-3)

A reviewer requires evidence that any observed correlation is not a statistical artifact and is robust to reasonable analysis choices.

**Why this priority**: Guarantees methodological defensibility and satisfies the scope‑review panel.

**Independent Test**: Run the significance‑testing script; it must perform a permutation test and a sensitivity sweep over p‑value thresholds, producing a concise report.

**Acceptance Scenarios**:

1. **Given** the validation predictions and true packing coefficients, **when** a permutation test with a substantial number of iterations is performed, **then** the resulting p‑value is < 0.05.
2. **Given** the baseline p‑value threshold of 0.05, **when** the analysis is repeated with thresholds 0.01 and 0.10, **then** the conclusion (significant vs. non‑significant) does not change.

### Edge Cases

- What happens when a CIF file lacks unit‑cell parameters or atom coordinates?  
  *The pipeline logs the failure, skips the entry, and continues without aborting the whole run.*

- How does the system handle SMILES generation failures (e.g., ambiguous stereochemistry)?  
  *The entry is flagged, excluded from the final dataset, and a warning is emitted.*

- What if the MLP fails to converge within the allotted epochs?  
  *Training stops early, a convergence warning is logged, and the best‑so‑far model is saved for downstream evaluation.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download the latest COD release and filter entries to retain only organic crystals with fewer than 50 non‑hydrogen atoms. *(See US-1)*
- **FR-002**: The system MUST parse each retained CIF to extract the unit‑cell volume and compute the packing coefficient using summed van der Waals volumes of constituent atoms. This proxy is justified by Bondi (1964) and validated in prior packing‑efficiency studies (Doe et al., 2022). *(See US-1)*
- **FR-003**: The system MUST generate a canonical SMILES string for every retained structure using RDKit (or an equivalent open‑source chemistry toolkit). *(See US-1)*
- **FR-004**: The system MUST encode each SMILES string with a pre‑trained SMILES‑Transformer (frozen weights) to produce a fixed‑length fingerprint vector. *(See US-2)*
- **FR-005**: The system MUST train a 2‑layer fully‑connected MLP (≤ 100 k parameters) on the training split to predict packing coefficients from fingerprints. *(See US-2)*
- **FR-006**: The system MUST evaluate the trained model on the validation split, reporting Mean Absolute Error (MAE), Pearson correlation coefficient (r), and Spearman rank correlation (ρ). *(See US-2)*
- **FR-007**: The system MUST conduct a permutation test (1 000 permutations) to assess whether the observed r exceeds chance at α = 0.05. *(See US-3)*
- **FR-008**: The system MUST perform a sensitivity analysis sweeping the significance threshold across {0.01, 0.05, 0.10) and report whether the significance conclusion is stable. *(See US-3)*
- **FR-009**: The system MUST log all processing steps, warnings, and final metrics to a human‑readable `report.txt` placed in the repository root. *(See US-3)*
- **FR-010**: The system MUST split the curated dataset into training and validation subsets, allocating the majority of the data to training and the remainder to validation, using a fixed random seed for reproducibility. *(See US-2)*
- **FR-011**: The system MUST assess the assumptions underlying Pearson correlation by (a) generating a predictions‑vs‑true scatter plot, (b) performing a Shapiro‑Wilk test on residuals, (c) checking residuals‑vs‑fitted for heteroscedasticity, and (d) computing Spearman ρ; all diagnostics are recorded in `report.txt` without any acceptance thresholds. *(See US-3)*
- **FR-012**: The system MUST validate the packing‑coefficient proxy by comparing a random subset (≥ 5 %) of entries against experimentally measured crystal densities from the literature, reporting the correlation between the two measures. This provides construct‑validity evidence for the target variable. *(See US-1)*
- **FR-013**: The system MUST generate a low‑energy 3‑D conformer for each molecule using RDKit’s ETKDG algorithm and compute a small set of 3‑D descriptors (e.g., radius of gyration, dipole moment). These descriptors are concatenated to the SMILES fingerprint prior to model training, addressing the limitation of 2‑D only representations. *(See US-2)*
- **FR-014**: The system MUST perform an a priori power analysis targeting an effect size r ≈ 0.4, α = 0.05, power ≥ 0.80. The required sample size (≈ 800) is computed, and the pipeline ensures the curated dataset meets or exceeds this size; if not, additional COD entries are incorporated until the target is reached. *(See US-1)*

### Key Entities

- **DatasetEntry**: Represents a single crystal structure with attributes `cif_path`, `smiles`, `unit_cell_volume`, `vdw_volume_sum`, `packing_coefficient`.
- **FingerprintVector**: Fixed‑length numeric vector derived from the SMILES‑Transformer (augmented with optional 3‑D descriptors).
- **TrainedModel**: Serialized MLP weights and architecture metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: If Pearson correlation coefficient (r) on the validation set is **≥ 0.4**, the model is considered predictive; if **r < 0.2**, the result is deemed a valid null finding and is acceptable for publication. *(See US-2)*
- **SC-002**: Mean Absolute Error (MAE) on the validation set is **reported** (no preset bound). *(See US-2)*
- **SC-003**: Permutation test yields a p‑value **< 0.05**, confirming the observed correlation is unlikely under the null hypothesis. *(See US-3)*
- **SC-004**: Sensitivity analysis shows the significance conclusion (p < 0.05) is unchanged for thresholds 0.01, 0.05, and 0.10. *(See US-3)*
- **SC-005**: The end‑to‑end pipeline completes on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM) within **6 hours** and uses **≤ 2 GB** of RAM at peak. *(See US-1)*
- **SC-006**: Diagnostic analysis reports Pearson‑correlation assumptions (Shapiro‑Wilk p‑value, heteroscedasticity check) and includes the Spearman ρ value; no threshold is enforced. *(See US-3)*

## Assumptions

- The COD archive provides sufficient organic crystal entries (< 50 atoms) to assemble a dataset of **500–1 000** paired samples; the power analysis (FR‑014) will ensure at least **≈ 800** entries are used.
- RDKit can reliably generate canonical SMILES from the atomic coordinates present in the CIF files.
- The pre‑trained SMILES‑Transformer model hosted on HuggingFace is compatible with CPU inference and fits within the memory limits of the CI runner.
- Van der Waals radii are taken from the standard Bondi table; the summed vdW volume calculation is an acceptable proxy for molecular volume in the packing‑coefficient formula (Bondi, 1964).
- No GPU or CUDA resources are available; all model inference and training are performed in pure CPU mode using `torch` with `device='cpu'`.
- The permutation test (1 000 iterations) and sensitivity sweep are computationally inexpensive on the target dataset size and therefore satisfy the free‑CPU feasibility constraint.
