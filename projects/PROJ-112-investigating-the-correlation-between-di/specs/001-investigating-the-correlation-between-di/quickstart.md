# Quickstart: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Prerequisites
- Python 3.11+
- Git
- Internet access (to download AGP, optional UKBB, and helper datasets)
- R ≥ 4.2 with packages `Maaslin2`, `ANCOMII`, `DESeq2`, `zCompositions` (installed automatically via `rpy2` when the pipeline runs)

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

## Prepare Your Data
1. **American Gut Project** data will be downloaded automatically to `data/raw/agp/` from the public FTP mirror.  
2. **UK Biobank** gut‑microbiome data will be attempted from its open portal; if unavailable, a warning is logged and the pipeline proceeds with AGP only.  
3. If you wish to use a custom open dataset, place the CSV/BIOM files inside `data/user_dataset/`. The dataset **must** contain the required columns listed in the research plan.  

## Execution Steps
1. **Data Ingestion & Cohort Download**  
   ```bash
   python -m src.ingestion.agp_loader
   python -m src.ingestion.ukbb_loader   # may log a warning if not accessible
   ```
   *Creates* `data/raw/` files and records SHA‑256 checksums.

2. **Harmonization & QC**  
   ```bash
   python -m src.preprocessing.harmonize --input-dir data/raw/
   ```
   *Outputs* `data/harmonized_data.csv`.

3. **Covariate Cleaning & Imputation**  
   ```bash
   python -m src.preprocessing.covariate_handler --input data/harmonized_data.csv
   ```
   *Outputs* `data/cleaned_data.csv`.

4. **CLR Transformation (for Spearman & MaAsLin2)**  
   ```bash
   python -m src.preprocessing.clr_transform --input data/cleaned_data.csv --method bayesian
   ```
   *Outputs* `data/analysis_matrix_clr.csv`.

5. **Association Analyses**  
   - **Partial Spearman (covariate‑adjusted)**  
     ```bash
     python -m src.analysis.association --matrix data/analysis_matrix_clr.csv --mode spearman_partial
     ```
   - **MaAsLin2 Linear Model on CLR data**  
     ```bash
     python -m src.analysis.association --matrix data/analysis_matrix_clr.csv \
         --mode maaslin2 --covariates age,bmi,sex,antibiotic_use,batch
     ```
   - **Merged Results** (matches `correlation_result.schema.yaml`)  
     ```bash
     python -m src.analysis.association --merge-results
     ```
   *Outputs* `results/association_combined.tsv`.

6. **Differential Abundance (High vs Low Fiber)**  
   ```bash
   python -m src.analysis.differential --matrix data/analysis_matrix_clr.csv \
       --group-method quartile --methods ANCOM-II DESeq2
   ```
   *Outputs* `results/diff_ancom.tsv` and `results/diff_deseq2.tsv`.

7. **Measurement‑Error Simulation (Synthetic Truth)**  
   ```bash
   python -m src.analysis.measurement_error --synthetic --beta 0.1 --error-sd 0.10
   ```
   *Outputs* `results/measurement_error_bias.tsv`.

8. **Power & Sensitivity Analyses**  
   ```bash
   python -m src.preprocessing.power_analysis --mode spearman \
       --target-beta 0.1 --alpha 0.05 --power 0.80
   python -m src.preprocessing.power_analysis --mode linear \
       --target-beta 0.1 --alpha 0.05 --power 0.80
   ```
   *Outputs* `results/power_report.txt`. If the smaller cohort fails the a priori sample‑size target, the script halts with FR‑013 warning.

9. **Cross‑Cohort Validation & Summary Report**  
   ```bash
   python -m src.reporting.summary \
       --assoc results/association_combined.tsv \
       --diff-ancom results/diff_ancom.tsv \
       --diff-deseq2 results/diff_deseq2.tsv \
       --me-bias results/measurement_error_bias.tsv
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


