# Quickstart: Phenomenological AI: First-Person Experience Modeling

## Prerequisites

- Python 3.11+
- Sufficient RAM (for `TinyLlama-1.1B` via GGUF)
- CPU-only environment (no GPU required)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd projects/PROJ-592-phenomenological-ai-first-person-experie
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

## Running the Pipeline

### 1. Generate Reports
Execute the generation script. This will run `TinyLlama-1.1B` (CPU-safe).
*Note: Larger models are excluded from the automated pipeline due to RAM constraints. Use `code/generation/runner_local.py` for local 7B inference if you have ≥16GB RAM.*
```bash
python code/main.py --task generate --config code/config.py
```
*Output*: `data/raw/generations.jsonl` (Target: A sufficiently large sample size to ensure statistical power and representativeness.)

### 2. Generate Control Corpus
Generate the control set for discriminant validity.
```bash
python code/main.py --task generate_control --config code/config.py
```
*Output*: `data/raw/control_corpus.jsonl`

### 3. Select Validation Sample
Automatically select a representative subset of reports per condition for human rating (SC-002).
```bash
python code/main.py --task select_validation_sample --config code/config.py
```
*Output*: `data/qualitative/sampling_ids.csv`

### 4. Compute Metrics
Run the analysis pipeline.
```bash
python code/main.py --task analyze
```
*Output*: `data/processed/validity_scores.csv`, `data/processed/metrics.csv`

### 5. Human Validation (Manual Step)
1. Open `data/qualitative/rating_sheet_template.csv`.
2. Distribute to raters (blind to strategy/model).
3. Collect ratings and save to `data/qualitative/ratings_collected.csv`.
4. Run reliability check:
 ```bash
 python code/main.py --task validate_human
 ```

### 6. Statistical Analysis
Run the final statistical tests (ANOVA, FDR, Tukey HSD).
```bash
python code/main.py --task stats
```
*Output*: `data/processed/statistical_results.json`

### 7. Sensitivity Analysis (κ Thresholds)
Automate the sensitivity analysis across κ thresholds {0.5, 0.6, 0.7} (FR-011).
```bash
python code/main.py --task sensitivity-kappa
```
*Output*: `data/processed/sensitivity_kappa.csv`

## Reproducibility

To reproduce the exact results:
1. Set `SEED=42` in `code/config.py`.
2. Ensure `data/raw/generations.jsonl` matches the checksum in `state/...yaml`.
3. Run `python code/main.py --task full-pipeline`.

## Troubleshooting

- **OOM Error**: If the script crashes with "Out of Memory", check that you are not attempting to run 7B models in the CI environment. The pipeline uses `TinyLlama-1.1B` by default.
- **NLI Timeout**: Warnings are logged; the pipeline continues.
- **Low Cohen's κ**: The script will output a warning and flag the condition for re-evaluation.
