# Quickstart: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM (for streaming)
- Access to Hugging Face (for dataset download)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This installs `rpy2`, `biom-format`, `datasets`, and `zCompositions` (via R).*

## Running the Pipeline

### 1. Data Ingestion & Harmonization
Download and preprocess data from AGP/UKBB (or fallback):
```bash
python -m src.ingestion.harmonize --cohort all
```
*Output*: `data/harmonized_data.csv`

### 2. Preprocessing (Imputation & CLR)
Handle missing data (exclude >20%, impute rest) and apply CLR transformation (Bayesian replacement):
```bash
python -m src.preprocessing.clr_transform --input data/harmonized_data.csv --method bayesian
```
*Output*: `data/analysis_matrix.csv`, `data/covariate_log.json`

### 3. Association Analysis
Run Spearman ρ (Primary) and Beta (Secondary) for correlation between fiber and taxa:
```bash
python -m src.analysis.association --input data/analysis_matrix.csv --covariates age,bmi,sex,antibiotic_use
```
*Output*: `results/association_results.tsv`

### 4. Differential Abundance (Primary: Relative Quartiles)
Run ANCOM-II and DESeq for High (Top 25th percentile) vs. Low (Bottom 25th percentile) fiber groups:
```bash
python -m src.analysis.differential --input data/analysis_matrix.csv --method ancom --method deseq2 --group-method quartile
```
*Output*: `results/diff_abundance_ancom.tsv`, `results/diff_abundance_deseq2.tsv`

### 5. Differential Abundance (Sensitivity: Absolute Thresholds)
Run ANCOM-II and DESeq2 for High (>30g/day) vs. Low (<15g/day) fiber groups as a secondary sensitivity analysis:
```bash
python -m src.analysis.differential --input data/analysis_matrix.csv --method ancom --method deseq2 --threshold-high 30 --threshold-low 15
```
*Output*: `results/diff_abundance_ancom_sensitivity.tsv`, `results/diff_abundance_deseq2_sensitivity.tsv`

### 6. Cross-Cohort Validation & Reporting
Aggregate results and check replication (requires significance in both):
```bash
python -m src.reporting.summary --ancom results/diff_abundance_ancom.tsv --deseq2 results/diff_abundance_deseq2.tsv
```
*Output*: `results/final_report.md`, `results/replication_table.csv`

## Verification

- **Contract Test**: Run `pytest tests/contract/` to validate output schemas.
- **Reproducibility**: Re-run the pipeline; checksums in `data/` should match.
