# llmXive: AgenticSTS Follow-up

## Project Overview

This project extends the "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents" research.
It implements a dynamic memory retrieval policy for LLM agents, comparing it against static and random baselines
to evaluate token efficiency and task performance.

## Key Features

- **Dynamic Layer Selection**: Uses a trained classifier to predict optimal memory layers based on turn entropy.
- **Bounded Memory**: Enforces a hard token budget (4096 tokens) with a minimum context floor (256 tokens).
- **Statistical Validation**: Performs McNemar's tests and Bonferroni corrections to validate efficacy.
- **Ablation Studies**: Generates ground-truth utility labels via ablation on specific dataset splits.

## Project Structure

```
.
├── code/ # Core implementation
│ ├── config.py # Configuration constants (TOKEN_BUDGET, MIN_CONTEXT)
│ ├── parser.py # Trajectory parsing and metric extraction
│ ├── entropy.py # Shannon entropy calculation for move distributions
│ ├── splitter.py # Stratified data splitting (Train, Ablation, Validation, Test)
│ ├── ablation.py # Ablation study engine
│ ├── classifier.py # Utility classifier training and validation
│ ├── simulator.py # Dynamic and baseline simulation execution
│ ├── engine_runner.py # Engine invocation wrapper
│ ├── stats.py # Statistical testing (McNemar, Permutation, t-test)
│ └── main.py # Pipeline orchestrator
├── data/
│ ├── raw/ # Input trajectory logs
│ └── processed/ # Derived metrics, splits, and simulation logs
├── models/ # Trained classifier artifacts
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Step-by-step execution guide
```

## Prerequisites

- Python 3.11+
- Standard scientific stack (pandas, numpy, scikit-learn)
- CPU-only environment (no GPU required)

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Prepare Data**:
 Ensure raw trajectory logs are placed in `data/raw/`. The parser will validate checksums automatically.

3. **Run the Pipeline**:
 ```bash
 python code/main.py
 ```
 This executes the full pipeline: parsing, splitting, ablation, training, simulation, and statistical analysis.

4. **Dry Run Mode** (Recommended for verification):
 ```bash
 python code/main.py --dry-run
 ```
 Runs the pipeline on a single trajectory to verify data flow and edge case handling.

## Output Artifacts

The pipeline generates the following key artifacts in `data/processed/`:

- `metrics_with_moves.csv`: Extracted per-turn metrics and move distributions.
- `validation_set.csv`, `test_set.csv`, etc.: Stratified dataset splits.
- `ablation_labels_train.json`: Ground-truth utility scores from ablation.
- `simulation_logs_dynamic.json`: Results from the dynamic policy.
- `baseline_comparison.csv`: Aggregated win rates and token usage.
- `statistical_results.json`: Final p-values, effect sizes, and test types.

## Configuration

Key hyperparameters are defined in `code/config.py`:

- `TOKEN_BUDGET`: 4096 (Maximum tokens per prompt)
- `MIN_CONTEXT`: 256 (Minimum tokens required, enforced by appending 'Current Objective')
- `RANDOM_SEED`: Fixed for reproducibility.

## Testing

Run unit tests to verify edge cases (e.g., NaN entropy, token budget enforcement):

```bash
pytest tests/ -v
```

## License

Research use only. See project documentation for details.
