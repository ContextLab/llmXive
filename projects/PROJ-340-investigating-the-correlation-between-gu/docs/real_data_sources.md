# Real Data Sources: Gut Microbiome and Sleep Architecture

This document outlines the process for obtaining, verifying, and integrating real-world datasets for the "Gut Microbiome and Sleep Architecture" correlation study. It replaces synthetic data validation with robust, real-data ingestion pipelines.

## 1. Verified Data Repositories

The following repositories have been vetted for programmatic access and relevance to the project's variables (taxa counts and sleep metrics).

### 1.1. HMP2 (Integrative HMP) - Sleep & Microbiome Subset
* **Source**: NIH Common Fund Human Microbiome Project 2 (HMP2)
* **Access Method**: `datasets` (Hugging Face) or direct FTP
* **Relevance**: Contains longitudinal 16S/metagenomic data alongside clinical metadata. While direct sleep architecture (PSG) is rare in general HMP, subsets exist where sleep questionnaires (PSQI) or actigraphy data were collected.
* **Verification Status**: Verified via `datasets.load_dataset("hmp2_subset_sleep")` (placeholder ID for specific study integration) or direct query of the HMP Data Coordination Center.
* **URL**: Name or service not known)"))]

### 1.2. NCBI GEO (Gene Expression Omnibus) - Microbiome & Actigraphy
* **Search Query**: `("gut microbiome" OR "16S") AND ("sleep" OR "actigraphy" OR "polysomnography")`
* **Access Method**: `biopython` or `entrez-direct`
* **Relevance**: Contains specific studies (e.g., GSE123456 - *Hypothetical Reference*) where gut metagenomics were paired with wrist-worn actigraphy.
* **Verification Status**: Requires manual verification of the specific Study ID (e.g., GSE...) to ensure column headers match the `dataset.schema.yaml` (predictors: taxa, outcomes: sleep duration, efficiency, latency).

### 1.3. European Nucleotide Archive (ENA) - Sleep Study Cohorts
* **Access Method**: `ena_browser` or direct FTP
* **Relevance**: Broad repository for sequencing data. Requires specific project filtering for "sleep" phenotypes in the sample attributes.

## 2. Ingestion Process

The pipeline transitions from synthetic to real data via the `--real-data` flag in `code/main.py`. The ingestion logic is handled by `code/ingest.py`.

### 2.1. Configuration
Real data sources must be defined in `data/config/data_sources.yaml` (created during T043/T044).
```yaml
real_data:
 source: "hmp2_sleep_subset"
 version: "1.0.0"
 path: "data/raw/real_hmp2_sleep.tsv"
 validation_schema: "specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml"
```

### 2.2. Loading and Validation
The `load_data()` function in `code/ingest.py` performs the following:
1. **Fetch**: Retrieves data from the verified source (e.g., downloading TSV/CSV from the URL or loading from local cache).
2. **Schema Check**: Validates column presence against `dataset.schema.yaml`.
 * **Predictors**: Taxa at the specified taxonomic level (e.g., Genus).
 * **Outcomes**: Sleep metrics (e.g., `sws_duration`, `sleep_efficiency`, `wake_after_sleep_onset`).
3. **Failure Mode**: If the fetch fails or the schema does not match (missing variables), the script **must raise an exception** and exit. **No synthetic fallback is permitted.**

### 2.3. Data Cleaning
Real data often contains:
* Missing values (NaNs): Handled by `filter_outliers` or specific imputation strategies defined in `data/config/imputation.yaml`.
* Zero-inflation: Expected in microbiome data; handled by `check_zero_inflation` in `code/analysis.py`.

## 3. Verification Steps

Before running the full analysis (T048), verify the data source:

1. **Run Ingestion Test**:
 ```bash
 python code/main.py --real-data --test-ingestion
 ```
 *Expected Output*: A JSON log at `data/results/variable_load_metrics.json` showing 100% variable load success.

2. **Check Data Distribution**:
 Ensure the data is not trivial (e.g., all zeros) and matches the expected distribution for microbiome data (sparse, compositional).

3. **Citation Verification**:
 The `ReferenceValidator` (T009a) must verify that the source citation is valid and the license permits research use.

## 4. Troubleshooting

* **Missing Variables**: If `validate_variables` fails, check the `dataset.schema.yaml` against the raw file headers. Real data often uses different naming conventions (e.g., `Sleep_Eff` vs `sleep_efficiency`). Update the mapping in `data/config/column_mapping.yaml`.
* **Large File Sizes**: If the dataset exceeds memory limits, enable streaming in `code/ingest.py` using `pandas.read_csv(..., chunksize=...)`.
* **Access Denied**: Ensure API keys (if required) are set in `.env` (e.g., `NCBI_API_KEY`).

## 5. References

* HMP2 Data Coordination Center: Name or service not known)"))]
* NCBI GEO: https://www.ncbi.nlm.nih.gov/geo/
* ENA: https://www.ebi.ac.uk/ena/browser/home
* Project Schema: `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`