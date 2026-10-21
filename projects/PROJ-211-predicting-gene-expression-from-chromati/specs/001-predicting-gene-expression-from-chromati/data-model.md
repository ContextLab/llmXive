# Data Model: Predicting Gene Expression from Chromatin Accessibility

## 1. Overview
Defines all file‑level schemas used throughout the pipeline, from raw ENCODE downloads to final model artifacts. Every file is validated against a JSON‑Schema contract in `contracts/`.

## 2. Input Data Models

| File | Format | Key Columns | Description |
|------|--------|-------------|-------------|
| `data/raw/encode_counts.csv` | CSV | `gene_id`, `gene_name`, `sample_id`, `cell_line`, `count` | RNA‑seq raw read counts (one row per gene‑sample). |
| `data/raw/encode_peaks.bed` | BED | `chrom`, `start`, `end`, `score`, `strand` | ATAC/DNase peak calls (score = signal intensity). |
| `data/raw/gene_coords.bed` | BED | `chrom`, `start`, `end`, `gene_id`, `gene_name` | TSS coordinates (hg38). |

All three files are accompanied by SHA‑256 checksums recorded in `state/projects/...yaml`.

## 3. Processed Data Models

| Artifact | Format | Columns / Structure | Constraints |
|----------|--------|---------------------|-------------|
| `filtered_expression.csv` | CSV | `gene_id`, `cell_line`, `count` | Genes with zero count across *all* samples removed (FR‑003). |
| `imputed_expression.csv` | CSV | `gene_id`, `cell_line`, `log_count` | `log_count = log(count + 1)` (FR‑004); missing values imputed with median per gene (FR‑005). |
| `normalized_counts.csv` | CSV | `gene_id`, `cell_line`, `cpm` | CPM‑normalised RNA‑seq counts (library‑size scaling). |
| `normalized_peaks.csv` | CSV | `peak_id`, `cell_line`, `cpm` | CPM‑normalised ATAC/DNase peak scores. |
| `selected_bins.txt` | TXT | One integer per line (0‑based bin index) | Bins retained after variance‑based filter (≤ N‑1 per cell line). |
| `binned_matrix.csv` | CSV (wide) | `gene_id`, `cell_line`, `bin_1` … `bin_200` (all bins retained) | Accessibility summed per 200 fixed‑width bins within ±50 kb of TSS; promoter (±2 kb) set to 0 (FR‑002, FR‑008). |
| `housekeeping_genes.csv` | CSV | `gene_id`, `gene_name`, `cv` | CV < 0.2 across cell lines (derived for FR‑009). |
| `cell_type_specific_genes.csv` | CSV | `gene_id`, `gene_name`, `max_cv`, `cell_line` | CV > 0.5 in at least one cell line (derived for FR‑010). |
| `housekeeping_matrix.csv` | CSV | Same layout as `binned_matrix.csv` but restricted to housekeeping genes | Used for FR‑009 performance calculation. |

## 4. Model Artifacts

| Artifact | Format | Schema Keys |
|----------|--------|-------------|
| `elastic_net_{cell_line}.pkl` | Pickle (sklearn `ElasticNet`) | `cell_line`, `alpha`, `l1_ratio`, `coef` (a representative value), `intercept` |
| `cv_scores.json` | JSON array | `cell_line`, `fold`, `r2`, `pearson_r`, `p_value`, `p_value_corrected` |

## 5. Derived Results

| File | Format | Description |
|------|--------|-------------|
| `feature_importance.csv` | CSV | Top bins per gene with coefficient magnitude, distance to TSS, and boolean `within_10kb`. |
| `sc003_enrichment.json` | JSON | Empirical p‑value for the proportion of top‑100 bins within ±10 kb (permutation test, 1 000 draws). |
| `housekeeping_r2.csv` | CSV | R² values for housekeeping genes per cell line (FR‑009). |
| `performance_gap.csv` | CSV | ΔR² between housekeeping and cell‑type‑specific genes (FR‑010). |
| `external_validation.json` | JSON | R² on held‑out cell line (cross‑cell‑line validation, SC‑006). |
| `paper/results.md` & `paper/limitations.md` | Markdown | Human‑readable report generated from the above CSV/JSON files. |

## 6. Data Flow Diagram
```mermaid
flowchart TD
    A[ENCODE RNA‑seq] -->|download_encode.py| B(data/raw/encode_counts.csv)
    C[ENCODE Peaks] -->|download_encode.py| D(data/raw/encode_peaks.bed)
    E[GENCODE TSS] -->|download_encode.py| F(data/raw/gene_coords.bed)

    B -->|preprocess.py| G(data/processed/filtered_expression.csv)
    G -->|preprocess.py| H(data/processed/imputed_expression.csv)
    G -->|preprocess.py| I(data/processed/normalized_counts.csv)
    D -->|preprocess.py| J(data/processed/normalized_peaks.csv)
    J & F -->|preprocess.py| K(data/processed/binned_matrix.csv)
    K -->|preprocess.py| L(data/processed/selected_bins.txt)

    H & K -->|train.py| M(models/elastic_net_*.pkl)
    M -->|train.py| N(data/processed/cv_scores.json)

    K -->|analyze.py| O(data/processed/feature_importance.csv)
    O -->|analyze.py| P(data/processed/sc003_enrichment.json)
    H -->|analyze.py| Q(data/processed/housekeeping_r2.csv)
    Q -->|analyze.py| R(data/processed/performance_gap.csv)
    M & N & O & Q & R -->|generate_report.py| S(paper/results.md)
```

All intermediate files are checksum‑verified before downstream steps begin.

---


