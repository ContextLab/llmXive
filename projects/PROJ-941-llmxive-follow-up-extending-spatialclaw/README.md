# llmXive: SpatialClaw Restriction Follow-up

This project implements a restricted 2D action space agent ("SpatialClaw") and compares its performance against a 3D baseline.
The goal is to quantify the information loss and performance degradation when an agent is restricted to 2D geometric operations
(using `shapely` and `numpy`) while attempting to solve 3D spatial reasoning tasks.

## Prerequisites

- Python 3.9+
- pip
- A Unix-like environment (Linux/macOS) or WSL2 on Windows.

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-941-llmxive-follow-up-extending-spatialclaw
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

## Configuration

Before running the full pipeline, ensure the power analysis configuration is set correctly in `data/power_config.yaml`.
This file defines the statistical parameters (effect size, power, alpha) used to determine the required dataset size.

```yaml
# data/power_config.yaml
effect_size: 0.5
power: 0.8
alpha: 0.05
description: "Default power analysis configuration for SpatialClaw comparison"
```

## Usage Examples

The project is designed to be run as a sequential pipeline via `code/main.py`. However, individual components can be executed independently for debugging or specific analysis tasks.

### 1. Run the Full Pipeline (Orchestration)

The main entry point handles budget validation, data generation, baseline execution, 2D agent execution, and statistical analysis.

```bash
python code/main.py
```

This will:
1. Check the power analysis budget (abort if estimated runtime > 6 hours).
2. Generate the "Synthetic SpatialClaw Proxy" dataset (`data/raw/synthetic_spatialclaw_v1.json`).
3. Run the 3D Baseline Agent on the generated tasks.
4. Run the 2D Restricted Agent on the same tasks.
5. Perform paired statistical comparisons and sensitivity analysis.
6. Save results to `results/analysis/`.

### 2. Generate Dataset Only

To generate the dataset without running the agents:

```bash
python code/data/generator.py --output data/raw/synthetic_spatialclaw_v1.json
```

### 3. Run Baseline Agent (3D)

To re-run the 3D baseline on an existing dataset:

```bash
python code/agents/baseline_3d.py --input data/raw/synthetic_spatialclaw_v1.json --output results/logs/baseline_run.json
```

### 4. Run 2D Restricted Agent

To run the restricted 2D agent:

```bash
python code/agents/agent_2d.py --input data/raw/synthetic_spatialclaw_v1.json --output results/logs/agent_2d_run.json
```

*Note: This execution is wrapped by the `restricted_kernel` which blocks imports of 3D libraries like `trimesh` and `pytorch3d`.*

### 5. Statistical Analysis & Sensitivity Report

To perform the statistical comparison and generate the sensitivity report (requires previous agent runs):

```bash
python code/stats/sensitivity.py --baseline results/logs/baseline_run.json --agent results/logs/agent_2d_run.json --output results/analysis/sensitivity_report.csv
```

### 6. Power Analysis

To manually run the power analysis and validate the budget:

```bash
python code/stats/power_analysis.py
```

Output will be saved to `results/analysis/power_analysis_summary.json`.

## Project Structure

```text
.
├── code/
│ ├── agents/ # 2D Agent and 3D Baseline implementations
│ ├── data/ # Dataset generation and loading
│ ├── kernel/ # Restricted kernel enforcing 2D policy
│ ├── metrics/ # Metrics collection and comparison
│ ├── stats/ # Statistical tests and sensitivity analysis
│ ├── tools/ # Utilities for profiling and API docs
│ ├── utils/ # Logging, reproducibility, memory monitoring
│ └── main.py # Orchestration entry point
├── data/
│ ├── raw/ # Generated datasets (e.g., synthetic_spatialclaw_v1.json)
│ └── power_config.yaml
├── results/
│ ├── analysis/ # Statistical results, CSVs, sensitivity reports
│ ├── logs/ # Execution logs, baseline/agent run logs
│ └── runs/ # Per-run detailed JSON outputs
├── specs/ # Feature specifications and design docs
├── tests/ # Unit and integration tests
├── requirements.txt
└── README.md
```

## Testing

Run the test suite using `pytest`:

```bash
pytest tests/ -v
```

Specific test groups:
- Kernel restrictions: `pytest tests/integration/test_kernel_2d.py`
- Statistical tests: `pytest tests/unit/test_stats.py`

## License

[Project License]