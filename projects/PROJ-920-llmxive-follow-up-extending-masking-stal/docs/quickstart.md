# Quickstart Guide: llmXive Follow-up Study

This guide walks you through running the full pipeline for the study:
**"Masking Stale Observations Helps Search Agents -- Until It Doesn't"**

**Prerequisites**:
- Python 3.9+
- pip (Python package manager)
- ~7 GB RAM available for processing
- ~14 GB disk space for data and outputs

---

## 1. Installation

Clone the repository and install dependencies:

```bash
# Navigate to project root
cd projects/PROJ-920-llmxive-follow-up-extending-masking-stal

# Install required packages
pip install -r requirements.txt
```

> **Note**: If `requirements.txt` does not exist yet, create it with the following:
> ```text
> numpy>=1.24.0
> scipy>=1.10.0
> statsmodels>=0.13.0
> matplotlib>=3.7.0
> seaborn>=0.12.0
> ```

---

## 2. Directory Structure Setup

Ensure the required directories exist. If not, create them:

```bash
mkdir -p data/raw data/processed output/plots output/regression
mkdir -p code utils tests
```

Alternatively, run the setup scripts (if available):

```bash
python code/setup_directories.py
python code/setup_utils_directory.py
python code/setup_plots_directory.py
```

---

## 3. Step-by-Step Pipeline Execution

### Step 1: Generate Synthetic Trajectories

This step creates 500 synthetic search trajectories with controlled semantic density and injected critical evidence.

```bash
python code/generate_trajectories.py --output data/raw/trajectories.json
```

**Output**: `data/raw/trajectories.json` (≤ 100 MB)

**Verification**:
- Check file exists and is valid JSON.
- Ensure it contains ~500 trajectory entries.
- Verify metadata includes `evidence_turn_index` and `density_value`.

---

### Step 2: Simulate Agent with Variable Horizons

Run the heuristic agent simulation across retention horizons (1 to T) to measure success rates.

```bash
python code/simulate_agent.py \
 --input data/raw/trajectories.json \
 --output data/processed/simulation_results.csv
```

**Output**: `data/processed/simulation_results.csv`

**Verification**:
- Confirm CSV has columns: `trajectory_id`, `horizon`, `density`, `success`.
- Check that horizons < 5 show lower success rates for high-density evidence.
- Ensure horizons ≥ 5 show higher success rates (ground truth behavior).

---

### Step 3: Statistical Analysis (Logistic Regression)

Perform logistic regression with natural splines to model the interaction between density and horizon.

```bash
python code/analyze_results.py \
 --input data/processed/simulation_results.csv \
 --output output/regression/ \
 --df 3
```

**Outputs**:
- `output/regression/regression_summary.json` — Coefficients, p-values, and model stats.
- `output/regression/hypothesis_summary.txt` — Automatic conclusion on hypothesis support.

**Verification**:
- Open `regression_summary.json` and check for interaction term `density * horizon` with p < 0.05.
- Read `hypothesis_summary.txt` to confirm whether the hypothesis was supported.

---

### Step 4: Visualize Results (3D Surface Plot)

Generate a 3D surface plot showing Success Rate as a function of Masking Horizon and Semantic Density.

```bash
python code/visualize_results.py \
 --input output/regression/regression_summary.json \
 --output output/plots/surface_plot.png
```

**Output**: `output/plots/surface_plot.png` (≤ 5 MB)

**Verification**:
- Open the PNG and confirm axes: X=Horizon, Y=Density, Z=Success Rate.
- Ensure the surface shows a clear interaction effect (peak shifts with density).

---

## 4. Full Pipeline (One-Liner)

To run the entire pipeline sequentially (ensure dependencies are met first):

```bash
python code/generate_trajectories.py && \
python code/simulate_agent.py && \
python code/analyze_results.py && \
python code/visualize_results.py
```

> **Warning**: This assumes default input/output paths. For custom paths, use the individual commands above.

---

## 5. Troubleshooting

- **Missing dependencies**: Run `pip install -r requirements.txt` again.
- **File not found errors**: Ensure you are running commands from the project root (`projects/PROJ-920-llmxive-follow-up-extending-masking-stal/`).
- **Memory errors**: The simulation step may require ~7 GB RAM. Close other applications or use a machine with more memory.
- **Plot not rendering**: Ensure `matplotlib` and `seaborn` are installed and your backend supports GUI (or use a headless backend like `Agg`).

---

## 6. Next Steps

- Review `docs/api.md` for detailed function documentation.
- Run unit tests: `python -m pytest tests/unit/`
- Run integration tests: `python -m pytest tests/integration/`
- Run contract tests: `python -m pytest tests/contract/`

For further details, refer to the main `README.md`.