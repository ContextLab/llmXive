# Data Model: Can Publicly Available Microbiome Data Predict Host Plant Defense Responses?

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Sample** | One biological specimen, uniquely identified. | `sample_id` (str), `species` (enum: `arabidopsis`, `tomato`), `condition` (enum: `herbivore_stress`), `study_id` (str) |
| **ASVTable** | Sparse matrix of Amplicon Sequence Variant counts per sample. | Columns: `asv_1 … asv_N` (int), rows indexed by `sample_id` |
| **MetaboliteProfile** | Vector of normalized intensities for defense metabolites. | Columns: `metab_glucosinolate`, `metab_alkaloid`, `metab_phenolic`, … (float) |
| **MergedDataset** | Wide table where each row corresponds to a Sample and contains both ASV and metabolite columns **plus species one‑hot columns** for modeling. | All fields from **Sample**, plus ASV columns, plus Metabolite columns, plus `species_arabidopsis` and `species_tomato` (int, 0/1) |

## Schema Definition (YAML contract)
See `contracts/merged-dataset.schema.yaml`.

## Data Flow Diagram (conceptual)

```
Raw SRA parquet  --> acquire.py --> raw_reads.parquet
Raw MetaboLights --> (unavailable) --> (guard abort)

raw_reads.parquet --> curate.py --> asv_table.csv
(when available) metabolite_raw.csv --> curate.py --> metabolite_table.csv

asv_table.csv + metabolite_table.csv --> integrate.py --> merged_dataset.csv
merged_dataset.csv --> pca.py / model.py --> results/
```

## Storage Layout
```
data/
├── raw/
│   ├── sra_parquet/            # downloaded parquet files (or placeholder guard)
│   └── metabolomics/           # (empty; guard will abort)
├── processed/
│   ├── asv_table.csv
│   ├── metabolite_table.csv
│   └── merged_dataset.csv      # conforms to contract
└── checksums/
    └── checksums.txt
```

---

