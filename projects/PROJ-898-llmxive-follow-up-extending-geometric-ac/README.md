# llmXive: Geometric Action Model Follow-up

Automated pipeline for extending the "Geometric Action Model for Robot Policy Learning" with a symbolic latent planner.

## Project Structure

```
.
├── code/ # Core Python modules
│ ├── __init__.py
│ ├── analysis.py # Statistical analysis (McNemar, t-test, Wilcoxon)
│ ├── baseline_validator.py
│ ├── config.py # Configuration loader and typed objects
│ ├── config.yaml # Experiment parameters
│ ├── data_generation.py # Physics simulation and task generation
│ ├── differentiable_solver.py
│ ├── experiment_time_validator.py
│ ├── gfm_wrapper.py # Frozen GFM encoder/decoder interface
│ ├── gradient_verification.py
│ ├── inference_integration.py
│ ├── inference_pipeline.py
│ ├── latent_drift.py # Drift detection utilities
│ ├── metadata_checksum.py
│ ├── physics_state_extractor.py
│ ├── solver_profiler.py
│ ├── statistical_reference.py
│ ├── symbolic_solver.py # Symbolic planner implementation
│ ├── timeout_handler.py
│ ├── trial_log_schema.py
│ └── utils.py # Logging, seeding, hashing
├── data/ # Data artifacts (gitignored)
│ ├── raw/ # Downloaded models, reference stats
│ ├── generated/ # Synthetic test sets, ground truth
│ └── results/ # Trial logs, analysis reports
├── tests/ # Unit and integration tests
│ ├── __init__.py
│ └──...
├── scripts/ # Entry point scripts
│ ├── generate_test_set.py
│ └── validate_quickstart.sh
├── requirements.txt # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.9+
- PyBullet (`pip install pybullet`)
- PyTorch CPU (`pip install torch==2.0.0+cpu --index-url https://download.pytorch.org/whl/cpu`)
- DiffTaichi, CVXPY, SciPy, Pandas, NumPy, PyYAML, Ruff, Pre-commit

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. (Optional) Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Configuration

Edit `code/config.yaml` to define experiment parameters:
- `topology_counts`: List of kinematic chain lengths to generate.
- `trial_count`: Number of tasks to generate (default 100).
- `sim_fps`: Simulation steps per second.
- `timeout_limits`: Maximum duration per solver step.
- `target_zone`: Center and radius for success criteria.
- `baseline_model_url`: URL for baseline weights (optional).

## CLI Usage

### Generate Test Set (US1)
Generates a synthetic dataset of manipulation tasks with novel topologies.
```bash
python scripts/generate_test_set.py --seed 42
```
**Outputs:**
- `data/generated/physics_states.json`: Full simulation states.
- `data/generated/latent_trajectory.csv`: Latent vector trajectories.
- `data/generated/ground_truth_traj.json`: Ground truth for validation.
- `data/generated/unique_topology_ids.json`: Verification of zero overlap.

### Run Symbolic Planner (US2)
Executes the symbolic latent planner on the generated test set.
```bash
python code/inference_pipeline.py --config code/config.yaml
```
**Outputs:**
- `data/results/trial_logs.jsonl`: Per-trial results (success, latency, constraints).
- `data/results/symbolic_decoder_mse.json`: Decoder error metric.
- `data/results/constraint_satisfaction_log.json`: Constraint satisfaction rates.

### Run Baseline Comparison (US3)
Runs the baseline model for comparison.
```bash
python code/baseline_runner.py --config code/config.yaml
```
**Outputs:**
- `data/results/baseline_results.csv`: Baseline performance metrics.

### Analysis and Reporting (US3)
Performs statistical analysis and generates the final report.
```bash
python code/analysis.py --config code/config.yaml
```
**Outputs:**
- `data/results/analysis_report.md`: Markdown table with metrics, p-values, and effect sizes.
- `data/results/experiment_validation.json`: Pass/fail status for SC-001, SC-003.

## Validation

Run the quickstart validation script to ensure end-to-end reproducibility:
```bash
bash scripts/validate_quickstart.sh
```

## Testing

Run unit tests:
```bash
pytest tests/ -v
```

## License

[Project License]