# Quickstart Guide

## Prerequisites

Ensure you have the following installed:
- Python 3.11 or higher
- pip
- MRtrix3 (optional, for real dMRI preprocessing; simulated path skips this)

## Setup

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd llmXive
 ```

2. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Configure environment**:
 Create a `.env` file in the root directory:
 ```env
 DATA_ROOT=./data
 SIMULATION_SEED=42
 LOG_LEVEL=INFO
 ```

4. **Initialize directories**:
 ```bash
 python code/main.py --init
 ```
 This creates `data/raw`, `data/processed`, `data/results`, and `figures`.

## Running the Pipeline

### Full Execution

To run the entire pipeline from download to final report:

```bash
python code/main.py --config config.yaml
```

### Step-by-Step Execution

If you prefer to run stages manually:

1. **Download Data**:
 ```bash
 python code/data/download.py --subjects sub-001,sub-002
 ```

2. **Preprocess dMRI**:
 ```bash
 python code/data/preprocess_dMRI.py --input data/raw --output data/processed/connectomes
 ```

3. **Simulate EEG**:
 ```bash
 python code/data/simulate_EEG.py --connectomes data/processed/connectomes --output data/processed/eeg
 ```

4. **Compute Metrics**:
 ```bash
 python code/analysis/metrics.py --connectomes data/processed/connectomes --output data/results/network_metrics.csv
 ```

5. **Detect Avalanches**:
 ```bash
 python code/analysis/avalanches.py --eeg data/processed/eeg --output data/results/avalanche_events.csv
 ```

6. **Run Statistics**:
 ```bash
 python code/analysis/stats.py --metrics data/results/network_metrics.csv --avalanches data/results/avalanche_events.csv --output data/results/correlation_report.csv
 ```

## Verification

After running the pipeline, verify the outputs:

```bash
ls data/results/
# Should contain: network_metrics.csv, avalanche_events.csv, correlation_report.csv
```

Check the log file for any warnings or errors:
```bash
tail -f logs/pipeline.log
```

## Troubleshooting

- **Missing MRtrix3**: If preprocessing fails, ensure MRtrix3 is in your PATH. For the simulation-only path, this is not required.
- **Memory Errors**: Reduce the number of subjects in the simulation step.
- **Permission Denied**: Ensure write permissions for `data/` and `logs/`.

## Next Steps

- Review the [API Usage](API_USAGE.md) guide for customization.
- Read the [Data Model](DATA_MODEL.md) to understand the data structures.
- Run the unit tests: `pytest tests/`
