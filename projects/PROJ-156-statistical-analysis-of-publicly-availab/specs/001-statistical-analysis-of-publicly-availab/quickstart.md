# Quickstart: Statistical Analysis of Speedrun Data

## 1. Prerequisites
- Python 3.11+  
- `git`  
- Access to a GitHub Actions runner (or a comparable local Linux environment)

## 2. Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-156-statistical-analysis-of-publicly-availab

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 3. Configuration
Edit `code/config.yaml` to list the target games and optional difficulty file:

```yaml
games:
  - "super-mario-64"
  - "celeste"
  - "hollow-knight"
  # add up to 15 games
difficulty_source: "data/external/difficulty_labels.csv"   # optional; set to null if unavailable
random_seed: 42
```

- `difficulty_source` should point to a **public CSV** with columns `game_id` and `difficulty_label`. If no verified public source exists, leave the field as `null`; games without a difficulty label will be omitted from difficulty‑modulation analyses (as described in the research plan).

## 4. Run the Full Pipeline

| Step | Command | Output |
|------|---------|--------|
| **1️⃣ Data acquisition** | `python code/scripts/fetch_data.py` | `data/raw/speedrun_api.json` + per‑game checkpoints |
| **2️⃣ Preprocessing** | `python code/scripts/preprocess.py` | `data/processed/run_records.csv` |
| **3️⃣ Distribution fitting** | `python code/scripts/fit_distributions.py` | `data/processed/distribution_fits.csv` |
| **4️⃣ Mixed‑effects modeling** | `python code/scripts/fit_mixed_effects.py` | `data/processed/mixed_effects_results.csv` |
| **5️⃣ Report generation** | `python code/scripts/generate_report.py` | `paper/draft.md` |

Each script automatically loads checkpoints if a previous run was interrupted, allowing seamless resumption (FR‑012).

## 5. Testing & Validation
```bash
pytest code/tests/
```
- `test_preprocess.py` checks ≥ 95 % record retention and validates against `contracts/run_record.schema.yaml`.  
- `test_models.py` verifies model convergence, VIF ≤ 5, and schema compliance for `distribution_fits.csv` (`contracts/distribution_fit.schema.yaml`).

## 6. Troubleshooting
- **API rate limit** – the fetch script includes exponential back‑off; simply re‑run if it aborts.  
- **MemoryError** – reduce the number of games in `config.yaml`.  
- **Model non‑convergence** – check logs; optionally simplify the mixed‑effects formula via `config.yaml`.  
- **Missing checkpoint** – delete the partially‑written checkpoint file and re‑run the failing step; the script will restart from the last successful game.

## 7. Expected Artifacts
- `data/processed/run_records.csv` – cleaned dataset (entity **RunRecord**).  
- `data/processed/distribution_fits.csv` – per‑game distribution fit summary (entity **DistributionFit**).  
- `data/processed/mixed_effects_results.csv` – mixed‑effects coefficients and diagnostics (entity **ModelCoefficient**).  
- `paper/draft.md` – final report with associational interpretations only.  

---

