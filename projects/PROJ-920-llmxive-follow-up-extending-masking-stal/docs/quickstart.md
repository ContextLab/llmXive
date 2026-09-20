# Quickstart Guide: llmXive Follow-up Study

This guide provides a step-by-step procedure to run the full pipeline for the study
"Masking Stale Observations Helps Search Agents -- Until It Doesn't".

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- A Unix-like environment (Linux/macOS) or WSL on Windows

## 1. Environment Setup

Navigate to the project root directory:

```bash
cd projects/PROJ-920-llmxive-follow-up-extending-masking-stal
```

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 2. Directory Structure Initialization

Ensure all necessary directories exist. Run the setup script:

```bash
python code/setup_directories.py
python code/setup_utils_directory.py
python code/setup_processed_directory.py
python code/setup_plots_directory.py
python code/setup_test_directories.py
```

*Expected Output*: Confirmation that directories `data/raw/`, `data/processed/`, `output/plots/`, `code/`, `code/utils/`, `tests/`, etc., are created.

## 3. Phase 1: Generate Synthetic Trajectories

Generate 500 synthetic search trajectories with controlled semantic density and injected critical evidence.

```bash
python code/generate_trajectories.py --output data/raw/trajectories.json --count 500 --seed 42
```

*Verification*:
- Check that `data/raw/trajectories.json` exists.
- Ensure the file contains 500 entries with metadata fields `density` and `critical_evidence_turn_index`.

## 4. Phase 2: Agent Simulation

Run the rule-based agent simulation with varying retention horizons to observe success rates.

```bash
python code/simulate_agent.py \
 --input data/raw/trajectories.json \
 --output data/processed/simulation_results.jsonl \
 --horizons 1 2 3 4 5 6 7 8 9 10 \
 --alpha 2.0 \
 --threshold 0.5 \
 --seed 42
```

*Parameters*:
- `--horizons`: Space-separated list of retention horizons to test.
- `--alpha`: Scaling factor for the logistic function (default: 2.0).
- `--threshold`: Critical density threshold for the logistic function (default: 0.5).

*Verification*:
- Check that `data/processed/simulation_results.jsonl` exists.
- The file should contain one JSON object per line with fields `trajectory_id`, `horizon`, `success`, and `density`.

## 5. Phase 3: Statistical Analysis

Perform logistic regression with natural splines to quantify the interaction effect between density and horizon.

```bash
python code/analyze_results.py \
 --input data/processed/simulation_results.jsonl \
 --output output/regression_summary.json \
 --hypothesis-output output/hypothesis_summary.md \
 --splines-df 3
```

*Verification*:
- Check that `output/regression_summary.json` exists and contains regression coefficients and p-values.
- Check that `output/hypothesis_summary.md` exists and states whether the hypothesis was supported.

## 6. Phase 4: Visualization

Generate a 3D surface plot visualizing the relationship between Masking Horizon, Semantic Density, and Success Rate.

```bash
python code/visualize_results.py \
 --input output/regression_summary.json \
 --output output/plots/surface_plot.png
```

*Verification*:
- Check that `output/plots/surface_plot.png` exists and is under 5 MB.
- The plot should display a 3D surface with axes: Horizon (X), Density (Y), and Success Rate (Z).

## 7. Validation (Optional)

Run the validation script to ensure all steps completed successfully.

```bash
python code/validate_quickstart.py
```

## Troubleshooting

- **Memory Issues**: If the simulation step fails due to memory constraints, ensure you are using the streaming version of the script (default) and that your system has at least 7 GB of RAM available.
- **Missing Dependencies**: If import errors occur, re-run `pip install -r requirements.txt`.
- **Path Errors**: Ensure you are running commands from the project root directory.

## Next Steps

- Review the generated hypothesis summary in `output/hypothesis_summary.md`.
- Analyze the 3D surface plot for regime shifts.
- Proceed to code cleanup tasks (T028-T033) if needed.
