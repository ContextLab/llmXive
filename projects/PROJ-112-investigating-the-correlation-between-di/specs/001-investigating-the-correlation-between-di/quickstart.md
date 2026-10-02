# Quickstart: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Prerequisites

- Python 3.11+
- R 4.3+ (with `Maaslin2`, `ANCOMBC`, `DESeq2` packages)
- `pip` and `conda` (or `venv`)
- Access to GitHub Actions runner (2 CPU, 7GB RAM) or local equivalent.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install R packages** (if running locally):
   ```r
   install.packages(c("Maaslin2", "ANCOMBC", "DESeq2", "BiocManager"))
   BiocManager::install(c("Maaslin2", "ANCOMBC", "DESeq2"))
   ```

## Running the Pipeline

### 1. Data Ingestion (Phase 1)
The pipeline will attempt to download AGP and UKBB data. If access is blocked, it will fall back to an open substitute.

```bash
python src/main.py --phase ingestion
```

- **Output**: `data/raw/` (checksummed), `data/processed/harmonized.tsv`.
- **Note**: If data is unavailable, the pipeline will halt with a clear error message.

### 2. Preprocessing & Transformation (Phase 2)
Filters samples, harmonizes units, applies CLR transformation.

```bash
python src/main.py --phase preprocessing
```

- **Output**: `data/processed/clr_transformed.tsv`, `data/processed/exclusion_log.tsv`.

### 3. Statistical Analysis (Phase 3)
Runs MaAsLin2, ANCOM-II, and DESeq2.

```bash
python src/main.py --phase analysis
```

- **Output**: `data/processed/association_results.tsv`, `data/processed/diff_abundance_results.tsv`.

### 4. Cross-Cohort Validation (Phase 4)
Compares results between AGP and UKBB.

```bash
python src/main.py --phase validation
```

- **Output**: `data/processed/validation_results.tsv`.

### 5. Final Summary (Phase 5)
Generates summary tables and power analysis.

```bash
python src/main.py --phase summary
```

- **Output**: `data/processed/summary.tsv`, `data/processed/power_analysis.tsv`.

## Running Tests

```bash
pytest tests/ -v
```

- **Unit Tests**: `tests/unit/` (parsing, filtering, CLR).
- **Integration Tests**: `tests/integration/` (end-to-end on synthetic data).
- **Contract Tests**: `tests/contract/` (schema validation).

## Troubleshooting

- **Data Download Failed**: Check if AGP/UKBB are accessible. If not, the pipeline will use the open substitute. Ensure `datasets` library is up to date.
- **Memory Error**: Ensure streaming is enabled (`datasets.load_dataset(..., streaming=True)`). Reduce sample size if necessary.
- **R Package Errors**: Verify R packages are installed and `rpy2` is configured correctly.
- **PII Detected**: The pipeline will halt. Check `data/raw/` for PII and redact or exclude.

## Output Artifacts

- `data/processed/harmonized.tsv`: Cleaned, harmonized data.
- `data/processed/clr_transformed.tsv`: CLR-transformed abundances.
- `data/processed/association_results.tsv`: MaAsLin2 results.
- `data/processed/diff_abundance_results.tsv`: ANCOM-II/DESeq2 results.
- `data/processed/validation_results.tsv`: Cross-cohort replication status.
- `data/processed/summary.tsv`: Final summary (median fiber, power).