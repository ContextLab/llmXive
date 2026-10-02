# Quickstart Guide: Bounded Confidence Impact Study

## Prerequisites

- Python 3.11+
- `pip install -r code/requirements.txt`

## Project Structure

```
.
├── code/
│ ├── generate_networks.py # Network generation
│ ├── simulate_hk.py # HK simulation engine
│ ├── analyze_scaling.py # Scaling analysis & regression
│ └── utils/
│ ├── metrics.py # Structural metrics
│ └── plotting.py # Visualization
├── data/
│ ├── raw/
│ │ ├── networks/ # Generated network instances
│ │ └── simulations/ # Raw simulation traces
│ └── processed/
│ ├── epsilon_c_values.json # Critical thresholds
│ └── regression_data.json # Merged dataset for analysis
├── docs/
│ ├── METHODOLOGY.md # Detailed methodology
│ └── RESULTS.md # Summary of findings
└── tests/
 └──... # Unit and integration tests
```

## Execution Workflow

### 1. Generate Network Ensembles

Run the network generator to create Erdős-Rényi, Barabási-Albert, and Watts-Strogatz networks.

```bash
python code/generate_networks.py --topologies er ba ws --count 50 --seed 42
```

**Output**: Network files in `data/raw/networks/` and metrics in `data/raw/networks/metrics_*.json`.

### 2. Run Simulations

Execute the HK simulation sweep across $\epsilon \in [0.01, 0.50]$.

```bash
python code/simulate_hk.py --epsilon-range 0.01 0.50 0.01 --seeds 10
```

**Output**: HDF5 files in `data/raw/simulations/` containing opinion traces and metadata.

### 3. Analyze Scaling Laws

Detect $\epsilon_c$ and fit power-law models.

```bash
python code/analyze_scaling.py --input data/raw/simulations/ --output data/processed/
```

**Output**: `data/processed/epsilon_c_values.json` and `data/processed/regression_data.json`.

### 4. Visualize Results

Generate convergence plots and regression scatter plots.

```bash
python code/utils/plotting.py --data data/processed/regression_data.json --output figures/
```

**Output**: PNG figures in `figures/`.

### 5. Run Tests

Verify correctness and reproducibility.

```bash
pytest tests/ -v
```

## Reproducibility

All scripts use deterministic seeds. To reproduce exact results, set the global seed via the `--seed` argument. Parallel workers use `worker_seed = base_seed + worker_id` to ensure reproducibility.

## Troubleshooting

- **Non-convergence**: If simulations fail to converge, check if $\epsilon < \epsilon_c$. The model may fragment permanently.
- **Memory Limits**: For large ensembles, reduce `--count` or use streaming mode in `simulate_hk.py`.
- **Checksum Mismatch**: Run `python code/utils/checksums.py --verify` to validate data integrity.

## References

- Hegselmann, R., & Krause, U. (2002). Opinion dynamics and bounded confidence: models, analysis and simulation.
- Deffuant, G., et al. (2000). Mixing beliefs among interacting agents.
- NetworkX Documentation: https://networkx.org/documentation/stable/