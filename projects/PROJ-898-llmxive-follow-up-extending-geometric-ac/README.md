# llmXive: Geometric Action Model for Robot Policy Learning (Follow-up)

An automated research pipeline implementing a symbolic latent planner for robot policy learning, extending the "Geometric Action Model" (GAM) framework. This project focuses on zero-overlap generalization to novel kinematic chains and deformable materials using a frozen GFM encoder/decoder and a differentiable symbolic solver.

## Project Structure

```
.
├── code/ # Core implementation modules
│ ├── analysis.py # Statistical analysis (McNemar, Wilcoxon/t-test)
│ ├── baseline_validator.py
│ ├── config.py # Configuration loading and management
│ ├── data_generation.py # Synthetic topology generation
│ ├── differentiable_solver.py
│ ├── gfm_wrapper.py # Frozen GFM encoder/decoder interface
│ ├── inference_pipeline.py
│ ├── latent_drift.py # Drift detection logic
│ ├── symbolic_solver.py # Core symbolic constraint solver
│ └── utils.py # Logging, seeding, hashing utilities
├── data/
│ ├── raw/ # Raw inputs (weights, manifests, stats)
│ ├── generated/ # Generated test sets and physics states
│ └── results/ # Experiment logs and analysis reports
├── tests/ # Unit and integration tests
├── scripts/ # CLI entry points and automation
│ ├── generate_test_set.py
│ └── run_experiment.py
├── README.md
├── requirements.txt
└──.gitignore
```

## Prerequisites

- Python 3.9+
- CPU-only environment (No GPU/CUDA required)
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmxive-follow-up-extending-geometric-ac
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: PyTorch CPU version is pinned in `requirements.txt`.*

## Configuration

Edit `code/config.yaml` to set experiment parameters:
- `topology_counts`: Number of topologies to generate
- `timeout_limits`: Solver step timeout in seconds
- `seed`: Random seed for reproducibility
- `trial_count`: Number of experimental trials
- `baseline_model_url`: URL for baseline weights (optional)

Generate a default config if missing:
```bash
python -c "from code.config import create_default_config_file; create_default_config_file()"
```

## CLI Usage

### 1. Generate Test Set (User Story 1)

Generates a synthetic dataset of 100+ unique manipulation tasks with novel topologies.
```bash
python scripts/generate_test_set.py
```
**Outputs:**
- `data/generated/raw_topology_data.json`
- `data/generated/physics_states.json`
- `data/generated/latent_trajectory.csv`

### 2. Run Experiment (User Story 2 & 3)

Executes the symbolic planner and baseline comparison.
```bash
python scripts/run_experiment.py
```
**Outputs:**
- `data/results/trial_logs.jsonl`
- `data/results/symbolic_results.csv`
- `data/results/baseline_results.csv`
- `data/results/analysis_report.md`

### 3. Statistical Analysis

Performs McNemar's test and latency comparison (Wilcoxon/t-test).
```bash
python -c "from code.analysis import StatisticalAnalyzer; StatisticalAnalyzer().run_full_analysis()"
```

## Data Verification

The pipeline enforces zero-overlap with the original GAM training set.
- Checksums are verified against `data/raw/training-topology-manifest.json`.
- Latent drift is monitored against `data/raw/gam_reference_stats.json`.

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Validation

Run the quickstart validation script to ensure end-to-end reproducibility:
```bash
bash scripts/validate_quickstart.sh
```

## License

[Insert License Here]