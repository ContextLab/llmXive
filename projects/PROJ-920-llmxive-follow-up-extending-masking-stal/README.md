# llmXive: Extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

**Project ID**: PROJ-920
**Status**: Active Research Pipeline

## Overview

This project implements an automated science pipeline to investigate the hypothesis that masking stale observations in search agents improves performance up to a critical threshold, after which performance degrades due to loss of necessary context.

The pipeline consists of four main stages:
1. **Trajectory Generation**: Creates synthetic search trajectories with controlled semantic density and ground-truth critical evidence injection.
2. **Agent Simulation**: Simulates rule-based agents with varying retention horizons to measure success rates.
3. **Statistical Analysis**: Performs logistic regression with natural splines to quantify the interaction between density and horizon.
4. **Visualization**: Generates a 3D regime map surface plot.

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup
1. Clone the repository.
2. Create a virtual environment (optional but recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline
The easiest way to run the entire research pipeline is via the provided shell script:

```bash
bash run_pipeline.sh
```

This script orchestrates the following steps in order:
1. `code/generate_trajectories.py`
2. `code/simulate_agent.py`
3. `code/analyze_results.py`
4. `code/visualize_results.py`

**Output**: All outputs will be written to the `output/` and `data/` directories.

### Individual Script Execution

If you wish to run specific stages independently:

#### 1. Generate Trajectories
Generates 500 synthetic trajectories with varying density levels.
```bash
python code/generate_trajectories.py
```
*Output*: `data/raw/trajectories.json`

#### 2. Simulate Agent
Runs the simulation with configurable retention horizons and heuristic parameters.
```bash
python code/simulate_agent.py --alpha 1.0 --threshold 0.5
```
*Output*: `data/processed/simulation_results.csv`

#### 3. Analyze Results
Performs logistic regression and generates hypothesis summaries.
```bash
python code/analyze_results.py
```
*Output*: `output/regression_summary.json`, `output/hypothesis_summary.md`

#### 4. Visualize Results
Generates the 3D regime map surface plot.
```bash
python code/visualize_results.py
```
*Output*: `output/plots/regime_map.png`

## Project Structure

```text
.
 ├── code/
 │ ├── utils/
 │ │ ├── entropy.py # Shannon entropy calculations
 │ │ └── heuristics.py # Composite density heuristics
 │ ├── generate_trajectories.py
 │ ├── simulate_agent.py
 │ ├── analyze_results.py
 │ ├── visualize_results.py
 │ └──... (setup scripts)
 ├── data/
 │ ├── raw/ # Generated trajectories
 │ └── processed/ # Simulation logs
 ├── output/
 │ ├── plots/ # Regime map visualization
 │ └──... (regression data)
 ├── tests/
 │ ├── unit/
 │ ├── integration/
 │ └── contract/
 ├── docs/
 │ ├── api.md
 │ └── quickstart.md
 ├── requirements.txt
 ├── run_pipeline.sh
 └── README.md
```

## Key Configuration

- **Density Terms**: The list of technical terms used for density calculation is defined in `code/config/density_terms.json`.
- **Heuristic Parameters**: The logistic function scaling (`alpha`) and threshold can be adjusted via CLI arguments in `simulate_agent.py`.
- **Splines**: The regression analysis uses natural splines with a fixed degrees of freedom (`df=3`) for the horizon variable.

## Contributing

Ensure all unit tests pass before submitting changes:
```bash
python -m pytest tests/unit/
```

## License

Research use only.