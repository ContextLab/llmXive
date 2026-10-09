# Quickstart: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## Prerequisites
- Python 3.11 or newer
- Git
- Internet access (to download the IAT dataset)
- ≤ 7 GB RAM, 2 CPU cores (GitHub Actions free tier) or a local machine with similar specs

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r code/requirements.txt
   # Ensure the extra index URL for CPU‑only PyTorch wheels:
   # (pip will read code/pip.conf automatically)
   ```

## Running the Full Pipeline

All steps are invoked via the CLI entry point `code/main.py`. The `--step` flag selects a stage; the pipeline can be run step‑by‑step or in one shot.

```bash
# 1️⃣ Ingest raw data
python code/main.py --step ingest

# 2️⃣ Preprocess & derive missing scores
python code/main.py --step preprocess

# 3️⃣ Fit the linear mixed‑effects model
python code/main.py --step model

# 4️⃣ Generate the PDF report
python code/main.py --step report
```

**One‑shot execution** (runs all steps in order):
```bash
python code/main.py --run-all
```

### Expected Outputs
| Step | File(s) Produced |
|------|------------------|
| `ingest` | `data/raw/iat.parquet`, `data/processed/ingest_metrics.json` |
| `preprocess` | `data/processed/linked_trials.csv`, `state/vif_flag.json`, `config/analysis_params.json` |
| `model` | `state/model_results.pkl`, `state/model_convergence_metrics.json`, `state/model_diagnostics.json` |
| `report` | `reports/final_report.pdf`, `reports/sensitivity_analysis.csv`, `reports/pii_scan.json` |
| Logging | `code/logs/pipeline.log` (created automatically by Task T009) |

## Verification Checklist
- **Log file**: `code/logs/pipeline.log` should contain timestamps for each task.  
- **Schema validation**: Run `pytest -m contract` to ensure all JSON/YAML contracts pass.  
- **PDF completeness**: Open `reports/final_report.pdf` and confirm it contains the interaction plot, coefficient table, and sensitivity‑analysis summary (SC‑003).  
- **Power flag**: If the dataset after filtering is < 300 trials, the PDF will contain a “Power Limitation” note.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| `Data Gap: Image files missing for >10% of trials` | Source dataset missing many stimulus files | Verify the OSF image repository URL; if the gap persists, the pipeline halts as required (US‑1). |
| `Model convergence failure` | Complex random‑effects structure or collinearity | Check `state/vif_flag.json`; if VIF > 5, simplify the model or drop the interaction (Task T014 fallback). |
| `CUDA error` | Valence derivation attempted GPU but no GPU available | The pipeline will automatically retry on CPU; if still too slow, the step aborts with a clear message. |
| Missing `pipeline.log` | Logging configuration not executed | Ensure Task T009 ran (it occurs early in the pipeline). |

---
