# Quickstart: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Prerequisites
- Python 3.11+ and `git`.
- Docker (required for antiSMASH 7.0) **or** a locally installed antiSMASH binary on the PATH.
- Internet access to NCBI RefSeq and MetaboLights (no API keys needed).
- Genomes larger than 500 MB will be automatically skipped.

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd projects/PROJ-198-predicting-plant-secondary-metabolite-pr

# 2. Set up a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r code/requirements.txt
```

## Step‑by‑Step Pipeline

### 1. Configure Species List
Edit `config/species_list.yaml` to contain the scientific names you wish to analyze:

```yaml
species:
  - "Arabidopsis thaliana"
  - "Oryza sativa"
  - "Solanum lycopersicum"
  # add additional species here
```

### 2. Download & Align Data
```bash
python code/cli/main.py --step download_and_align
```
- Downloads genomes from NCBI RefSeq.
- Retrieves metabolite tables from MetaboLights/PMDB.
- Runs antiSMASH 7.0 (Docker) on each genome.
- Produces `data/processed/aligned_matrix.csv`.  
- Zero‑BGC rows are **kept**; species missing either modality are excluded with a logged warning.

### 3. Train Models & Evaluate
```bash
python code/cli/main.py --step train_and_evaluate
```
- Performs optional PCA (if needed).
- Trains Random Forest, Elastic Net, Gradient Boosting, and PGLS.
- Executes LOO CV (N < 20) or 5‑Fold CV (N ≥ 20).
- Runs the phylogenetic permutation baseline.
- Writes `data/processed/model_metrics.json` (the SSoT) and `data/processed/sensitivity_analysis.csv`.

### 4. Review Results
- `data/processed/aligned_matrix.csv` – feature‑target matrix.  
- `data/processed/model_metrics.json` – all performance metrics, feature importances, CV method.  
- `data/processed/sensitivity_analysis.csv` – threshold sweep outcomes; pipeline aborts if max |ΔR²| > 0.05 (SC‑002).  

### 5. Run a Sub‑set (CI Validation)
```bash
python code/cli/main.py --step download_and_align --limit 5
```
Executes the pipeline on the first five species to verify the 30‑minute CI time‑budget (User Story 1 independent test).

## Testing
```bash
pytest tests/
```
All tests include contract validation against the JSON schemas.

## Troubleshooting
- **antiSMASH timeout** – Species exceeding the time limit are logged and omitted.  
- **Missing metabolite data** – Check `data/interim/alignment_warnings.log` for species excluded.  
- **Memory errors** – Reduce the number of species or increase swap space on the runner.  
- **Small N** – If fewer than 20 species remain after filtering, LOO CV is automatically selected.

---
