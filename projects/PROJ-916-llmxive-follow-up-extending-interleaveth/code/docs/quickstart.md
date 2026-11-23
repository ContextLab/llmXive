# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip
- PyTorch (CPU version)

## Installation

```bash
# Clone the repository
git clone
cd llmxive

# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install
```

## Running the Pipeline

### 1. Data Preparation

The pipeline requires real datasets (WISE, RISE). Ensure they are accessible:

```bash
# The loader will attempt to stream these datasets
# If unavailable, it will raise a ValueError
```

### 2. Run the Simulator (US1)

```bash
python code/scripts/run_simulator.py --mode noisy --prompt "A cat sitting on a mat"
```

### 3. Run the Agentic Loop (US2)

```bash
python code/scripts/run_agentic_loop.py --threshold 0.8 --max-time 30
```

### 4. Run Statistical Analysis (US3)

```bash
python code/scripts/run_analysis.py --baseline single-pass
```

## Configuration

Edit `src/config.py` to adjust:
- Random seeds
- Critic thresholds (0.7, 0.8, 0.9)
- Batch sizes
- Timeout limits

## Output

- Simulator outputs: `data/intermediate/simulator_results.json`
- Agentic loop logs: `data/intermediate/trajectory_logs.json`
- Statistical report: `data/intermediate/statistical_significance_report.md`

## Troubleshooting

- **Dataset unavailable**: Ensure WISE and RISE datasets are accessible via HuggingFace
- **OOM errors**: Reduce batch size or enable memory profiling
- **Timeout errors**: Increase timeout limit in config
