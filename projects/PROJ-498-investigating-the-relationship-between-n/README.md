# PROJ-498: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

This project investigates the relationship between pre-stimulus frontoparietal neural synchrony (PLV/wPLI in theta and gamma bands) and attention switching costs using task-switching EEG data from OpenNeuro.

## Prerequisites

- Python 3.10+
- pip
- Access to the internet (for dataset discovery and download)

## Setup

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

To run the full pipeline (dataset discovery, download, preprocessing, synchrony computation, and correlation analysis):

```bash
python code/main.py
```

**Note:** No manual dataset ID is required. The pipeline automatically discovers a valid task-switching dataset from OpenNeuro and saves the selected ID to `data/selected_dataset_id.txt`. If no dataset is found, a data gap report is generated and execution halts.

## Project Structure

- `code/`: Source code for the pipeline
 - `main.py`: Orchestrator
 - `download.py`: Dataset discovery and download
 - `preprocess.py`: EEG preprocessing (filtering, ICA, epoching)
 - `synchrony.py`: Synchrony metric computation (PLV/wPLI)
 - `analysis.py`: Statistical correlation and mixed-effects modeling
- `data/`: Input and output data
 - `raw/`: Downloaded raw EEG data
 - `processed/`: Preprocessed and epoched data
 - `metrics/`: Computed synchrony and correlation metrics
- `tests/`: Unit and integration tests
- `contracts/`: Schema definitions for output artifacts

## Output Artifacts

- `data/processed/`: Cleaned epochs per subject
- `data/metrics/synchrony_metrics.csv`: Synchrony values per electrode pair and band
- `data/metrics/correlation_results.json`: Correlation results and p-values
- `data/metrics/sensitivity_report.json`: Sensitivity analysis results
- `results_summary.md`: Final results summary with associational framing

## License

[Insert License]