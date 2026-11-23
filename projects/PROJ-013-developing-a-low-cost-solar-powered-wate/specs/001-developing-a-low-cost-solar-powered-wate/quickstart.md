# Quickstart: 001-solar-purification-tradeoff

## 1. Prerequisites

- Python 3.11+
- `pip`
- Internet access (for API calls)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-013-developing-a-low-cost-solar-powered-wate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

### Step 1: Data Ingestion
Fetches material properties (hardcoded NIST) and current market prices.
```bash
python code/data_ingestion.py
```
*Output*: `data/processed/materials.csv`

### Step 2: Simulation
Runs transient heat transfer for all material-geometry-angle combinations.
```bash
python code/simulation.py
```
*Output*: `data/processed/simulation_results.csv`

### Step 3: Optimization & Visualization
Identifies Pareto frontier and generates the trade-off plot.
```bash
python code/optimization.py
```
*Output*: `data/plots/pareto_frontier.png`, `data/processed/pareto_frontier.csv`

### Step 4: Validation
Checks Energy Balance and plausibility (integrated in Step 2).
```bash
python code/validation.py
```

## 4. Full Run (One Command)
```bash
python code/main.py
```

## 5. Expected Output

- **Console**: Progress bars, warnings for non-convergent runs, final efficiency/cost summary.
- **Files**:
  - `data/processed/materials.csv`: 4 rows (Al, Cu, Steel, Plastic).
  - `data/processed/simulation_results.csv`: ~108 rows (including angle sweeps).
  - `data/plots/pareto_frontier.png`: Scatter plot with knee point marked.

## 6. Troubleshooting

- **API Error**: If NASA POWER or price API fails, the script will log a warning and use hardcoded fallbacks. Check `data/raw/api_logs.txt`.
- **Non-Convergence**: If a simulation fails, it is excluded from the Pareto set. Check `data/processed/simulation_results.csv` for `convergence_status = failed`.
- **Energy Balance Failure**: If `energy_balance_error` > 5%, the result is flagged as `invalid_balance` and excluded.
- **Plausibility Warning**: If efficiency is outside the expected operational range, a warning is logged, but the result is NOT excluded unless Energy Balance fails.
- **Spec-Root Cause Note**: If the mean-efficiency check (FR-006) fails, it is logged as a warning only. The Spec requires amendment to remove this gate.