# Quickstart: The Role of Epigenetic Drift in Adaptive Landscape Exploration

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or a local environment with 2GB+ RAM.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd epigenetic-drift-project
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `requirements.txt` pins all versions to ensure reproducibility.*

## Running the Pipeline

### 1. Data Discovery (Phase 0)
Run the discovery script to verify dataset availability.
```bash
python code/main.py --stage discovery
```
- **Output**: `output/discovery_report.json`
- **Success**: Reports ≥3 valid matched datasets.
- **Failure**: Reports "Data Unavailable" and halts. **This is an expected outcome if the verified sources do not contain the required data.**

### 2. Preprocessing (Phase 1)
Download, normalize, and filter data. **Uses LOGO jackknife for variance calculation.**
```bash
python code/main.py --stage preprocess
```
- **Output**: `data/processed/unified_variance_matrix.csv`
- **Logs**: `logs/preprocess.log`

### 3. Correlation Analysis (Phase 2)
Compute Spearman's $\rho$ and run permutation tests. **Associational only.**
```bash
python code/main.py --stage analysis
```
- **Output**: `output/correlation_results.json`
- **Logs**: `logs/analysis.log`

### 4. Sensitivity & Visualization (Phase 3)
Run sensitivity sweep and generate plots.
```bash
python code/main.py --stage viz
```
- **Output**: `output/figures/scatter_plot.png`, `output/sensitivity_report.json`

## Verification

To ensure reproducibility:
1. Run `pytest tests/` to verify unit and contract tests.
2. Check `data/` checksums against `state/...yaml`.
3. Re-run `python code/main.py --stage all` on a fresh environment.

## Troubleshooting

- **Memory Error**: Ensure dataset size is within 2GB RAM limit. If so, the pipeline should automatically sample or filter genes.
- **Data Not Found**: If the discovery stage fails, check the `Verified datasets` list in `research.md` to confirm if the required matched datasets exist in the provided sources. **If not, the study is currently infeasible with these sources.**
- **Missing Metadata**: If "fluctuation timescale" is missing, the pipeline will flag the dataset as "insufficient temporal resolution" and exclude it from the final association claim.
