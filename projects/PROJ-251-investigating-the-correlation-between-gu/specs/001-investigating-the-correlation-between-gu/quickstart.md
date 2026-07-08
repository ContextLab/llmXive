# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

## Prerequisites

- Python 3.11+
- `pip`
- Internet access (for dataset download)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The pipeline is configured to use NCBI SRA accession **SRP053178** as the primary data source.
*Note: If this dataset is unavailable, the pipeline will halt with a clear error.*

## Running the Pipeline

Execute the main pipeline script:
```bash
python code/main.py
```

This will:
1. Download and validate data from SRP053178.
2. Filter for complete subjects (N ≥ 50).
3. Exclude zero-variance taxa and apply CLR transformation.
4. Run Pseudocount Sensitivity Analysis.
5. Run Spearman correlation with BH correction.
6. Train Random Forest with nested CV.
7. Run Permutation Baseline (Microbiome Shuffle) and Threshold Sweep.
8. Generate reports in `data/results/`.

## Verifying Results

Check the `data/results/` directory for:
- `correlations.csv`: Significant taxa.
- `model_metrics.json`: Cross-validation accuracy.
- `sensitivity_analysis.csv`: Threshold stability and robustness.
- `model_significance.json`: Result of the permutation baseline test (p < 0.05?).

## Troubleshooting

- **Error: Insufficient Sample Size**: The dataset has < 50 subjects with complete data.
- **Error: DataUnavailable**: The specified dataset URL (SRP053178) is unreachable or invalid.
- **Memory Error**: The dataset is too large. Try enabling sampling in `config.yaml`.
- **Warning: Absolute Fallback**: Pre-vaccination titers were missing; responder status defined by absolute titer only.