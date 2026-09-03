# llmXive: From Chatbot to Digital Colleague

A reproducible research pipeline for simulating persistent digital colleagues with overlapping skill libraries.

## Prerequisites

- Python 3.9+
- pip
- System RAM: ≥ 8 GB recommended for full dataset generation

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-975-llmxive-follow-up-extending-from-chatbot
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Quick Start

### 1. Project Setup
Ensure the directory structure is created:
```bash
python code/setup_directories.py
```

### 2. Configure Seeds (Optional)
Set environment variables to override defaults in `code/config.py`:
```bash
export SEED_A=42
export SEED_B=123
export OVERLAP_LEVEL=medium
```

### 3. Generate Synthetic Data
Generate 500 multi-step tasks and a configurable skill library:
```bash
python code/generate_data.py
```
**Outputs**:
- `data/raw/tasks.json`
- `data/raw/skills.json`
- `state/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml` (checksums)

### 4. Run Baseline Experiment (No Pruning)
Execute the agent with pruning disabled across library sizes [10, 30, 50, 100]:
```bash
python code/run_baseline.py
```
**Outputs**:
- `data/results/experiment_log_baseline.csv`
- `data/results/baseline_metrics.json`

### 5. Run Pruning Experiment
Execute the agent with the "Safe Pruning" heuristic enabled:
```bash
python code/run_experiment.py
```
**Outputs**:
- `data/results/experiment_log.csv`

### 6. Analyze Results
Perform statistical analysis, calculate VIF, and identify the tipping point:
```bash
python code/analyze.py
```
**Outputs**:
- `data/results/tipping_point.json`
- `data/results/final_analysis.json`
- `data/results/sensitivity_report.json`

## Verification

To verify the logging infrastructure:
```bash
python code/verify_logging.py
```

## Configuration

Edit `code/config.py` to modify:
- `SEED_A`, `SEED_B`: Random seeds for reproducibility
- `OVERLAP_LEVEL`: 'low', 'medium', or 'high' semantic overlap
- `PRUNING_INTERVAL`: Number of tasks between pruning checks (default: 10)

## Troubleshooting

- **Memory Errors**: The script checks for >7GB RAM usage. If exceeded, it will fail with "Memory Limit Exceeded". Reduce `OVERLAP_LEVEL` or run on a machine with more RAM.
- **Missing Modules**: Ensure all dependencies in `requirements.txt` are installed.
- **Data Integrity**: Checksums are stored in `state/projects/...yaml`. If data files are modified, regeneration is required.