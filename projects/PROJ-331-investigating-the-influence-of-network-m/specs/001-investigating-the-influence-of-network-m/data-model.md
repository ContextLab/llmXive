# Data Model: Investigating the Influence of Network Motifs on Resting-State Functional Connectivity

## 1. Entities & Relationships

| Entity | Key Attributes | Relationships |
|--------|----------------|---------------|
| **Subject** | `subject_id` (string), `status` (`processed`/`skipped`/`error`) | Owns one Structural Connectome (optional), one Functional Connectome, one Motif Profile, one Metadata record |
| **Structural Connectome** | `structural.npy` — binary symmetric 100×100 float32 | Belongs to Subject; derived from real structural input with provenance, or absent (gated) |
| **Functional Connectome** | `rsfc.npy` — symmetric 100×100 float32 Pearson matrix | Belongs to Subject |
| **Motif Profile** | `motif_profile.json` — motif_id → z-score map + null-model params | Belongs to Subject; derived from Structural Connectome |
| **Metadata** | `metadata.json` conforming to `structural_connectome.schema.yaml` (provenance, seed, status) | Belongs to Subject |
| **Subject Metrics** | CSV row: `subject_id, rsfc_strength, global_efficiency, global_degree` | Aggregates Subject outputs |
| **Correlation Result** | JSON row per motif×metric: partial r (Pearson/Spearman), raw/Bonferroni/empirical p, VIF, method | Aggregates across Subjects |
| **Manifest** | `manifest.json`: cohort counts, subject records, checksums | Global view |

## 2. File Formats

- **Raw**: `data/raw/openneuro-fslr64k/*.parquet` (checksummed, unchanged; SHA-256 recorded in manifest)
- **Processed** (all new files, derivations documented in metadata):
  - `data/processed/<subject_id>/structural.npy`
  - `data/processed/<subject_id>/rsfc.npy`
  - `data/processed/<subject_id>/motif_profile.json`
  - `data/processed/<subject_id>/metadata.json`
  - `data/processed/subject_metrics.csv`
  - `data/processed/correlation_results.json` (conforms to `output.schema.yaml`)
  - `data/processed/manifest.json` (conforms to `dataset.schema.yaml`)
- **Outputs**: `results/results.pdf`; `data/logs/pipeline.log` (machine-readable, structured entries)

## 3. Data Flow

1. Ingestion (`data_loader.py`): parquet → `data/raw/` (checksummed)
2. Parcellation (`data_loader.py`): time series → 100-node rsFC; structural input → binary adjacency (gated)
3. Metrics: rsFC strength, global efficiency, global degree → `subject_metrics.csv`
4. Motif enumeration (`motif_analysis.py`) → `motif_profile.json`
5. Metadata (`utils.py`) → `metadata.json` per subject
6. Statistics (`correlation_analysis.py`) → `correlation_results.json`
7. Reporting (`report_generator.py`) → `results.pdf`
8. Logging (`utils.py`) → `pipeline.log` at every step

## 4. Validation & Logging

- `utils.py` validates constants at startup: `seed=42`, Bonferroni α = 0.05/13, `permutation_count ≥ 1000`, `vif_threshold = 5`, and logs pinned library versions.
- Manifest enforces SC-001: `cohort_actual ≥ 0.95 × cohort_target` else warning.
- Contract tests (`tests/contract/test_schemas.py`) validate every JSON artifact against `contracts/*.schema.yaml`.
- No PII: subject IDs are dataset-provided pseudonymous identifiers only.
