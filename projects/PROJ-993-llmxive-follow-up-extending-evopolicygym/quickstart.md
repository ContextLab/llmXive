# Quickstart: EvoPolicyGym Extension

2. Ensure the project structure is correct (Phase 1 tasks completed).

## Running the Pipeline

The pipeline is controlled via `code/main.py`. You can run specific stages or the full pipeline.

### Option 1: Run the Full Pipeline (Recommended)

This executes shift analysis, evolution, and statistical analysis, producing `data/final_results.csv`.

1. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline consists of three main stages: Shift Analysis, Evolution, and Statistics.

### Run Full Pipeline

To run the entire pipeline (Shift Analysis -> Evolution -> Stats) with default settings:

**Shift Sensitivity Analysis:**
```bash
python code/main.py
```

### Run Specific Stages

- **Shift Analysis**:
 ```bash
 python code/main.py --run-shift-analysis
 ```

- **Evolution**:
 ```bash
 python code/main.py --run-evolution --seeds 42 123 --runs 5
 ```

- **Statistics**:
 ```bash
 python code/main.py --run-stats
 ```

### Customization

You can customize the run with the following arguments:

- `--seeds`: List of random seeds (default: 42)
- `--runs`: Number of runs per seed (default: 5)
- `--envs`: Specific environment IDs to run (default: all discovered)
- `--conditions`: Conditions to test (default: baseline, counterfactual)

Example:
```bash
python code/main.py --run-evolution --seeds 42 --runs 10 --envs CartPole-v1 --conditions baseline
```

## Output Files

After running the pipeline, the following files will be generated in the `data/` directory:

- `sensitivity_report.csv`: Results of the shift sensitivity analysis.
- `evolution_results.csv`: Detailed results of the evolutionary runs (T032b).
- `stats_results.json`: Statistical analysis results (T036).
- `final_results.csv`: Aggregated metrics (T037).