# Data Model: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Overview
The pipeline converts OQMD records into reconstructed bulk structures, grain‑boundary supercells, **bulk‑lattice clustering descriptors** (computed before any impurity insertion), EAM‑derived segregation energies, and a schema‑validated training dataset. Every artifact is checksummed (using a SHA‑2 hash) in `data/metadata.yaml`; raw data is immutable; all transformations produce new files with documented provenance.

## Entity Definitions

| Entity | Fields | Description |
|--------|--------|-------------|
| **OQMDRecord** | `record_id` (str), `name` (str), `formula` (str), `spacegroup` (int), `volume_per_atom` (float), `source_url` (str) | One row from the verified OQMD loader; stored under `data/raw/`. |
| **BulkConfiguration** | `bulk_id` (str), `record_id` (str), `formula` (str), `spacegroup` (int), `lattice` (list), `sites` (list[dict]), `derivation` (str) | Bulk structure reconstructed via `pymatgen.Structure.from_spacegroup` using `volume_per_atom`. |
| **GrainBoundaryStructure** | `gb_id` (str), `bulk_id` (str), `boundary_plane` (str), `misorientation_angle` (float), `sites` (list[dict]), `interface_mask` (list[bool]), `impurity_species` (str), `n_impurity` (int) | GB supercell with interface impurities; zero‑impurity cases filtered and counted. |
| **ClusteringDescriptor** | `gb_id` (str), `impurity_species` (str), `descriptor_type` (enum: rdf_peak, pair_correlation, voronoi_count), `value` (float), `bulk_region_only` (bool) | One of the three FR‑002 descriptor types, computed **on the bulk lattice region only** (outside any GB interface). |
| **SegregationEnergy** | `gb_id` (str), `impurity_species` (str), `energy_eV` (float), `method` (enum: EAM), `potential_name` (str), `status` (enum: SUCCESS, FAILED) | EAM‑derived segregation energy; ≥200 configurations required (FR‑003). |
| **TrainingSample** | `sample_id` (str), `gb_id` (str), `alloy_system` (str), `impurity_species` (str), `rdf_peak_value` (float), `pair_corr_value` (float), `voronoi_count` (int), `misorientation_angle` (float), `boundary_plane` (str), `local_lattice_strain` (float), `atomic_radius` (float), `electronegativity` (float), `segregation_energy_eV` (float), `split` (enum: train, test) | Row of `data/processed/training_set.csv`; validated against `contracts/dataset.schema.yaml`. **Note**: `cluster_size` is **not** included as a predictor; it is computed post‑insertion solely for visualization (FR‑009). |
| **HypothesisResult** | `feature_name` (str), `coefficient` (float), `p_value_raw` (float), `p_value_adjusted` (float), `significance_changed` (bool) | Row of the US‑3 report; aggregated into `results/hypothesis_report.json`. |

## Data Flow
```mermaid
graph TD
    A[Verified OQMD loader] -->|download.py| B[data/raw OQMDRecord]
    B -->|gb_builder.py| C[BulkConfiguration]
    C -->|GB supercell + impurity insertion| D[GrainBoundaryStructure]
    D -->|descriptors.py (bulk‑only)| E[ClusteringDescriptor + VIF report]
    D -->|extract_energy.py| F[SegregationEnergy]
    E & F -->|train_model.py assembly| G[TrainingSample CSV]
    G -->|train/CV/power/RESET| H[results/metrics.json + hypothesis_report.json]
    G -->|plots.py (post‑insertion)| I[cluster_size_vs_segregation.png]
```

## Validation Constraints (FR/SC mapping)

- **FR‑001**: `download.py` uses the verified OQMD loader with ≤3 retries; `[DATA_UNAVAILABLE]` logged on permanent failure. **Materials Project omitted (waiver).**  
- **FR‑002**: `descriptors.py` emits all three descriptor types **on the bulk lattice only**.  
- **FR‑003**: ≥200 configurations with linked descriptors + energies (generated via validated EAM potentials).  
- **FR‑004a/b**: Both Linear Regression (with p‑values) and RandomForest trained under 5‑fold CV (LOOCV if N < 5).  
- **FR‑005/SC‑003**: Bonferroni‑adjusted p‑values + significance‑change count in `hypothesis_report.json`.  
- **FR‑007/FR‑012/SC‑004**: VIF computed on the three raw descriptors before any PCA; threshold VIF = 10 (flagged per 2005.02245); JSON report for VIF ≥ 10.  
- **FR‑008**: Power‑analysis fields (f² = 0.15, α = 0.05, predictor count = 7) stored in `metrics.json`.  
- **FR‑009/SC‑005**: PNG figure with confidence intervals per alloy system (uses post‑insertion `cluster_size` *only for illustration*).  
- **FR‑010**: Ramsey RESET test (α = 0.05) stored as `appears_linear` flag.  
- **FR‑014**: Permutation‑test (≥1 000 permutations) for each regression coefficient; empirical p‑values reported.  
- **SC‑001/SC‑002**: Permutation‑test p‑value for R², per‑system R², held‑out RMSE with confidence intervals.  
- **SC‑004**: VIF ≥ 10 threshold enforced; JSON collinearity report generated.  

## Hygiene & Provenance
- SHA‑256 checksums for every raw and processed file in `data/metadata.yaml`.  
- `data/metadata.yaml` records OQMD dataset id, loader config, random seeds, EAM potential version, and code hash.  
- No PII; only materials‑science data are stored.

---===
