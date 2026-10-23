# Data Model: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Overview

The pipeline converts OQMD records into reconstructed bulk structures, grain‑boundary supercells, **bulk‑pre‑insertion** clustering descriptors, EAM‑derived segregation energies, and a schema‑validated training dataset. Every artifact is checksummed (using a SHA‑2 hash) in `data/metadata.yaml`; raw data is immutable; all transformations produce new files with documented provenance.

## Entity Definitions

| Entity | Fields | Description |
|--------|--------|-------------|
| **OQMDRecord** | `record_id` (str), `name` (str), `formula` (str), `spacegroup` (int), `volume_per_atom` (float), `source_url` (str) | One row from the verified OQMD loader; stored under `data/raw/`. |
| **BulkConfiguration** | `bulk_id` (str), `record_id` (str), `formula` (str), `spacegroup` (int), `lattice` (list), `sites` (list[dict]), `derivation` (str) | Bulk structure reconstructed via `pymatgen.Structure.from_spacegroup` using `volume_per_atom`. |
| **GrainBoundaryStructure** | `gb_id` (str), `bulk_id` (str), `boundary_plane` (str), `misorientation_angle` (float), `sites` (list[dict]), `interface_mask` (list[bool]), `impurity_species` (str), `n_impurity` (int) | GB supercell with interface impurities; zero‑impurity cases filtered and counted. |
| **ClusteringDescriptor** | `gb_id` (str), `impurity_species` (str), `descriptor_type` (enum: rdf_peak, pair_correlation, voronoi_count), `value` (float), `interface_only` (bool) | One of the three FR‑002 descriptor types, computed **on the bulk configuration before impurity insertion** and then restricted to the interface region for analysis. |
| **SegregationEnergy** | `gb_id` (str), `impurity_species` (str), `energy_eV` (float), `method` (enum: EAM), `potential_name` (str), `status` (enum: SUCCESS, FAILED) | EAM‑derived segregation energy; ≥200 configurations required (FR‑003). |
| **ValidationRecord** | `benchmark_source` (str or null), `n_benchmark` (int), `mae_eV` (float or null), `status` (enum: VALIDATED, DATA_UNAVAILABLE) | FR‑011 validation result; `[DATA_UNAVAILABLE]` recorded when no verified DFT benchmark exists. |
| **TrainingSample** | `sample_id` (str), `gb_id` (str), `alloy_system` (str), `impurity_species` (str), `rdf_peak_value` (float), `pair_corr_value` (float), `voronoi_count` (int), `cluster_size` (float), `local_lattice_strain` (float), `atomic_radius` (float), `electronegativity` (float), `segregation_energy_eV` (float), `split` (enum: train, test) | Row of `data/processed/training_set.csv`; validated against `contracts/dataset.schema.yaml`. **Derivations:** `cluster_size` = mean nearest‑neighbor distance among interface impurities (derived from the same neighbor list used for Voronoi counts). |
| **HypothesisResult** | `feature_name` (str), `coefficient` (float), `p_value_raw` (float), `p_value_adjusted` (float), `significance_changed` (bool) | Row of the US‑3 report; aggregated into `results/hypothesis_report.json`. |

## Data Flow

```mermaid
graph TD
    A[Verified OQMD loader] -->|download.py| B[data/raw OQMDRecord]
    B -->|gb_builder.py| C[BulkConfiguration]
    C -->|GB supercell + impurity insertion| D[GrainBoundaryStructure]
    D -->|descriptors.py (post‑relaxation)| E[ClusteringDescriptor + VIF report]
    D -->|simulate_energy.py| F[SegregationEnergy]
    F -->|validate_potential.py| G[ValidationRecord]
    E & F & G -->|train_model.py assembly| H[TrainingSample CSV]
    H -->|train/CV/power/correction| I[results/metrics.json + hypothesis_report.json]
    H -->|plots.py| J[cluster_size_vs_segregation.png]
```

## Validation Constraints (FR/SC mapping)

- **FR‑001**: `download.py` uses the verified OQMD loader with ≤3 retries; `[DATA_UNAVAILABLE]` logged on permanent failure. **Materials Project omitted (waiver).**  
- **FR‑002**: `descriptors.py` emits all three descriptor types per impurity, **computed on the bulk configuration before impurity insertion**.  
- **FR‑003**: ≥200 configurations with linked descriptors + energies (generated via EAM).  
- **FR‑004a/b**: Both Linear Regression (with p‑values) and RandomForest trained under 5‑fold CV (LOOCV if N < 5).  
- **FR‑005/SC‑003**: Bonferroni‑adjusted p‑values + significance‑change count in `hypothesis_report.json`.  
- **FR‑007/FR‑012/SC‑004**: VIF computed on the three raw descriptors before any PCA; threshold VIF = 10; JSON report for VIF ≥ 10.  
- **FR‑008**: Power‑analysis fields (f² = 0.15, α = 0.05, predictor count = 7) stored in `metrics.json`.  
- **FR‑009/SC‑005**: PNG figure with confidence intervals per alloy system.  
- **FR‑010**: Linearity‑assessment record (`appears_linear`) generated.  
- **FR‑011/SC‑006**: `ValidationRecord` with MAE ≤ 0.1 eV **if** a verified DFT benchmark becomes available; otherwise status `DATA_UNAVAILABLE`.  
- **SC‑001/SC‑002**: Permutation‑test p‑value for R², per‑system R², held‑out RMSE with 95 % CIs.  

## Hygiene & Provenance

- SHA‑256 checksums for every raw and processed file in `data/metadata.yaml`.  
- `data/metadata.yaml` records OQMD dataset id, loader config, random seeds, EAM potential version, and code hash.  
- No PII; only materials‑science data are stored.

---


