# Quickstart: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Prerequisites
- Python 3.11+
- Git
- Internet access (to download Hugging Face datasets)
- R (≥ 4.2) with packages `Maaslin2`, `ANCOMII`, `DESeq2`, `zCompositions` (installed automatically via `rpy2` when running the pipeline)

## Installation
```bash
# 1. Clone the repository
git clone <repo-url>
cd <project-dir>

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt
```

## Execution Steps
1. **Data Ingestion & Harmonization**  
   ```bash
   python -m src.ingestion.unified_loader --cohorts AGP UKBB
   ```
   *Creates* `data/harmonized_data.csv` (checksum logged). If a cohort lacks the required variables (`fiber_intake_g`, `age`, `bmi`, `sex`, `antibiotic_use`, `batch`), it is skipped and a warning is shown; the pipeline will continue with any remaining cohort.

2. **Covariate Cleaning & Imputation**  
   ```bash
   python -m src.preprocessing.covariate_handler --input data/harmonized_data.csv
   ```
   *Outputs* `data/cleaned_data.csv`.

3. **CLR Transformation (for Spearman only)**  
   ```bash
   python -m src.preprocessing.clr_transform --input data/cleaned_data.csv --method bayesian
   ```
   *Outputs* `data/analysis_matrix_clr.csv`.

4. **Association Analysis**  
   - **Spearman correlation (CLR matrix)**  
     ```bash
     python -m src.analysis.association --matrix data/analysis_matrix_clr.csv \
         --mode spearman
     ```
   - **MaAsLin2 linear model (raw counts)**  
     ```bash
     python -m src.analysis.association --matrix data/analysis_matrix_counts.csv \
         --mode maaslin2 --covariates age,bmi,sex,antibiotic_use,batch
     ```
   *Outputs* `results/association_results.tsv`.

5. **Differential Abundance (High vs Low Fiber)**  
   ```bash
   python -m src.analysis.differential --matrix data/analysis_matrix_counts.csv \
       --group-method quartile --methods ANCOM-II DESeq2
   ```
   *Outputs* `results/diff_ancom.tsv` and `results/diff_deseq2.tsv`.

6. **Power & Sensitivity Analyses**  
   ```bash
   python -m src.preprocessing.power_analysis --results results/association_results.tsv
   python -m src.analysis.association --matrix data/analysis_matrix_clr.csv \
       --mode spearman --categorical-fiber
   ```
   *Outputs* `results/power_report.txt` and sensitivity tables.

7. **Cross‑Cohort Validation & Summary Report**  
   ```bash
   python -m src.reporting.summary \
       --assoc results/association_results.tsv \
       --diff-ancom results/diff_ancom.tsv \
       --diff-deseq2 results/diff_deseq2.tsv
   ```
   *Outputs* `results/final_report.md` and `results/replication_table.csv`.

## Verification
```bash
# Contract validation
pytest tests/contract/
```
All tests must pass; failures indicate schema mismatches.

## Reproducibility Checks
- Re‑run the entire pipeline; checksums in `data/` must match the previous run.
- Random seeds are fixed in `src.utils.config`; no stochastic variation beyond what is explicitly seeded.

---


