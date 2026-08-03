# llmXive: Extending OpenRath Session-Centered Runtime State

A research pipeline for evaluating session-centered runtime state architectures against traditional event-log approaches in multi-agent debugging workflows.

## Overview

This project implements a reproducible scientific pipeline to:
1. Generate deterministic synthetic multi-agent debugging workflows with ground truth states.
2. Execute workflows through two distinct architectures:
 - **Baseline**: Event-Log (asynchronous, fragmented storage)
 - **Experimental**: Session-First (atomic, single-object state recording)
3. Inject controlled corruption and network jitter.
4. Reconstruct final states from corrupted logs.
5. Calculate fidelity metrics and perform statistical analysis (Cochran's Q, McNemar's test).

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration and state management
│ ├── main.py # Orchestration CLI and pipeline logic
│ ├── setup_structure.py # Project initialization utility
│ ├── generators/ # Workflow generation and ground truth
│ ├── executors/ # Baseline and Session-First executors
│ ├── reconstructors/ # State reconstruction logic
│ ├── analyzers/ # Metrics calculation and statistical tests
│ ├── simulators/ # Corruption injection and network jitter
│ └── utils/ # Checksum management and utilities
├── data/
│ ├── raw/workflows/ # Generated ground truth files
│ └── processed/
│ ├── event_log/ # Baseline architecture logs
│ ├── session_first/ # Session-First architecture states
│ ├── corrupted_logs/ # Logs after corruption injection
│ ├── reconstruction_results/ # Reconstructed states
│ └── results/ # Aggregated metrics and statistical results
├── state/
│ └── projects/ # Project state and checkpoint files
├── tests/
│ ├── unit/ # Unit tests for core components
│ └── integration/ # Integration tests for pipelines
├── docs/
│ └── architecture.md # Detailed architecture documentation
├── requirements.txt # Python dependencies
├── pyproject.toml # Tool configuration (Black, etc.)
└──.ruff.toml # Linting configuration
```

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmXive-follow-up-extending-openrath-ses
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Initialize project structure:
 ```bash
 python code/setup_structure.py
 ```

## Usage

### Quick Start

Run the full pipeline with default settings:
```bash
python code/main.py
```

### CLI Arguments

- `--seed`: Random seed for reproducibility (default: 42)
- `--count`: Number of workflows to generate (default: 500)
- `--resume`: Resume from last checkpoint
- `--sweep`: Run corruption rate sweep (0.05, 0.10, 0.20)

Example:
```bash
python code/main.py --seed 123 --count 100 --sweep
```

### Workflow Generation

Generate ground truth workflows:
```bash
python code/main.py --count 50 --phase generate
```

### Execution and Corruption

Execute workflows and inject corruption:
```bash
python code/main.py --count 50 --phase execute --corruption-rate 0.1
```

### Reconstruction and Analysis

Reconstruct states and calculate metrics:
```bash
python code/main.py --count 50 --phase reconstruct
```

### Statistical Analysis

Run statistical tests on aggregated results:
```bash
python code/analyzers/statistical_test.py
```

## Configuration

Edit `code/config.py` to modify:
- `SEED`: Random seed
- `WORKFLOW_COUNT`: Default number of workflows
- `SWEEP_RATES`: Corruption rates for sensitivity analysis
- Directory paths for data storage

## Output Artifacts

### Data Files
- `data/raw/workflows/{id}_ground_truth.json`: Ground truth states
- `data/processed/corrupted_logs/`: Corrupted log artifacts
- `data/processed/corruption_map.json`: Corruption status map
- `data/processed/results/aggregated_metrics.json`: Final metrics
- `data/processed/results/{id}_reconstruction_result.json`: Per-workflow results

### State Files
- `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml`: Checkpoints and artifact hashes

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

Run all tests:
```bash
pytest -v
```

## Performance

The pipeline is optimized for:
- < 6 hours runtime for full sweep
- < 4GB RAM usage
- Batched processing and streaming for large datasets

## Contributing

1. Ensure all tests pass: `pytest -v`
2. Lint code: `ruff check code/`
3. Format code: `black code/`
4. Submit pull request

## License

[License information]

## References

- OpenRath: Session-Centered Runtime State for Agent Systems
- Cochran's Q test for binary outcomes
- McNemar's test for paired comparisons
- Holm-Bonferroni correction for multiple comparisons
