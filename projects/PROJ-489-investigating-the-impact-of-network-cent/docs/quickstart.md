# Quickstart Guide

This guide provides step-by-step instructions to set up and run the **llmXive** pipeline for investigating the impact of network centrality on neural synchrony during sleep stages.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Access to the internet (for initial dataset download)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Project Structure

The project follows this directory structure:

```
.
├── code/ # Python source code
│ ├── main.py # Entry point
│ ├── download.py # Data acquisition
│ ├── preprocess.py # Signal preprocessing
│ ├── metrics.py # Centrality & synchrony metrics
│ ├── analysis.py # Statistical analysis
│ ├── report.py # Report generation
│ └──...
├── data/
│ ├── raw/ # Raw EDF files (downloaded)
│ ├── processed/ # Preprocessed data
│ ├── metrics/ # Computed metrics (SubjectMetrics.csv)
│ └── results/ # Analysis results
├── tests/ # Unit and integration tests
├── docs/ # Documentation
└── README.md # Project overview
```

## Usage

### 1. Data Acquisition and Preprocessing (User Story 1)

Download the Sleep-EDF dataset and preprocess the EEG signals:

```bash
python code/download.py
python code/preprocess.py
```

This will populate `data/raw` with the dataset and `data/processed` with cleaned, epoch-labeled data.

### 2. Metric Computation (User Story 2)

Compute network centrality and neural synchrony metrics:

```bash
python code/metrics.py
```

Output: `data/metrics/SubjectMetrics.csv`

### 3. Statistical Analysis and Reporting (User Story 3)

Perform LME analysis, apply FDR correction, and generate the final report:

```bash
python code/analysis.py
python code/report.py
```

Output:
- `data/results/analysis_results.json`
- `reports/final_report.md`

### Running the Full Pipeline

To execute the entire pipeline in sequence:

```bash
python code/main.py
```

Ensure you have sufficient disk space and memory (recommended: ≥4GB RAM).

## Testing

Run the test suite to verify the installation:

```bash
python -m pytest tests/ -v
```

## Configuration

Edit `code/config.yaml` to adjust:
- Signal processing parameters (filter cutoffs, ICA thresholds)
- Band definitions (theta, alpha, etc.)
- Random seed for reproducibility
- Output paths

## Troubleshooting

- **Missing dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Data download fails**: Check internet connection and verify PhysioNet access.
- **Memory errors**: Reduce the number of subjects or epochs processed at once.

## Data Model

The pipeline processes EEG data from the Sleep-EDF dataset. Key entities:
- **Subject**: Individual participant with waking and sleep recordings.
- **Epoch**: Segmented time window labeled by sleep stage.
- **Connectivity Matrix**: Functional connectivity between electrode pairs.
- **Centrality Metrics**: Degree, betweenness, eigenvector centrality.
- **Synchrony Score**: Mean Phase Lag Index (PLI) per sleep stage.

For a detailed data model diagram, see `docs/data_model.md`.

## Next Steps

- Explore the generated reports in `reports/`.
- Modify `code/config.yaml` to experiment with different parameters.
- Contribute to the project by implementing additional tasks or improving documentation.
