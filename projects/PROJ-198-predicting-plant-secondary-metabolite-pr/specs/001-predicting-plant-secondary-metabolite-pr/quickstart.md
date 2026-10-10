# Quickstart: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Prerequisites

- Python 3.11+  
- Git  
- Access to NCBI RefSeq and MetaboLights (no API key required; respect rate limits).  
- **antiSMASH 7.0** – either Docker installed (preferred) or a local installation on the PATH.  
- Genomes > 500 MB will be automatically skipped.

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repository-url>
   cd projects/PROJ-198-predicting-plant-secondary-metabolite-pr
   ```

2. **Create a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r code/requirements.txt
   ```

4. **(Optional) Install antiSMASH**  
   - With Docker (recommended): no further action.  
   - Locally: follow https://docs.antismash.secondarymetabolites.org/ and ensure `antismash` is on your PATH.

## Running the Pipeline

### 1. Configuration
Edit `config/species_list.yaml` to list the plant species you wish to analyze.

```yaml
species:
  - "Arabidopsis thaliana"
  - "Oryza sativa"
  - "Solanum lycopersicum"
  # add more …
```

### 2. Data Download & Alignment
```bash
python code/cli/main.py --step download_and_align
```
*Downloads genomes, runs antiSMASH, fetches metabolite tables, harmonizes identifiers, and writes `data/processed/aligned_matrix.csv`. Zero‑BGC rows are **preserved** as valid entries.*

### 3. Model Training & Evaluation
```bash
python code/cli/main.py --step train_and_evaluate
```
*Performs PCA (if needed), runs LOO CV (for N < 20) or 5‑Fold CV (for N ≥ 20), trains RF, Elastic Net, Gradient Boosting, and PGLS, runs the phylogenetic permutation baseline **after** model training, and writes `data/processed/model_metrics.json` (the SSoT artifact).*

### 4. View Results
- `data/processed/aligned_matrix.csv` – Input matrix.  
- `data/processed/model_metrics.json` – **Single Source of Truth** for R², Pearson r, p‑values, CV method, and feature importances.  
- `data/processed/sensitivity_analysis.csv` – Threshold sweep outcomes.

## Sensitivity Sweep Enforcement

The pipeline will **abort with a non‑zero exit code** if the maximum absolute R² variation across the BGC‑threshold sweep exceeds **0.05** (fulfilling SC‑002). This ensures robustness is a hard requirement.

## Testing

```bash
pytest tests/
```

## Sub‑set Run (CI validation)

```bash
python code/cli/main.py --step download_and_align --limit 5
```
*Runs the pipeline on an initial set of species to verify the 30‑minute CI constraint.*

## Troubleshooting

- **antiSMASH timeout** – Species exceeding the time limit are logged and excluded.  
- **Missing metabolite data** – Species lacking metabolite tables are excluded; see `data/interim/alignment_warnings.log`.  
- **Memory errors** – Reduce the number of species or increase swap space.  
- **Small N** – If fewer than 20 species remain after filtering, LOO CV is automatically selected.  
