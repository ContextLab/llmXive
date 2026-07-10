# Quickstart: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- GitHub Actions Runner (for CI execution)

## Installation

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

## Running the Pipeline

### 1. Generate Networks
```bash
python code/01_generate_networks.py --n 200 --types small_world,scale_free,random --seed 42
```
*Output*: `data/processed/graphs/`

### 2. Compute Transport
```bash
python code/02_compute_transport.py --input data/processed/graphs/ --mode cpu
```
*Output*: `data/processed/transport/`

### 3. Analyze Correlations
```bash
python code/03_analyze_correlations.py --transport data/processed/transport/ --graphs data/processed/graphs/
```
*Output*: `data/processed/analysis/`

## Verification

To verify the pipeline on a small scale:
```bash
pytest tests/unit/
pytest tests/integration/test_full_pipeline.py
```

## Troubleshooting

- **Convergence Failure**: If `convergence_status` is `failed`, check `simulation_config.yaml` for time step adjustments.
- **Memory Error**: Reduce `--n` (number of nodes) to a computationally feasible scale appropriate for the experimental design.
- **Disconnected Graphs**: The script automatically retries with a larger cutoff. If it fails >5% of the time, log and report.
