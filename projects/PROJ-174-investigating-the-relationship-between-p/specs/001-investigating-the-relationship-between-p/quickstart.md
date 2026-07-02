# Quickstart: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## 1. Prerequisites

- Python 3.11+
- Git
- ~10 GB free disk space (for raw data download)
- ~8 GB RAM (pipeline optimized for ≤ 6 GB)

## 2. Installation

1. **Clone the Repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-174-investigating-the-relationship-between-p
   ```

2. **Create Virtual Environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**  
   ```bash
   pip install -r code/requirements.txt
   ```

## 3. Data Acquisition

The pipeline automatically fetches the verified eye‑tracking datasets from OpenNeuro. Ensure an internet connection.

```bash
python code/utils.py --fetch-data
```

*The script will download ds001734, ds002642, and ds003663 into `data/raw/`. It verifies that each file contains the required columns (`pupil_diameter`, `timestamp`, and `target_salience` where available) before proceeding.*

## 4. Running the Full Pipeline

```bash
python code/main.py
```

### Configuration (config.yaml)

- `random_seed`: Fixed seed for reproducibility.  
- `thresholds`: `[0.01, 0.05, 0.10]` (decision thresholds for the classifier).  
- `salience_mode`: `strict` (must **skip** salience if missing; do not derive on‑the‑fly).  

## 5. Expected Outputs (all in `data/results/`)

| File | Description |
| :--- | :--- |
| `quality_report.csv` | Primary exclusion report (FR‑008) – counts of blink loss, timestamp errors, insufficient trials, etc. |
| `correlation_summary.csv` | Pearson r, raw & Holm‑Bonferroni‑adjusted p‑values, significance flag (SC‑001). |
| `model_summary.csv` | LME fixed effects, SE, p‑values, model type (Full or Reduced (Collinearity Handled)), and likelihood‑ratio test (SC‑002). |
| `classification_metrics.csv` | Accuracy, precision, recall, ROC‑AUC, `relative_decrease` across thresholds, and ground‑truth limitation note (SC‑003, SC‑004). |
| `ground_truth_limitation.txt` | Explicit statement that ground truth is derived from search‑time median split when no independent measure is present (FR‑011). |

## 6. Troubleshooting

- **Missing Salience Warning**: `WARNING: Target salience missing; skipping proxy` is expected if the dataset lacks the column. The pipeline will continue with the remaining proxies.  
- **MemoryError**: Reduce the optional `sample_fraction` in `config.yaml` to process a smaller subset of trials.  
- **Timestamp Errors**: Non‑monotonic timestamps will be dropped and reported in `quality_report.csv`.  
