# llmXive Follow-up: Extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

This project implements a research pipeline to investigate the interaction between **semantic density** of search trajectories and the **retention horizon** (masking staleness) of search agents.

The core hypothesis is that while masking stale observations generally helps agents focus, the optimal retention horizon shifts positively as the semantic density of the critical evidence increases. We validate this using synthetic trajectory generation, a rule-based heuristic agent simulation, and statistical analysis (logistic regression with natural splines).

## Project Structure

```text
.
├── code/ # Main implementation scripts
│ ├── utils/ # Utility modules (entropy, heuristics)
│ │ ├── entropy.py
│ │ └── heuristics.py
│ ├── generate_trajectories.py # Synthetic data generation (US1)
│ ├── simulate_agent.py # Agent simulation loop (US2)
│ ├── analyze_results.py # Statistical analysis (US3)
│ └── visualize_results.py # 3D surface plotting (US3)
├── data/
│ ├── raw/ # Generated trajectories (JSON)
│ └── processed/ # Simulation logs (JSON/CSV)
├── output/
│ ├── plots/ # Generated figures (PNG)
│ ├── regression_summary.json # Regression coefficients
│ └── hypothesis_summary.txt # Final hypothesis conclusion
├── tests/
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Schema contract tests
├── README.md
└── requirements.txt
```

## Prerequisites

- Python 3.9+
- pip

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 cd projects/PROJ-920-llmxive-follow-up-extending-masking-stal
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

The pipeline consists of three main stages. Run them sequentially to reproduce the full study.

### Step 1: Generate Synthetic Trajectories

Generates 500 synthetic search trajectories with controlled semantic density (low, medium, high) and injected critical evidence.

```bash
python code/generate_trajectories.py
```

**Output**: `data/raw/trajectories.json`

### Step 2: Simulate Agent with Variable Horizons

Runs the heuristic agent simulation across varying retention horizons (1 to T) on the generated trajectories.

```bash
python code/simulate_agent.py
```

**Output**: `data/processed/simulation_results.json`

### Step 3: Analyze and Visualize

Performs logistic regression with natural splines to quantify the interaction effect and generates a 3D surface plot.

```bash
python code/analyze_results.py
python code/visualize_results.py
```

**Outputs**:
- `output/regression_summary.json` (Coefficients and p-values)
- `output/hypothesis_summary.txt` (Hypothesis validation)
- `output/plots/surface_plot.png` (3D interaction surface)

## Configuration

- **Density Levels**: Controlled in `generate_trajectories.py` (default: low, medium, high).
- **Retention Horizons**: Configurable in `simulate_agent.py` (default: 1 to T).
- **Regression Degrees of Freedom**: Pass `--df <int>` to `analyze_results.py` to adjust spline flexibility.
- **Heuristic Parameters**: `alpha` (scaling) and `threshold` (critical density) are defined in `simulate_agent.py`.

## Testing

Run the full test suite:

```bash
pytest tests/
```

Specific test groups:
- Unit tests: `pytest tests/unit/`
- Integration tests: `pytest tests/integration/`
- Contract tests: `pytest tests/contract/`

## License

Research project for academic use.

## References

- Original Study: "Masking Stale Observations Helps Search Agents -- Until It Doesn't"
- Project ID: PROJ-920-llmxive-follow-up-extending-masking-stal