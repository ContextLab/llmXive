# Quickstart: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Prerequisites

- Python 3.11+
- `pip`
- GitHub Actions runner (or local environment with 2+ CPU cores, 7 GB RAM).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-236-exploring-the-influence-of-network-topol
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Generate Network Ensembles
```bash
python code/generation/network_generator.py --type all --count 100 --seed 42 --n-nodes 100
```
*Output*: `data/processed/networks/` (includes JSON files with metadata as top-level keys).

### Step 2: Cutoff Sensitivity Analysis (Optional)
```bash
python code/generation/sensitivity_sweep.py --min 1.0 --max 2.0 --step 0.1
```
*Output*: `data/results/sensitivity/`

### Step 3: Compute Thermal Conductivity
```bash
python code/transport/solver.py --input data/processed/networks/ --mode cpu
```
*Output*: `data/processed/transport/results.csv`

### Step 4: Statistical Analysis
```bash
python code/analysis/regressor.py --input data/processed/transport/results.csv --bootstrap 1000
```
*Output*: `data/results/correlations/analysis_report.json`

### Step 5: Visualize Results
```bash
python code/analysis/visualizer.py --input data/results/correlations/analysis_report.json --output figures/
```

## Validation

Run unit tests to verify network generation and solver stability:
```bash
pytest tests/unit/
```

## Troubleshooting

- **Convergence Failure**: Check `simulation_config.yaml` for time step adjustments.
- **Disconnected Graphs**: Increase `cutoff_factor` in `network_generator.py` arguments.
- **Memory Error**: Reduce ensemble count or atom count per realization (currently capped at 100).
- **Spec Contradiction**: Note that the plan uses Debye-Grüneisen approximation instead of `phono3py` and composition-based mass instead of mass-by-degree mapping.