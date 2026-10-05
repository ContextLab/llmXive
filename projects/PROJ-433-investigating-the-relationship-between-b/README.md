# Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

This project investigates the relationship between brain network dynamics (specifically network reconfigurability) and subjective time perception (measured by DSST scores) using fMRI data from the Human Connectome Project (HCP).

## Project Structure

```
.
├── code/ # Source code modules
│ ├── analysis.py # Statistical analysis (correlations, permutation tests)
│ ├── download.py # HCP data retrieval and verification
│ ├── main.py # Entry point for the pipeline
│ ├── metrics.py # Network reconfigurability computation
│ ├── models.py # Data models (Subject)
│ ├── preprocess.py # fMRIPrep invocation and QC
│ ├── utils.py # Logging, RNG, QC utilities
│ ├── viz.py # Visualization (scatter plots)
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Downloaded raw HCP data
│ ├── processed/ # Preprocessed fMRI data (MNI space)
│ └── results/ # Metrics, statistical results, plots
├── tests/ # Unit tests
├── specs/ # Design documents
└── README.md
```

## Prerequisites

- Python 3.11+
- Docker (for fMRIPrep container)
- HCP account and credentials (for data download)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-name>
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Set up HCP credentials** (environment variables):
 ```bash
 export HCP_USERNAME="your_username"
 export HCP_PASSWORD="your_password"
 ```

## Usage

### Full Pipeline Execution

Run the main pipeline script to execute the entire workflow (download, preprocess, compute metrics, analyze, visualize):

```bash
python code/main.py
```

**Options**:
- `--mode {ci,cluster}`: Run in CI mode (subset of subjects, faster) or cluster mode (full dataset). Default: `ci`.
- `--subjects <list>`: Comma-separated list of subject IDs to process (e.g., `100106,100208`). If not provided, all available subjects are processed.

**Example**:
```bash
python code/main.py --mode ci --subjects 100106
```

### Individual Components

#### Data Download
Download HCP resting-state fMRI and behavioral data:
```bash
python code/download.py
```

#### Preprocessing
Run fMRIPrep on preprocessed data:
```bash
python code/preprocess.py --mode ci
```

#### Metric Computation
Compute network reconfigurability metrics:
```bash
python code/metrics.py
```

#### Statistical Analysis
Perform correlation analysis and permutation testing:
```bash
python code/analysis.py
```

#### Visualization
Generate scatter plots:
```bash
python code/viz.py
```

## Output Files

- `data/preprocess_log.txt`: Logs from download and preprocessing steps.
- `data/analysis_log.txt`: Logs from analysis steps.
- `data/results/metrics_{subject_id}.json`: Network reconfigurability metrics per subject.
- `data/processed/metrics_aggregated.tsv`: Aggregated metrics across all subjects.
- `data/analysis_results.tsv`: Statistical summary (correlation coefficients, p-values, effect sizes).
- `data/results/permutation_results.tsv`: Permutation test results.
- `data/results/plot_{metric}_{behavior}.png`: Scatter plots with confidence intervals.

## Testing

Run unit tests:
```bash
pytest tests/
```

## Logging

All operations log to:
- `data/preprocess_log.txt`: Download and preprocessing logs.
- `data/analysis_log.txt`: Analysis and metric computation logs.

Logs include ISO timestamps and are written using the `setup_logger()` utility from `code/utils.py`.

## Data Availability

If HCP data is unavailable (e.g., missing credentials, network issues), the pipeline will:
1. Log "N/A - Data Unavailable" to `data/preprocess_log.txt`.
2. Skip preprocessing and metric computation steps.
3. Exit gracefully without crashing.

This ensures the pipeline can be tested in CI environments without requiring real data.

## License

[Insert License Information Here]

## Acknowledgments

- Human Connectome Project (HCP) for providing the fMRI and behavioral data.
- fMRIPrep for preprocessing pipeline.
- Schaefer et al. for the parcellation atlas.