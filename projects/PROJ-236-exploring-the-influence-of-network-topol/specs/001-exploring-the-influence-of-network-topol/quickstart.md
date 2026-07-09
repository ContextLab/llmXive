# Quickstart: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## 1. Prerequisites

*   Python 3.11+
*   `pip`
*   Access to a CPU-only environment (e.g., GitHub Actions, local Linux machine).
*   `lammps` installed (CPU version) for EAM relaxation.

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-236-exploring-the-influence-of-network-topol
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## 3. Execution

The pipeline is executed in three sequential phases.

### Phase 0: Power Analysis
Calculates the required sample size.
```bash
python code/power_analysis.py --config code/simulation_config.yaml
```
*Output*: `data/processed/power_analysis.yaml`

### Phase 1: Generate Networks
Generates the ensemble of atomic connectivity networks with sensitivity sweep.
```bash
python code/generate_networks.py --config code/simulation_config.yaml
```
*Output*: `data/processed/network_realizations/`

### Phase 2: Compute Transport
Calculates thermal conductivity for each realization.
```bash
python code/compute_transport.py --input data/processed/network_realizations/ --config code/simulation_config.yaml
```
*Output*: `data/processed/transport_results/`

### Phase 3: Analyze Correlations
Performs statistical analysis and generates reports.
```bash
python code/analyze_correlations.py --networks data/processed/network_realizations/ --results data/processed/transport_results/
```
*Output*: `data/processed/analysis/`

## 4. Verification

Run the unit tests to ensure the pipeline is functional:
```bash
pytest tests/unit/
```

Run the integration test to verify the full pipeline (may take a significant duration).:
```bash
pytest tests/integration/test_full_pipeline.py
```

## 5. Troubleshooting

*   **Convergence Failure**: If `compute_transport.py` fails, check `simulation_config.yaml` for tighter convergence criteria or reduce the system size.
*   **Memory Error**: If `MemoryError` occurs, reduce `num_atoms` in `simulation_config.yaml` (target < 500 atoms).
*   **Missing Data**: Ensure `data/raw/` contains the synthetic lattice seed file. If missing, run `code/generate_networks.py` with `--generate-synth` flag.
*   **CI Width > 0.2**: If the analysis fails the CI width check, increase `bootstrap_iterations` in `simulation_config.yaml` or re-run the initial phase with a larger N.
