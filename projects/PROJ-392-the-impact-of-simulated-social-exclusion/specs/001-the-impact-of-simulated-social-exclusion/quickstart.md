# Quickstart: The Impact of Simulated Social Exclusion on Neural Responses to Reward

## Prerequisites

-   Python +
-   `pip`
-   Sufficient free disk space
-   ~7 GB RAM

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-392-the-impact-of-simulated-social-exclusion/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import nibabel, pandas, numpy, scipy, matplotlib, nilearn; print('All dependencies OK')"
    ```

## Running the Pipeline

The pipeline is executed via the main script `code/pipeline/run_pipeline.py`.

### Step 1: Data Download (Merged Datasets)
Download verified Exclusion and Reward datasets.
```bash
python code/data_download/download_openneuro.py --dataset-id ds,dsXXXXXX --output data/raw-fmri
```
*Note: If no verified datasets are found, the pipeline will halt and log an error. Synthetic data is NOT generated.*

### Step 2: Preprocessing
Runs slice timing, realignment, normalization, and smoothing.
```bash
python code/preprocess/run_preprocessing.py --input data/raw-fmri --output data/processed-fmri --smoothing --nthreads --mem-mb
```
*Note: This step respects the 7 GB RAM limit by processing in batches and generates provenance files.*

### Step 3: ROI Extraction & Analysis
Extracts betas and runs group t-tests.
```bash
python code/analysis/run_analysis.py --processed data/processed-fmri --output data/results
```

### Step 4: Visualization
Generates plots and reports, including SPM overlays.
```bash
python code/visualization/plot_results.py --input data/results --output docs/figures
```

### Step 5: Sensitivity Analysis
Sweeps smoothing kernels (small, medium, large).
```bash
python code/analysis/sensitivity_analysis.py --processed data/processed-fmri --output data/results
```

### Step 6: Reporting & Validation
Generates Power Limitations Report and validates framing.
```bash
python code/utils/report_generator.py --input data/results --output docs/report.md
python code/utils/framing_validator.py --input docs/report.md
```

## Verification

Run the test suite to ensure the pipeline is reproducible:
```bash
pytest tests/ -v
```

## Expected Outputs

-   `data/results/group_analysis.json`: Contains t-stats, p-values (Bonferroni), and effect sizes.
-   `data/results/preprocessing_metrics.json`: Contains completion rate (target ≥90%).
-   `docs/figures/roi_barplot.png`: Bar plot with error bars.
-   `docs/figures/spm_overlay.png`: Statistical parametric map overlaid on MNI template.
-   `docs/report.md`: Final report with associational framing and power limitations.

## Troubleshooting

-   **Memory Error**: Reduce batch size in `code/preprocess/run_preprocessing.py`.
-   **Missing Data**: If the download fails, the pipeline halts with an error. **No synthetic data is generated.**
-   **CUDA Error**: Ensure no GPU flags are passed; the code is CPU-only.
-   **Dataset Mismatch**: If no compatible datasets are found, the pipeline halts and logs the specific missing datasets.