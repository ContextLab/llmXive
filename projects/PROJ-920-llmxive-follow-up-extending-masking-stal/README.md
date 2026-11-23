# llmXive Follow-up: Extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

**Project ID**: PROJ-920-llmxive-follow-up-extending-masking-stal

This project implements a research pipeline to investigate the interaction between **semantic density** and **retention horizon** in search agents. It generates synthetic search trajectories, simulates agent behavior with variable memory horizons, and performs statistical analysis to map the "regime" where masking stale observations is beneficial versus detrimental.

## 🎯 Research Goal

To quantify how the density of critical evidence in a search trajectory modulates the effectiveness of masking stale observations. We hypothesize that while masking generally helps, there exists a specific interaction effect where high-density evidence requires longer retention horizons to be successfully retrieved by the agent.

## 🏗️ Project Structure

```text
.
├── code/
│ ├── utils/ # Core utilities (entropy, heuristics)
│ │ ├── entropy.py
│ │ └── heuristics.py
│ ├── config/ # Configuration files
│ │ └── density_terms.json
│ ├── generate_trajectories.py # Synthetic data generation (US1)
│ ├── simulate_agent.py # Agent simulation (US2)
│ ├── analyze_results.py # Statistical analysis (US3)
│ └── visualize_results.py # 3D surface plotting
├── data/
│ ├── raw/ # Generated trajectories (trajectories.json)
│ └── processed/ # Simulation logs (simulation_logs.csv)
├── output/
│ ├── plots/ # Regime map visualization
│ │ └── regime_map.png
│ ├── regression_summary.json
│ └── hypothesis_summary.md
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
├── docs/
│ ├── api.md
│ └── quickstart.md
├── requirements.txt
└── README.md
```

## 📦 Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-920-llmxive-follow-up-extending-masking-stal
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## 🚀 Usage

### Option 1: Run the Full Pipeline (Recommended)

Execute the entire research workflow (Generation → Simulation → Analysis → Visualization) with a single command. This ensures data flow consistency and reproducibility.

```bash
# Usage:./run_pipeline.sh [--seed <int>]
./run_pipeline.sh --seed 42
```

This script will:
1. Generate `data/raw/trajectories.json`
2. Run simulation and write `data/processed/simulation_logs.csv`
3. Perform logistic regression and output `output/regression_summary.json`
4. Generate the regime map at `output/plots/regime_map.png`

### Option 2: Run Steps Individually

You can run each stage of the pipeline independently.

**Step 1: Generate Synthetic Trajectories**
```bash
python code/generate_trajectories.py --seed 42
```
*Output*: `data/raw/trajectories.json` containing ~500 synthetic search trajectories with controlled density levels.

**Step 2: Simulate Agent Behavior**
```bash
python code/simulate_agent.py --seed 42
```
*Output*: `data/processed/simulation_logs.csv` containing success/failure outcomes for various horizon/density combinations.

**Step 3: Statistical Analysis**
```bash
python code/analyze_results.py --seed 42
```
*Output*: `output/regression_summary.json` and `output/hypothesis_summary.md`.

**Step 4: Visualization**
```bash
python code/visualize_results.py
```
*Output*: `output/plots/regime_map.png` (3D surface plot).

## 🔬 Key Components

- **Entropy Calculation (`code/utils/entropy.py`)**: Computes Shannon entropy on UTF-8 byte-level tokens with clamping for zero-density edge cases.
- **Density Heuristics (`code/utils/heuristics.py`)**: Implements the composite formula: `Density = 0.6 * Shannon_Entropy + 0.4 * Technical_Token_Ratio`.
- **Trajectory Generator (`code/generate_trajectories.py`)**: Creates synthetic search logs with parameterized semantic density and injected critical evidence.
- **Agent Simulator (`code/simulate_agent.py`)**: Runs a rule-based agent with a logistic success function `P(retrieval) = sigmoid(α * (density - threshold))` across varying retention horizons.
- **Analyzer (`code/analyze_results.py`)**: Fits a Generalized Linear Model (GLM) with natural splines to quantify the interaction effect.

## 📊 Expected Outputs

After running the full pipeline, verify the following artifacts:

| File | Description |
|------|-------------|
| `data/raw/trajectories.json` | Synthetic search trajectories with metadata |
| `data/processed/simulation_logs.csv` | Agent success/failure logs |
| `output/regression_summary.json` | GLM coefficients and p-values |
| `output/hypothesis_summary.md` | Human-readable hypothesis validation |
| `output/plots/regime_map.png` | 3D surface of Success Rate vs. Horizon & Density |

## 🧪 Testing

Run the unit and integration tests:

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Contract tests
pytest tests/contract/
```

## 📄 Documentation

- **Quickstart Guide**: See `docs/quickstart.md` for a step-by-step walkthrough.
- **API Reference**: See `docs/api.md` for detailed function documentation.

## ⚠️ Constraints & Notes

- **Memory**: The simulation step is memory-constrained. Ensure you have at least 7GB of RAM available. [UNRESOLVED-CLAIM: c_619e3159 — status=not_enough_info] The script will exit with `MEMORY_LIMIT_EXCEEDED` if this threshold is breached.
- **Reproducibility**: Always use the `--seed` flag to ensure deterministic results.
- **Data Flow**: The pipeline enforces strict data flow checks. If `trajectories.json` is missing, `simulate_agent.py` will fail immediately.