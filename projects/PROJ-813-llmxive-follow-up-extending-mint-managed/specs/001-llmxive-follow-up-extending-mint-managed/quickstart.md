# Quickstart: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local machine with 7GB+ RAM)

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-813-llmxive-follow-up-extending-mint-managed/code
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for reproducibility.*

## Running the Simulation

The simulation is designed to run end-to-end on a CPU-only environment.

### 1. Generate Synthetic Data
Generate adapters and the topology graph.
```bash
python -m data_generation.synthetic_adapters --seed 42 --num-adapters 10000
python -m data_generation.overlap_graph --seed 42
```

Generate the request trace with a specific topological coupling coefficient (e.g., 0.8 for high correlation).
```bash
python -m data_generation.request_trace --seed 42 --num-requests 100000 --topology-bias 0.8
```

### 2. Run Simulations
Run the simulation for each policy (FCFS, Greedy, Topological) with a specific seed.
*Note: The same seed and trace are used for all policies to ensure a paired design.*
```bash
# Run FCFS
python -m simulation.main --policy fcfs --seed 42 --replications 10

# Run Greedy
python -m simulation.main --policy greedy --seed 42 --replications 10

# Run Topological Lookahead
python -m simulation.main --policy topological --seed 42 --replications 10
```

### 3. Run Statistical Analysis
```bash
python -m analysis.statistics --input data/results/summary_metrics.csv
```

## Validation

To ensure the system meets the acceptance criteria:

1.  **Check Memory**: Monitor RSS usage during simulation. The resource usage must remain within the designated system capacity limits.
    ```bash
    # Example using `time` and `ps` (Linux)
    /usr/bin/time -v python -m simulation.main --policy topological --seed 42
    ```
2.  **Check Time**: Ensure the full run completes within 6 hours.
3.  **Check Graph Validity**:
    ```bash
    python -c "from code.data_generation.overlap_graph import validate_graph; validate_graph('data/processed/topology_graph.npz')"
    ```
4.  **Check Statistical Significance**: The output of `analysis.statistics` must report a p-value < 0.05 for the Topological vs. FCFS comparison to claim success.
5.  **Check Coupling**: Verify that the `topology_bias` field in the results matches the input parameter.

## Troubleshooting

*   **OOM Error**: Reduce `--num-adapters` or increase sparsity in `synthetic_adapters.py`.
*   **Timeout**: Reduce `--num-requests` (e.g., to 50k) or `--replications` for testing; scale up for final run.
*   **Non-Deterministic Results**: Ensure `--seed` is pinned and `simpy` random state is not overridden.
*   **No Improvement**: If the Topological policy shows no improvement, check the `--topology-bias` parameter. If it is 0.0, the trace is random and the policy has no signal to exploit.