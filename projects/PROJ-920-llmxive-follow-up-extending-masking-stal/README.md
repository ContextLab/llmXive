# llmXive Follow-up: Extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

This project implements an automated science pipeline to investigate the relationship between **semantic density** of search trajectories and the optimal **retention horizon** for search agents.

The core hypothesis is that while masking stale observations generally improves agent performance, the optimal retention window depends heavily on the density of critical evidence within the context. This project simulates search agents, generates synthetic trajectories with controlled density, and performs statistical analysis to map the "regime" where masking helps versus where it hurts.

## Project Structure

```text
.
├── code/ # Core implementation scripts
│ ├── utils/ # Utility modules (entropy, heuristics)
│ │ ├── entropy.py # Shannon entropy calculations
│ │ └── heuristics.py # Composite density formulas
│ ├── generate_trajectories.py # Synthetic data generation
│ ├── simulate_agent.py # Agent simulation with variable horizons
│ ├── analyze_results.py # Statistical analysis (GLM, splines)
│ └── visualize_results.py # 3D surface plotting
├── data/
│ ├── raw/ # Generated trajectory JSON files
│ └── processed/ # Simulation results (CSV/JSON)
├── output/
│ ├── plots/ # Generated figures (PNG)
│ └── regression_summary.json
├── tests/ # Unit, integration, and contract tests
│ ├── unit/
│ ├── integration/
│ └── contract/
├── README.md
└── requirements.txt
```

## Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

## Installation

1. **Clone the repository** (or navigate to the project root):
 ```bash
 cd projects/PROJ-920-llmxive-follow-up-extending-masking-stal
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

The pipeline consists of three main stages: Generation, Simulation, and Analysis.

### Step 1: Generate Synthetic Trajectories

Generates 500 search trajectories with controlled semantic density (low, medium, high) and injected critical evidence.

```bash
python code/generate_trajectories.py --output data/raw/trajectories.json --count 500 --seed 42
```

**Output**: `data/raw/trajectories.json` containing metadata, density values, and evidence turn indices.

### Step 2: Simulate Agent Behavior

Runs the rule-based agent simulation across varying retention horizons (1 to T) using the generated trajectories.

```bash
python code/simulate_agent.py \
 --input data/raw/trajectories.json \
 --output data/processed/simulation_results.csv \
 --alpha 2.5 \
 --threshold 0.5 \
 --batch-size 50
```

**Parameters**:
- `--alpha`: Scaling factor for the logistic retrieval probability.
- `--threshold`: Critical density threshold for the logistic function.
- `--batch-size`: Number of trajectories to process before writing to disk (streaming).

**Output**: `data/processed/simulation_results.csv` with success/failure logs per horizon.

### Step 3: Analyze Results & Visualize

Performs logistic regression with natural splines to identify the interaction effect and generates a 3D surface plot.

```bash
python code/analyze_results.py \
 --input data/processed/simulation_results.csv \
 --output output/ \
 --df 3
```

```bash
python code/visualize_results.py \
 --summary output/regression_summary.json \
 --output output/plots/regime_map.png
```

**Outputs**:
- `output/regression_summary.json`: Regression coefficients, p-values, and hypothesis test results.
- `output/hypothesis_summary.md`: Human-readable summary of findings.
- `output/plots/regime_map.png`: 3D surface plot (Masking Horizon vs. Density vs. Success Rate).

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

Run specific test categories:
- **Unit Tests**: `pytest tests/unit/ -v`
- **Integration Tests**: `pytest tests/integration/ -v`
- **Contract Tests**: `pytest tests/contract/ -v`

## Configuration & Reproducibility

To ensure reproducibility and avoid bias:
- All random seeds are explicitly set via CLI arguments.
- Logistic function parameters (`alpha`, `threshold`) are **not** hardcoded defaults; they must be provided or set via environment variables.
- The streaming implementation in `simulate_agent.py` ensures memory usage stays below 7GB even for large trajectory sets.

## License

This project is part of the llmXive research initiative.

## Contributing

Please refer to the `specs/` directory for detailed design documents and user stories.