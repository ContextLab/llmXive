# Quickstart: Predicting Plant Pathogen Host Range

## Prerequisites

*   Python 3.11+
*   `pip`
*   Internet connection (for downloading NCBI/PHI-base data)
*   **Note**: Requires `hmmer` and `hmmsearch` installed in PATH (for EffectorP 3.0). **No simplified fallback is available.** If tools are unavailable, the pipeline will fail with a critical error to preserve construct validity.

## Installation

1.  **Clone the repository** (assuming this is part of the larger project).
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

### 1. Full Pipeline (Training & Evaluation)

Run the end-to-end pipeline on the default pathogen dataset (using pre-computed features):

```bash
./code/cli/run_pipeline.sh
```

**Output**:
*   `data/models/model.pkl`: Trained logistic regression model.
*   `data/processed/feature_matrix.csv`: Extracted features (from pre-computed cache).
*   `data/reports/significant_features.tsv`: Statistically significant genomic features.
*   `data/reports/data_quality_report.json`: Missing data report.
*   `data/reports/sensitivity_analysis.json`: Sensitivity analysis results.
*   `data/reports/bias_awareness.json`: Bias awareness report.
*   `reports/pipeline.log`: Execution log.

### 2. Predict Host Range for a Novel Pathogen

To predict the host range of a newly sequenced pathogen:

```bash
./code/cli/predict_host_range.sh --genome path/to/novel_genome.fa
```

**Output**:
*   `prediction.csv`: Probability scores for each known host species.

## Expected Runtime & Resources

*   **Full Pipeline**: ~3-4 hours on a standard CPU (2 cores, 7GB RAM) (Modeling + Eval only; feature extraction is pre-computed).
*   **Prediction**: < 30 seconds per genome.
*   **Memory**: Peak usage ~3.5GB.

## Troubleshooting

*   **Error: "No interactions found for pathogen X"**: The pipeline halts if a pathogen has no host records in PHI-base/Interactome3D. Check the accession number or update the interaction database.
*   **Error: "Memory limit exceeded"**: Ensure you are not running other heavy processes. The pipeline is optimized for standard memory constraints.
*   **Error: "EffectorP/antiSMASH not found"**: The pipeline requires these tools for feature extraction. If you are running the full extraction (offline), ensure they are installed. If you are running the CI pipeline, ensure the pre-computed vectors are present in `data/raw/`.
*   **Error: "Pre-computed vectors missing"**: The pipeline cannot run without the pre-computed feature vectors. Contact the project maintainer to generate the cache or run the offline extraction step.