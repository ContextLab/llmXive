# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **RNASeqSample** | `accession_id` (string), `species` (string), `raw_counts_path` (path), `metadata` (JSON) | One GEO series (after filtering for ≥ 30 samples). |
| **Gene** | `gene_id` (TAIR or Ensembl), `cpm` (float), `variance` (float), `string_protein_id` (string, optional) | After CPM filtering and variance selection. |
| **RawCorrelation** | `gene_id_1`, `gene_id_2`, `correlation` (float), `p_value` (float), `adjusted_p_value` (float) | Produced by block‑wise correlation; stored in `raw_correlations_<species>.tsv.gz`. |
| **ProteinCorrelation** | `protein_id_1`, `protein_id_2`, `correlation` (float) | After identifier mapping; used for edge export. |
| **PredictedEdge** | `protein_id_1`, `protein_id_2`, `correlation` (float) | Rows of `predicted_ppi_<species>.tsv`. |
| **EvaluationMetric** | `species`, `auroc`, `auprc`, `baseline_auroc`, `baseline_auprc`, `baseline_p` (float) | Stored in `evaluation_metrics.json`. |
| **GOEnrichmentRecord** | `go_id`, `description`, `raw_p`, `adjusted_p`, `gene_count` | Rows of `go_enrichment_<species>.tsv`. |
| **ThresholdSensitivityRecord** | `threshold`, `edge_count`, `auroc`, `auprc` | Rows of `threshold_sensitivity_<species>.tsv`. |
| **PipelineLogEntry** | `timestamp`, `level`, `message`, `schema_version`, `seed`, `command` | JSON‑Line entries in `pipeline.log`. |

## Relationships

* Each **RNASeqSample** belongs to a **Species** (captured in `species.yaml`).  
* **Gene** objects are derived from the union of all samples for a species after CPM filtering.  
* **RawCorrelation** is computed for every unordered pair of retained **Gene** objects.  
* **ProteinCorrelation** is a filtered view of **RawCorrelation** where both genes have a valid `string_protein_id`.  
* **PredictedEdge** ⊆ **ProteinCorrelation** (edges satisfying the correlation threshold).  
* **EvaluationMetric** consumes the full set of **ProteinCorrelation** scores plus the STRING positive/negative label sets.  
* **GOEnrichmentRecord** is computed from the set of genes appearing in **PredictedEdge** against the background gene universe.  

## Storage Layout (relative to project root)

```
data/
├── raw/                # GEO series TSV/CSV files (unchanged)
├── processed/
│   ├── normalized/<species>.tsv
│   ├── raw_correlations_<species>.tsv.gz
│   ├── predicted_ppi_<species>.tsv
│   ├── go_enrichment_<species>.tsv
│   └── threshold_sensitivity_<species>.tsv
├── external/
│   └── string_highconf.parquet   # verified STRING dataset (see research.md)
└── checksums.yaml                # SHA‑256 hashes for all raw files
logs/
└── pipeline.log
results/
├── evaluation_metrics.json
├── summary_<species>.txt
└── final_report.txt
state/
└── artifact_hashes.yaml
```

All TSV files are UTF‑8, tab‑delimited, with a header row. Gzipped files are streamed with `gzip.open(..., 'rt')`.

---
