# Quickstart: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Prerequisites

*   Python 3.11+
*   MRtrix3 (for dMRI processing) - *Note: May need system install or Docker if not available on runner.*
*   MNE-Python
*   NetworkX, powerlaw, pandas, numpy, scipy, pytest

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-472-investigating-the-impact-of-network-stru
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install System Dependencies (if running locally)**:
    *   Ensure `mrconvert`, `tckgen`, `tck2connectome` (MRtrix3) are in PATH.
    *   Ensure `mne` is installed.

## Running the Pipeline

The pipeline is executed via the CLI entry point.

```bash
python -m src.cli.run_pipeline
```

### Configuration

*   **Data Sources**: Configured in `config.yaml` to point to the verified HuggingFace URLs.
*   **Thresholds**: Default 75% (configurable via CLI args).
*   **Seeds**: Pinned in `src/utils/seed.py`.

### Expected Output

1.  `data/processed/`: Contains preprocessed matrices and EEG.
2.  `data/results/metrics.csv`: Participant-level metrics.
3.  `data/results/correlations.csv`: Statistical associations (from synthetic validation).
4.  `data/results/collinearity_status.json`: VIF diagnostics (from synthetic validation).
5.  `report.md`: Final summary (including data availability disclaimer).

## Troubleshooting

*   **MRtrix3 not found**: The runner may not have MRtrix3 installed. If so, the pipeline will skip the dMRI processing and use a pre-computed matrix (if available) or fail gracefully with a clear error message.
*   **Memory Error**: The pipeline streams data. If OOM occurs, reduce the number of subjects in `config.yaml`.
*   **Power-law Convergence**: If `powerlaw` fails to converge, the participant is excluded from the correlation analysis (FR-005).
*   **No Matched Data**: The pipeline will explicitly state in the report that no matched data exists and that biological association analysis is suspended.