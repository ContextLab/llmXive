# Quickstart: EvoPolicyGym Extension Pipeline

This guide explains how to run the full analysis pipeline for the llmXive follow-up project.

## Prerequisites

1. Ensure all dependencies are installed:
 ```bash
 pip install -r requirements.txt
 ```
2. Verify that `data/discovered_envs.json` exists. If not, run:
 ```bash
 python code/main.py run-shift-analysis
 ```

## Running the Pipeline

The pipeline consists of four stages:
1. **Shift Sensitivity Analysis**: Evaluate environment sensitivity to dynamic shifts.
2. **Shift Validation**: Validate shift effects and calculate p-values.
3. **Evolution Pipeline**: Run evolutionary agents on baseline and counterfactual conditions.
4. **Statistical Analysis**: Perform mixed-effects model analysis.

You can run each stage individually or run the full pipeline at once.

### Run Full Pipeline

To execute the entire pipeline from start to finish:

```bash
python code/main.py run-full --seeds 42 --runs 5 --conditions baseline counterfactual
```

**Arguments:**
- `--seeds`: List of random seeds (default: 42)
- `--runs`: Number of runs per seed (default: 5)
- `--conditions`: Conditions to evaluate (default: baseline counterfactual)
- `--envs`: Specific environment IDs to target (optional, defaults to all discovered)

### Run Individual Stages

#### 1. Shift Sensitivity Analysis
```bash
python code/main.py run-shift-analysis
```
**Output:** `data/sensitivity_report.csv`

#### 2. Shift Validation
```bash
python code/main.py run-shift-validation
```
**Output:** `data/shift_validation.log`

#### 3. Evolution Pipeline
```bash
python code/main.py run-evolution --seeds 42 --runs 5
```
**Output:** `data/evolution_results.csv`, `data/run_state.json`

#### 4. Statistical Analysis
```bash
python code/main.py run-stats
```
**Output:** `data/stats_results.json`, `data/final_results.csv`

## Verifying Results

After running the full pipeline, verify that the following files exist:
- `data/sensitivity_report.csv`
- `data/evolution_results.csv`
- `data/stats_results.json`
- `data/final_results.csv`

## Troubleshooting

- **Missing `discovered_envs.json`**: Run `python code/main.py run-shift-analysis` first to discover environments.
- **Missing `sensitivity_report.csv`**: Ensure shift analysis completed successfully.
- **Missing `evolution_results.csv`**: Ensure evolution pipeline completed successfully.
- **Missing `stats_results.json`**: Ensure statistical analysis completed successfully.