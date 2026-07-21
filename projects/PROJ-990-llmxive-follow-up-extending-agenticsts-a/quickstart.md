# Quick Start Guide: llmXive AgenticSTS Follow-up

This guide provides a step-by-step walkthrough to reproduce the AgenticSTS dynamic memory retrieval experiments.

## 1. Environment Setup

Ensure you have Python 3.11 or higher installed.

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Required packages:
- `pandas`
- `numpy`
- `scikit-learn`
- `pytest`
- `pyyaml`
- `scipy`

## 2. Data Preparation

The pipeline expects raw trajectory logs in the `data/raw/` directory.

- **Input Format**: JSON or CSV files containing turn-by-turn agent trajectories.
- **Validation**: The `code/parser.py` module will automatically verify file checksums and ensure non-empty data.
- **Missing Data**: If `data/raw/` is empty or files are corrupted, the pipeline will raise a clear error (Task T034).

## 3. Execution Modes

### Full Pipeline Run

Executes the complete data processing, model training, simulation, and statistical analysis.

```bash
python code/main.py
```

**Expected Duration**: Varies based on dataset size (typically < 6 hours on CPU).
**Outputs**: All artifacts in `data/processed/` and `models/`.

### Dry-Run Mode (Verification)

Runs the pipeline on the first 5 trajectories to verify logic without full computation.

```bash
python code/main.py --dry-run
```

**Use Case**: Debugging data flow, checking edge cases (NaN entropy, budget truncation).
**Outputs**: Minimal logs in `data/processed/`.

## 4. Understanding the Workflow

The pipeline follows this strict dependency chain:

1. **Parsing** (`code/parser.py`): Extracts metrics and move distributions.
 - Output: `data/processed/metrics_with_moves.csv`
2. **Splitting** (`code/splitter.py`): Creates Train, Ablation-Train, Validation, and Test sets.
 - Constraint: Validation set must have ≥ 20 trajectories.
3. **Ablation** (`code/ablation.py`): Generates utility labels for training.
 - Output: `data/processed/ablation_labels_train.json`
4. **Validation** (`code/classifier.py`): Checks proxy correlation (r ≥ 0.7).
5. **Training** (`code/classifier.py`): Trains the utility classifier.
 - Output: `models/layer_utility_classifier.pkl`
6. **Simulation** (`code/simulator.py`): Runs Dynamic, Static, and Random policies.
 - Output: `data/processed/simulation_logs_*.json`
7. **Statistics** (`code/stats.py`): Computes significance (McNemar's, Bonferroni).
 - Output: `data/processed/statistical_results.json`

## 5. Key Artifacts

After a successful run, review these files:

- **`data/processed/baseline_comparison.csv`**:
 Compares Win Rate and Avg Tokens across Dynamic, Static, and Random policies.
- **`data/processed/token_reduction_verification.json`**:
 Reports if the Dynamic policy achieved ≥ 30% token reduction.
- **`data/processed/statistical_results.json`**:
 Contains p-values, effect sizes, and the specific statistical tests used (e.g., McNemar's).

## 6. Troubleshooting

- **Error: "Data source validation failed"**:
 Ensure `data/raw/` contains valid, non-empty trajectory files.
- **Error: "Validation set size < 20"**:
 The dataset split is too small. Check input data volume.
- **Error: "Proxy correlation < 0.7"**:
 The static log proxy does not correlate well with ablation utility. Check `data/processed/proxy_validation_report.json`.
- **Fallback Mode**:
 If the ablation sample size is < 300, the pipeline automatically generates fallback k=2 labels and logs a warning (Task T008c).

## 7. Reproducibility

To ensure exact reproducibility:
- Run `code/generate_analysis_config.py` to snapshot seeds and hyperparameters.
- The pipeline uses fixed random seeds defined in `code/config.py`.
- All statistical tests include Bonferroni corrections for family-wise error control.

## 8. Next Steps

- **Benchmarking**: Run `python code/benchmark.py` to profile execution time per phase.
- **Optimization**: Review `data/processed/optimization_report.md` for performance insights.
- **Contribution**: See `CONTRIBUTING.md` (if available) for guidelines on extending the pipeline.