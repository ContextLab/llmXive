# Quickstart: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Prerequisites

- Python 3.11+
- R 4.3+ (with `BiocManager`)
- `git`
- Access to American Gut Project (Qiita Study ID 10160) and UK Biobank (Fields 21003, 22012) data.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/001-investigating-the-correlation-between-di
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions to ensure CPU-only compatibility.*

4.  **Install R Dependencies**:
    ```bash
    Rscript -e 'if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")'
    Rscript -e 'BiocManager::install(c("Maaslin2", "mice", "phyloseq"))'
    ```

## Data Setup

1.  **Download Data**:
    - Download AGP 16S data from **Qiita Study ID 10160**.
    - Download UK Biobank 16S data and metadata (Fields 21003, 22012) from the UKBB portal.
    - Place files in `data/raw/`.
    - *Note: Ensure files contain `fiber_intake` and `read_depth` columns.*

2.  **Verify Checksums**:
    - Run `python src/utils/check_data.py` to verify data integrity (Constitution Principle III).

## Running the Pipeline

Execute the full pipeline:
```bash
python src/main.py --cohort all
```

**Steps performed**:
1.  **Ingestion**: Loads and harmonizes AGP (Qiita 10160) and UKBB data.
2.  **Filtering**: Removes samples with <5,000 reads or implausible fiber intake.
3.  **ID Generation**: Creates `SHA256` sample IDs for traceability.
4.  **Imputation**: Applies MICE for missing covariates.
5.  **Transformation**: Applies CLR transformation with pseudocount=1.
6.  **Analysis**: Runs MaAsLin2 for continuous association.
7.  **Validation**: Cross-cohort beta-coefficient comparison.
8.  **Output**: Generates summary tables in `data/processed/results/`.

## Expected Outputs

- `data/processed/merged_harmonized.tsv`: Cleaned input data with SHA256 IDs.
- `data/processed/results/correlation_maaslin2.tsv`: Association results.
- `data/processed/results/validation_summary.tsv`: Cross-cohort validation flags.

## Troubleshooting

- **Memory Error**: If `MemoryError` occurs, reduce the sample size by setting `--sample-ratio 0.5` in `main.py`.
- **Missing Columns**: Ensure downloaded datasets contain `fiber_intake` and `read_depth`. If not, the pipeline will exit with an error (FR-001).
- **R Package Install Failure**: Ensure R 4.3+ is installed and `BiocManager` is up to date.
