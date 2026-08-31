# llmXive: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

This project investigates how the stability of OLS regression coefficients varies with dataset subset selection, specifically analyzing the interaction between condition numbers (multicollinearity) and OLS assumption violations (heteroscedasticity, outliers).

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Project Structure

```
.
├── code/ # Executable scripts
├── data/
│ ├── raw/ # Downloaded datasets (gitignored)
│ └── processed/ # Processed data subsets (gitignored)
├── src/
│ ├── ingestion/ # Data loading and profiling
│ ├── resampling/ # Subset generation and OLS fitting
│ ├── analysis/ # Meta-analysis and visualization
│ └── utils/ # Configuration, logging, validation
├── tests/
│ ├── unit/
│ └── integration/
├── artifacts/
│ ├── profiles/ # Dataset violation profiles (JSON)
│ ├── stability/ # Coefficient stability metrics (JSON/CSV)
│ ├── meta_analysis/ # Final regression results and plots
│ └── checkpoints/ # Intermediate state saves
├── docs/
├── requirements.txt
└── README.md
```

## Quick Start

1. **Setup Directories**:
 ```bash
 python code/run_setup.py
 ```

2. **Ingest and Profile Datasets**:
 Runs the data loader and profiler to generate violation statistics.
 ```bash
 python code/ingest_and_profile.py --config config.yaml
 ```
 *Outputs*: `artifacts/profiles/*.json`

3. **Run Resampling Experiment**:
 Generates subsets, fits OLS models, and computes coefficient stability.
 ```bash
 python code/run_resampling.py --config config.yaml
 ```
 *Outputs*: `artifacts/stability/subsets_*.json`, `artifacts/stability/coefficient_sd.json`

4. **Compute Standard Error of SD**:
 Verifies convergence (SC-005).
 ```bash
 python code/calculate_sd_se.py --input artifacts/stability/coefficient_sd.json
 ```
 *Outputs*: `artifacts/stability/sd_se.json`

5. **Run Meta-Analysis**:
 Performs multiple regression with interaction terms.
 ```bash
 python code/regression_analysis.py --config config.yaml
 ```
 *Outputs*: `artifacts/meta_analysis/interaction_model.json`

6. **Generate Final Report**:
 Creates the summary markdown.
 ```bash
 python code/generate_final_report.py
 ```
 *Outputs*: `artifacts/meta_analysis/final_report.md`

7. **Visualize Results**:
 Generates stability curves.
 ```bash
 python code/generate_plots.py
 ```
 *Outputs*: `artifacts/meta_analysis/stability_curves.png`

## Artifact Paths Verification

The following artifacts are produced by the pipeline and verified against the `README.md` documentation:

| Artifact | Path | Description |
|:--- |:--- |:--- |
| **Profiles** | `artifacts/profiles/{dataset_name}.json` | Contains `breusch_pagan_stat`, `max_cooks_distance`, `condition_number`, `violation_severity`. |
| **Subsets** | `artifacts/stability/subsets_{tier}_{seed}.json` | Indices of generated random subsets per tier. |
| **Stability** | `artifacts/stability/coefficient_sd.json` | Empirical standard deviation of coefficients per predictor/tier. |
| **SD SE** | `artifacts/stability/sd_se.json` | Standard Error of the SD for convergence verification. |
| **Interaction Model** | `artifacts/meta_analysis/interaction_model.json` | Results of the multiple regression (coefficients, p-values, interaction term). |
| **Sensitivity Sweep** | `artifacts/meta_analysis/sensitivity_sweep.json` | Variance in classification rates across BP p-value cutoffs. |
| **Final Report** | `artifacts/meta_analysis/final_report.md` | Human-readable summary of findings. |
| **Stability Plot** | `artifacts/meta_analysis/stability_curves.png` | Visualization of coefficient std dev vs condition number. |

## CLI Usage

The main entry point for the pipeline is via the CLI module:

```bash
python -m src.cli --config test_config.yaml
```

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```

## License

MIT