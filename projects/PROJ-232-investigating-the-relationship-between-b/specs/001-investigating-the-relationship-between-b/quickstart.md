# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Prerequisites
- Python 3.10 or newer
- Git
- ~ several GB free disk space (the three parquet files together are on the order of a few gigabytes.)
- No GPU required (all steps run on CPU)

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-232-investigating-the-relationship-between-b

# 2️⃣ Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Pipeline

### 0️⃣ Verify Data Availability & Generate Data‑Gap Report
```bash
python src/data/validate.py --check-only
```
- **Success**: Prints a summary of available columns. If a music‑related proxy column (e.g., `music_emotion_score`) is present, the script notes its name and the pipeline can continue.  
- **Failure**: If **neither** a BMRQ column nor any music‑related proxy column is found, `data_gap_report.md` is written indicating the missing variable(s) and the script exits with status 1. The primary BMRQ analysis cannot proceed.

### 1️⃣ Download Verified HCP Parquet Files
```bash
python src/data/download.py \
  --urls https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet \
        https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv \
        https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet \
  --out-dir data/
```
- Files are streamed, checksummed, and saved under `data/`.  

### 2️⃣ Reconstruct Connectivity Matrices
```bash
python src/analysis/graph_metrics.py --mode reconstruct --subjects all
```
- Reads the `fc_upper_tri` column, builds a 200 × 200 symmetric matrix per subject, and validates symmetry/diagonal.  

### 3️⃣ Compute Graph‑Theory Metrics
```bash
python src/analysis/graph_metrics.py --mode compute --subjects all
```
- Produces `results/network_metrics.csv` adhering to the `NetworkMetrics` schema.  

### 4️⃣ Statistical Analysis (Partial Correlation + Regularized Regression)
```bash
python src/analysis/stats.py \
  --behavioral-column <proxy_column_name> \
  --output results/analysis_results.csv
```
- If **no** proxy column is supplied (i.e., BMRQ and any music‑related column are absent), the script aborts after printing a warning (the primary BMRQ analysis is not possible).  
- The script computes per‑metric power (`power_achieved`) and writes it to `analysis_results.csv`.  

### 5️⃣ Visualization
```bash
python src/analysis/visualize.py \
  --input results/analysis_results.csv \
  --output-dir figures/
```
- Generates `scatter_predicted_vs_actual.png` (if a proxy is present) and `significant_metrics_bar.png`.  

### 6️⃣ Run Tests
```bash
pytest -v
```
- Includes contract validation (`tests/contract/test_schemas.py`) and unit checks for matrix properties.  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| `data_gap_report.md` mentions missing BMRQ | No verified BMRQ source; primary analysis cannot proceed. | Accept the report and run the exploratory analysis with any available proxy, or revise the research question. |
| `MemoryError` during matrix reconstruction | Too many subjects loaded simultaneously. | Use `--subjects 10` to process a subset for debugging. |
| `FileNotFoundError` for a parquet URL | URL typo or temporary network issue. | Verify the URL against the verified list; retry later. |
| `VIF > 5` warnings | Predictors highly collinear. | The pipeline automatically drops the highest‑VIF predictor; review `results/vif_report.json` for details. |
| CI job times out | Running full dataset on CI (exceeds 6 h). | CI is intended only for the **validation** run (`--subjects 1`). Full analyses should be run locally or on a cloud VM. |

---



