# Quickstart: Statistical Analysis of Speedrun Data

## 1. Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to GitHub Actions runner (or local equivalent)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-156-statistical-analysis-of-publicly-availab

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Configuration

Edit `code/config.yaml` to specify:
- `games`: List of game IDs to analyze (10–15 games).
- `difficulty_source`: Path to external difficulty metadata (if available).
- `random_seed`: Integer for reproducibility.

Example:
```yaml
games:
  - "super-mario-64"
  - "celeste"
  - "hollow-knight"
  # ... add 10–15 games
difficulty_source: "data/external/difficulty_labels.csv"
random_seed: 42
```

## 4. Running the Pipeline

### Step 1: Data Acquisition
```bash
python code/scripts/fetch_data.py
```
Outputs: `data/raw/speedrun_api.json`

### Step 2: Preprocessing
```bash
python code/scripts/preprocess.py
```
Outputs: `data/processed/run_records.csv`

### Step 3: Distribution Fitting
```bash
python code/scripts/fit_distributions.py
```
Outputs: `data/processed/distribution_fits.csv`

### Step 4: Mixed-Effects Modeling
```bash
python code/scripts/fit_mixed_effects.py
```
Outputs: `data/processed/mixed_effects_results.csv`

### Step 5: Report Generation
```bash
python code/scripts/generate_report.py
```
Outputs: `paper/draft.md`

## 5. Verification

Run tests:
```bash
pytest code/tests/
```

Check data completeness:
```bash
python -c "import pandas as pd; df = pd.read_csv('data/processed/run_records.csv'); print(f'Completeness: {df.notna().mean().mean():.2%}')"
```

## 6. Troubleshooting

- **API Rate Limit**: Wait 60 seconds and re-run.
- **Model Non-convergence**: Check `code/config.yaml` for simpler model settings.
- **Memory Error**: Reduce number of games in `config.yaml`.
- **Checkpoint Resume**: If job times out, re-run; script detects checkpoints and resumes.

## 7. Output Artifacts

- `data/processed/run_records.csv`: Cleaned dataset.
- `data/processed/distribution_fits.csv`: Distribution fitting results.
- `data/processed/mixed_effects_results.csv`: Mixed-effects model coefficients.
- `paper/draft.md`: Final report with associational findings.
