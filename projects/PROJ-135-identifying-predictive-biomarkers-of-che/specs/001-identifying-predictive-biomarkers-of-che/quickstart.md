# Quickstart: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## Prerequisites

- Python 3.11 or higher.
- `pip` package manager.
- Unix‑like environment (Linux/macOS).
- ≥ 14 GB free disk space.

## Installation

```bash
git clone <repo-url>
cd <project-dir>
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Edit `src/config.py` to set:
- `RANDOM_SEED`: Fixed seed for reproducibility.
- `MAX_VARIANCE_GENES`: Number of top variable genes to retain (default 50).
- `TCGA_PROJECTS`: List of TCGA project IDs you wish to query (e.g., `["OV", "BRCA", "LUAD"]`). The pipeline will enforce ≥3 successful projects.
- `GEO_ACCESSIONS`: List of GEO accession numbers with chemotherapy response annotations (e.g., `["GSE25055", "GSE42752"]`). If none are available, the pipeline will skip external validation and note the limitation.

## Running the Pipeline

1. **Data Acquisition**
   ```bash
   python src/cli.py fetch --data-dir data/raw
   ```
   *Creates* `data/raw/` and `data/feasibility_gate.json`. The gate will halt with status `"halted"` if < 3 TCGA tumor types or required GEO datasets are missing.

2. **Preprocessing**
   ```bash
   python src/cli.py preprocess --input-dir data/raw --output-dir data/processed
   ```
   *Outputs* normalized matrices, batch‑corrected data, and `data/feasibility_gate.json` (updated).

3. **Feasibility Check**
   ```bash
   python src/cli.py gate --data-dir data/processed
   ```
   *Halts* if the feasibility gate reports `status: "halted"`; otherwise proceeds.

4. **Discovery & Meta‑Analysis**
   ```bash
   python src/cli.py analyze --mode discovery --data-dir data/processed --output-dir results/meta_analysis
   ```
   *Produces* `results/meta_analysis/gene_panel.json`.

5. **Modeling & Validation**
   ```bash
   python src/cli.py model --data-dir data/processed --panel results/meta_analysis/gene_panel.json --output-dir results
   ```
   *Generates* `results/metrics.json`, `results/summary.md`, `results/runtime_metrics.json`.

## Verification

```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: Reduce `MAX_VARIANCE_GENES` in `config.py`. |
- **Missing GEO Data**: The pipeline will automatically skip external validation and set `external_validation_status: "skipped"` in `results/summary.md`. |
- **Runtime Timeout**: Pipeline logs a warning if runtime > 5 h; consider reducing CV folds or gene panel size.
