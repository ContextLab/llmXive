# Quickstart: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## Prerequisites
- **Python 3.11+**
- **GitHub Personal Access Token** with `repo` scope (to avoid unauthenticated rate limits).  
- Minimum **8 GB RAM** and **Sufficient free disk space (e.g., on the order of several gigabytes).**.  
- `git` installed and available in `$PATH`.

## Repository Setup
```bash
git clone 
cd PROJ-247-evaluating-the-impact-of-code-generation
```

### Environment Variables
Create a `.env` file (you may copy from the provided example) and set:

```
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXX
DATA_PATH=./data
LOG_PATH=./logs
```

> **Note:** The repository now includes a **`.env.example`** file defining the required keys (`GITHUB_TOKEN`, `DATA_PATH`, `LOG_PATH`). If it is missing, create it manually with the three variables above.

> **Logging Configuration:** The pipeline expects a logging configuration file at `code/config/logging.yaml`. Ensure this file exists (it is included in the `code/config/` directory) or create a minimal YAML logger if you customize the setup.

### Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

### Run the Full Pipeline
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/code   # make internal modules importable
source .env.example && python code/main.py --stage quickstart   # orchestrates all steps in order
```

The script executes the following sub‑scripts (each produces deterministic, validated output):

| Step | Script | Expected Output | Description |
|------|--------|-----------------|-------------|
| 1️⃣ A‑priori Power Analysis | `code/00_power_analysis.py` | `state/power_analysis.json` | Determines required ≥ 300 matched pairs (adjusted for censoring) |
| 2️⃣ Repository Curation | `code/01_data_curation.py` | `data/raw/repo_list.csv`, `data/raw/repo_metadata.csv` | Shallow clones & repo metadata |
| 3️⃣ Block Extraction | `code/02_code_block_extraction.py` | `data/processed/raw_blocks.csv` (intermediate) | Parses `.py`/`.js` files |
| 4️⃣ Static Metrics & Classification | `code/03_classification.py` | `data/processed/tagged_blocks.csv` | `radon` metrics + CodeBERT labeling |
| 5️⃣ Ground‑Truth Verification | `code/04_ground_truth.py` | `data/ground_truth/manual_labels.csv` | Random ≥ 100‑block manual labeling |
| 6️⃣ Propensity‑Score Matching | `code/05_matching.py` | `data/processed/matched_pairs.csv` | Logistic regression & 1:1 NN |
| 7️⃣ Longitudinal Metrics | `code/06_metrics_extraction.py` | `data/processed/metrics_per_pair.csv`, `data/processed/maintenance_events.csv` | Churn, normalized churn_rate, latency (extended‑term & 3‑mo) |
| 8️⃣ Statistical Analysis | `code/07_analysis.py` | `data/analysis/wilcoxon_results.json`, `data/analysis/figures/*.png` | Survival analysis for latency, within‑repo paired permutation for churn, BY correction |
| 9️⃣ Logging & Config | `code/utils/config.py` | Console or file logs under `logs/` | Ensures reproducibility |

### Validation
Run the contract tests to ensure all files match their schema:

```bash
pytest tests/contract/
```

All tests must pass before proceeding to manuscript writing.

### Troubleshooting
- **Rate‑limit errors** – If you see `403` responses, wait a few minutes or increase the token’s rate‑limit quota. The script automatically backs off and retries.  
- **Memory errors** – Reduce `MAX_REPOS` in `config.py` to process fewer repositories at a time.  
- **Model download failure** – The first run downloads the ONNX model (hundreds of MB); ensure internet connectivity; the file is cached under `code/models/`.  

---