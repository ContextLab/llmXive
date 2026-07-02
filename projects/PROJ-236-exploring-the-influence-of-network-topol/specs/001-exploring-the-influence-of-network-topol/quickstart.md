# Quickstart: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- 2 CPU cores, 7GB RAM (GitHub Actions free-tier compatible)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-236-exploring-the-influence-of-network-topol
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Verify Environment**:
   ```bash
   python -c "import networkx, scikit_learn, numpy; print('All dependencies loaded.')"
   ```

## Running the Pipeline

The pipeline is executed in three sequential steps.

### Step 1: Generate Network Ensembles
Generates Small-World, Scale-Free, and Random networks with sensitivity analysis on distance cutoffs.
```bash
python code/generate_networks.py --config code/config.yaml
```
- **Output**: `data/processed/ensembles.jsonl`
- **Expected**: ~300 valid realizations (100 per topology).

### Step 2: Compute Thermal Conductivity
Calculates effective thermal conductivity using the simplified anharmonic solver.
```bash
python code/compute_transport.py --input data/processed/ensembles.jsonl --output data/results/transport_results.csv
```
- **Output**: `data/results/transport_results.csv`
- **Expected**: Runtime < 45 mins per realization; total < 6 hours.

### Step 3: Analyze Correlations
Performs regression, bootstrap resampling, and multiple-comparison correction.
```bash
python code/analyze_correlations.py --networks data/processed/ensembles.jsonl --transport data/results/transport_results.csv --output data/results/correlation_analysis.json
```
- **Output**: `data/results/correlation_analysis.json`
- **Expected**: JSON with correlation stats, p-values, and CIs.

## Validation

Run the test suite to ensure correctness:
```bash
pytest tests/ -v --cov=code
```
- **Pass Criteria**: All unit tests pass; coverage > 80%.
- **Contract Test**: `pytest tests/contract/` validates output schemas against `contracts/*.schema.yaml`.

## Troubleshooting

- **Disconnected Graphs**: If <95% of realizations are valid, increase `cutoff_factor` in `config.yaml` (e.g., from 1.5 to 1.8).
- **Convergence Failure**: If >5% of transport calculations fail, check `simulation_config.yaml` for tighter convergence criteria or increase `max_retries`.
- **Memory Error**: Ensure no large datasets are loaded into memory; use `pandas.read_csv(..., chunksize=...)` if needed (not expected for N=300).
