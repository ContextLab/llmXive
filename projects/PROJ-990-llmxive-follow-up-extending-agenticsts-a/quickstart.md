# Quick Start Guide: llmXive AgenticSTS Extension

This guide walks you through running the full research pipeline to reproduce the results of the Dynamic Policy experiment.

## 1. Environment Setup

Ensure you are using Python 3.11 or higher.

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Preparation

The pipeline expects raw trajectory logs in `data/raw/`.

- **Input**: `data/raw/trajectories.csv`
- **Schema**: Must contain `trajectory_id`, `turn`, `health`, `threat_level`, `deck_size`, `legal_moves`, `action`.

If you do not have raw data, ensure you have downloaded the AgenticSTS dataset and placed it in the correct directory. The pipeline will fail loudly if data is missing.

## 3. Running the Pipeline

Execute the pipeline tasks in the following order. Each script writes its output to `data/processed/` or `models/`.

### Step 1: Parse & Extract Metrics
```bash
python code/parser.py
python code/entropy.py
```
*Outputs*: `data/processed/turn_metrics.csv`, `data/processed/entropy_scores.csv`

### Step 2: Ablation Study (Ground Truth)
```bash
python code/ablation.py
python code/extractor.py
python code/validator.py
```
*Outputs*: `data/processed/ablation_labels_full.json`, `data/processed/utility_labels.csv`

### Step 3: Data Splitting & Model Training
```bash
python code/splitter.py
python code/classifier.py
```
*Outputs*: `data/processed/train_set.csv`, `data/processed/holdout_set.csv`, `models/layer_utility_classifier.pkl`

### Step 4: Validation (Proxy Check)
```bash
python code/classifier.py --mode validate
```
*Outputs*: `data/processed/proxy_validation_report.json`
*Constraint*: Exits with error if correlation < 0.7.

### Step 5: Simulation (Dynamic & Baselines)
```bash
python code/simulator.py --mode dynamic
python code/simulator.py --mode static
python code/simulator.py --mode random
```
*Outputs*: Logs in `data/processed/simulations/`

### Step 6: Aggregation & Statistics
```bash
python code/generate_baseline_comparison.py
python code/token_reduction_verifier.py
python code/generate_statistical_report.py
```
*Outputs*:
- `data/processed/baseline_comparison.csv`
- `data/processed/token_reduction_verification.json`
- `data/processed/statistical_results.json`

## 4. Interpreting Results

- **Token Reduction**: Check `token_reduction_verification.json`. `passed: true` indicates ≥ 30% reduction.
- **Statistical Significance**: Open `statistical_results.json`. Look for `bonferroni_adjusted` p-values < 0.05.
- **Win Rates**: Compare `win_rate` columns in `baseline_comparison.csv`.

## 5. Troubleshooting

- **Missing Data**: Ensure `data/raw/trajectories.csv` exists. The parser will raise an error if not found.
- **Low Correlation**: If proxy validation fails (r < 0.7), the pipeline stops. This indicates the static log features are poor predictors of utility.
- **Token Budget Errors**: If the simulator logs "Budget Exceeded", check `code/config.py` for `TOKEN_BUDGET` settings. The system should automatically prune layers.

## 6. Verification

To ensure reproducibility, run the full sequence from Step 1 to Step 6. All intermediate files in `data/processed/` should match the schema defined in `specs/`.
