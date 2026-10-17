# Data Model: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Overview

The pipeline transforms real OQMD records into reconstructed bulk structures, GB supercells, interface‑only clustering descriptors, EAM segregation energies, and a schema‑validated training dataset. All artifacts are checksummed (SHA‑256 in `data/metadata.yaml`); raw data is immutable; every derivation writes a new file with documented provenance.

## Entity Definitions

| Entity | Fields | Description |
|--------|--------|-------------|
| **OQMDRecord** | `record_id` (str), `name` (str), `formula` (str), `spacegroup` (int), `volume_per_atom` (float), `source_url` (str) | One row from the verified OQMD loader; persisted immutably under `data/raw/`. |
| **BulkConfiguration** | `bulk_id` (str), `record_id` (str), `formula` (str), `spacegroup` (int), `lattice` (list), `sites` (list[dict]), `derivation` (str) | Bulk structure reconstructed from formula + spacegroup via pymatgen (`Structure.from_spacegroup`) using `volume_per_atom` to estimate lattice constants; `derivation` documents the reconstruction method. |
| **GrainBoundaryStructure** | `gb_id` (str), `bulk_id` (str), `boundary_plane` (str), `misorientation_angle` (float), `sites` (list[dict]), `interface_mask` (list[bool]), `impurity_species` (str), `n_impurity` (int) | GB supercell with impurities inserted at the interface; zero‑impurity cases filtered with logged counts (edge case). |
| **ClusteringDescriptor** | `gb_id` (str), `impurity_species` (str), `descriptor_type` (enum: rdf_peak, pair_correlation, voronoi_count), `value` (float), `interface_only` (bool, always true) | One of the three FR‑002 descriptor types, computed only within the interface region **after** EAM relaxation. |
| **SegregationEnergy** | `gb_id` (str), `impurity_species` (str), `energy_eV` (float), `method` (enum: EAM), `potential_name` (str), `status` (enum: SUCCESS, FAILED) | Leave‑one‑out segregation energy from EAM simulation; ≥200 configurations; missing‑energy entries excluded with counts and a >5 % warning. |
| **ValidationRecord** | `benchmark_source` (str or null), `n_benchmark` (int), `mae_eV` (float or null), `status` (enum: VALIDATED, DATA_UNAVAILABLE) | FR‑011 EAM‑vs‑DFT validation result; `DATA_UNAVAILABLE` records the explicit no‑verified‑source limitation. |
| **TrainingSample** | `sample_id` (str), `gb_id` (str), `alloy_system` (str), `impurity_species` (str), `rdf_peak_value` (float), `pair_corr_value` (float), `voronoi_count` (int), `cluster_size` (float), `local_lattice_strain` (float), `atomic_radius` (float), `electronegativity` (float), `segregation_energy_eV` (float), `split` (enum: train, test) | Row of `data/processed/training_set.csv`, validated against `contracts/dataset.schema.yaml`. **Derivations:** `cluster_size` = mean nearest‑neighbor distance among interface impurities (derived from the same neighbor list used for Voronoi counts); `local_lattice_strain` = trace of the local strain tensor around the interface; `atomic_radius` and `electronegativity` are taken from standard elemental property tables (cited in code). |
| **HypothesisResult** | `feature_name` (str), `coefficient` (float), `p_value_raw` (float), `p_value_adjusted` (float), `significance_changed` (bool) | Row of the US‑3 report; aggregated into `results/hypothesis_report.json`. |

## Data Flow

```mermaid
graph TD
    A[Verified OQMD loader] -->|download.py + checksums| B[data/raw OQMDRecord]
    B -->|gb_builder.py reconstruction| C[BulkConfiguration]
    C -->|GB supercell + impurity insertion| D[GrainBoundaryStructure]
    D -->|descriptors.py (post‑relaxation)| E[ClusteringDescriptor + VIF report]
    D -->|simulate_energy.py EAM| F[SegregationEnergy]
    F -->|validate_potential.py| G[ValidationRecord]
    E & F & G -->|train_model.py assembly| H[TrainingSample CSV]
    H -->|train/CV/power/correction| I[results/metrics.json + hypothesis_report.json]
    H -->|plots.py| J[cluster_size_vs_segregation.png]
```

## Validation Constraints (FR/SC mapping)

- **FR‑001**: `download.py` uses the verified loader with ≤3 retries; `[DATA_UNAVAILABLE]` logged on permanent failure.
- **FR‑002**: `descriptors.py` emits all three descriptor types per impurity, interface‑only (`interface_only = true`) **after** relaxation.
- **FR‑003**: ≥200 configurations with linked descriptors + energies in the training set (generated via EAM).
- **FR‑004a/b**: both models trained under 5‑fold CV (LOOCV if N < 5); p‑values for the linear model.
- **FR‑005/SC‑003**: adjusted p‑values + significance‑change count in `hypothesis_report.json`.
- **FR‑007/FR‑012/SC‑004**: VIF on the three raw descriptors before any PCA/dimensionality reduction; threshold VIF = 10; JSON report for VIF ≥ 10.
- **FR‑008**: power‑analysis fields (f² = 0.15, α = 0.05, predictor count = 7) in `metrics.json`.
- **FR‑009/SC‑005**: per‑alloy‑system PNG with 95 % CIs.
- **FR‑010**: linearity‑assessment record (scatter plots + residual diagnostics + verdict).
- **FR‑011/SC‑006**: ValidationRecord with MAE ≤ 0.1 eV against a DFT benchmark (≥30 samples) **if** a verified benchmark is available; otherwise the status is `DATA_UNAVAILABLE`.
- **SC‑001/SC‑002**: permutation‑test p‑value for R², per‑system R², held‑out RMSE with 95 % CIs.

## Hygiene & Provenance

- SHA‑256 checksums for every raw and processed file in `data/metadata.yaml`; raw files never modified in place.
- `data/metadata.yaml` records the OQMD dataset id, loader configuration, random seeds, EAM potential name/version, and code hash.
- No PII (crystallographic data only).
