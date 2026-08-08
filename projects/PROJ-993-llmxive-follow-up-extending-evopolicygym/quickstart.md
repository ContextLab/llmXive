# Quickstart Guide: EvoPolicyGym Follow-up

This guide explains how to run the full evolutionary pipeline and generate the required data artifacts.

## Prerequisites

1. Ensure all dependencies are installed:
 ```bash
 pip install -r requirements.txt
 ```

2. Ensure the project structure is correct (Phase 1 tasks completed).

## Running the Pipeline

The pipeline is controlled via `code/main.py`. You can run specific stages or the full pipeline.

### Option 1: Run the Full Pipeline (Recommended)

This executes shift analysis, evolution, and statistical analysis, producing `data/final_results.csv`.

```bash
cd projects/PROJ-993-llmxive-follow-up-extending-evopolicygym
python code/main.py --run-full --seeds 42 --runs 5 --envs CartPole-v1 LunarLander-v2
```

**Arguments:**
- `--seeds`: List of random seeds (default: 42)
- `--runs`: Number of runs per seed (default: 5)
- `--envs`: Specific environment IDs (optional; runs all discovered if omitted)
- `--conditions`: Conditions to test (default: baseline, counterfactual)

### Option 2: Run Individual Stages

**Shift Sensitivity Analysis:**
```bash
python code/main.py --run-shift-analysis
```

**Evolutionary Pipeline:**
```bash
python code/main.py --run-evolution --seeds 42 --runs 5
```

**Statistical Analysis:**
```bash
python code/main.py --run-stats
```

## Output Artifacts

Upon successful completion, the following files will be generated in the `data/` directory:

- `data/sensitivity_report.csv`: Performance drop analysis per environment.
- `data/evolution_results.csv`: Detailed metrics for each evolutionary run.
- `data/stats_results.json`: Statistical model results (p-values, effect sizes).
- `data/final_results.csv`: Aggregated final results (T037 output).

## Troubleshooting

- **Missing Environments**: Ensure `data/discovered_envs.json` exists. If not, run the environment discovery script first.
- **Import Errors**: Verify that `code/` is in your Python path or run from the project root.
- **CUDA Errors**: The pipeline is CPU-optimized for TinyLlama. Ensure you have sufficient RAM.
