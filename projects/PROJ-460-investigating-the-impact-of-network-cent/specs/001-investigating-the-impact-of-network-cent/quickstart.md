# Quickstart: Investigating Network Centrality in ASD Resting-State fMRI

## Prerequisites

*   Python 3.11+
*   Docker (for fMRIPrep)
*   Git
*   7 GB+ RAM (recommended)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-460-investigating-the-impact-of-network-cent
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### ⚠️ CRITICAL BLOCKER: Real Data Required

**This pipeline is currently BLOCKED.** The `# Verified datasets` block does not contain a valid source for raw ABIDE fMRI data (NIfTI files). The scientific analysis **cannot proceed** without real biological data.

**To Unblock**:
1.  Identify a verified source for raw ABIDE data (e.g., official ABIDE website, verified HuggingFace dataset with NIfTI files).
2.  Update the `# Verified datasets` block in the project specification with the new URL.
3.  Once a valid source is confirmed, the pipeline can be executed as described below.

### Unit Testing (Code Logic Only)

To verify that the code logic (centrality calculation, FDR correction, etc.) functions correctly, you may run unit tests using **mock data**. This does **not** generate scientific results.

```bash
# Run unit tests (uses mock data internally)
pytest code/tests/
```

### Option B: Real Data (Required for Scientific Results)

Once a valid ABIDE source is added to the verified datasets block:

```bash
# Download real data (requires valid credentials/source)
python code/download.py --mode abide --credentials-file .abide_creds

# Run fMRIPrep (CPU mode) - Note: May require batch processing
python code/preprocess.py --mode abide --docker-image fmriprep/fmriprep:23.1.0

# Compute centrality and run stats
python code/analysis/centrality.py
python code/analysis/stats.py

# Generate visualizations
python code/viz/brain_maps.py
```

## Validation

1.  **Check Output Files**:
    *   `data/outputs/stats/group_comparison.json` should exist (only if real data was processed).
    *   `data/outputs/figures/centrality_map.png` should exist (only if real data was processed).

2.  **Run Tests**:
    ```bash
    pytest code/tests/
    ```

3.  **Verify FDR Correction**:
    Ensure `q_value` in the stats output is calculated using the Benjamini-Hochberg procedure.

## Troubleshooting

*   **Memory Error**: If running on real data, reduce the number of subjects or use a smaller atlas (e.g., 200 ROIs instead of 400).
*   **Docker Issues**: Ensure Docker daemon is running and the user has permissions.
*   **No Significant Results**: This is expected if the effect size is small or power is low. Report effect sizes and confidence intervals.
*   **Pipeline Blocked**: If you see a "Pipeline Blocked" message, check the `# Verified datasets` block for a valid fMRI source.
*   **Synthetic Data**: Synthetic data is **NOT** used for scientific results. Unit tests only use mock data.