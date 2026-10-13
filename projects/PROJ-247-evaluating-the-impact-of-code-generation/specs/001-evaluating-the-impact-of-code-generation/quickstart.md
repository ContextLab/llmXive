# Quickstart: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## Prerequisites
- **Python 3.11+**
- **GitHub Personal Access Token** with `repo` scope (to avoid unauthenticated rate limits).  
- Minimum **8 GB RAM** and **10 GB free disk**.  
- `git` installed and available in `$PATH`.

## Repository Setup
```bash
git clone https://github.com/your-org/PROJ-247-evaluating-the-impact-of-code-generation.git
cd PROJ-247-evaluating-the-impact-of-code-generation
```

### Environment Variables
Create a `.env` file (you may copy from the provided example if it exists) and set:

```
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXX
DATA_PATH=./data
LOG_PATH=./logs
```

> **Note:** If a `.env.example` file is missing, the pipeline will generate a minimal one automatically with the required keys. Likewise, a default `logging.conf` is provided; if it is absent the script will fall back to a basic console logger.

### Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

### Run the Full Pipeline
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/code   # make internal modules importable
python code/main.py   # orchestrates all steps in order
```

The script executes the following sub‑scripts (each produces **deterministic** and **validation‑ready** output):

| Step | Script | Expected Output | ✔️ | Description |
|------|--------|-----------------|----|-------------|
| 1️⃣ Curation | `code/01_data_curation.py` | `data/raw/repo_list.csv` and `data/raw/repo_metadata.csv` | ✅ | Shallow clones and metadata recorded |
| 2️⃣ Extraction | `code/02_code_block_extraction.py` | `data/processed/tagged_blocks.csv` (after classification) | ✅ | Extraction + radon + CodeBERT |
| 3️⃣ Classification | `code/03_classification.py` | `data/processed/tagged_blocks.csv` (with labels) | ✅ | ONNX CodeBERT inference |
| 4️⃣ Matching | `code/04_matching.py` | `data/processed/matched_pairs.csv` | ✅ | Propensity‑score matching |
| 5️⃣ Metrics | `code/05_metrics_extraction.py` | `data/processed/metrics_per_pair.csv` | ✅ | Churn & latency per pair |
| 6️⃣ Maintenance Events | `code/06_maintenance_events.py` | `data/processed/maintenance_events.csv` | ✅ | Individual churn/bug‑fix records |
| 7️⃣ Analysis | `code/07_analysis.py` | `data/analysis/wilcoxon_results.json`, `data/analysis/figures/*.png` | ✅ | Statistical tests, effect sizes, plots |
| 8️⃣ Ground‑Truth | `code/06_ground_truth.py` (optional) | `data/ground_truth/manual_labels.csv` | ✅ | Manual verification sample ≥ 100 blocks |
| 9️⃣ Logging | `code/utils/config.py` (loads `logging.conf`) | Console or file logs per run | ✅ | Ensures reproducible logging |

### Validation
Run the contract tests to ensure all files match their schema:

```bash
pytest tests/contract/
```

All tests must pass before proceeding to paper writing.

### Troubleshooting
- **Rate‑limit errors** – If you see `403` responses, wait a few minutes or increase the token’s rate‑limit quota. The script automatically backs off and retries.  
- **Memory errors** – Reduce `MAX_REPOS` in `config.py` to process fewer repositories at a time.  
- **Model download failure** – The first run downloads the ONNX model (hundreds of MB); ensure internet connectivity; the file is cached under `code/models/`.  

---



