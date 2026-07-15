# Quickstart Guide: llmXive Research Pipeline

This guide provides instructions for setting up the environment and running the initial experiments for the "Input Noise Injection for Latent Separability" study.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- At least 16GB of available RAM (recommended 32GB for full dataset processing)
- CPU-only execution (no GPU required)

## 1. Environment Setup

### Option A: Automated Setup (Recommended)

Run the provided setup script to create a virtual environment and install all dependencies:

```bash
cd <project-root>
bash code/scripts/setup.sh
```

### Option B: Manual Setup

1. Create a virtual environment:
 ```bash
 python3 -m venv venv
 ```

2. Activate the virtual environment:
 ```bash
 # Linux/macOS
 source venv/bin/activate

 # Windows
 venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## 2. Verify Installation

Run the following command to verify that all required packages are installed:

```bash
python -c "import torch, transformers, pandas, numpy, sklearn, bertscore, sentence_transformers; print('All dependencies installed successfully.')"
```

## 3. Running the Pipeline

### Baseline Extraction (User Story 1)

To extract baseline latent vectors from the reasoning dataset:

```bash
# Ensure you are in the project root and virtual environment is active
python code/main.py --mode baseline
```

This will:
1. Load the BigBench reasoning dataset
2. Pair questions by task type
3. Extract hidden states for "thought" tokens
4. Save normalized vectors to `data/processed/baseline_vectors.csv`

### Noise Injection & Perturbation (User Story 2)

To run the noise injection sweep and validity checks:

```bash
python code/main.py --mode perturbation --sigma-range 0.01 0.5
```

This will:
1. Iterate over a range of $\sigma$ values
2. Inject Gaussian noise into input embeddings
3. Project to nearest valid tokens
4. Run input drift and output validity checks
5. Save results to `data/processed/perturbed_vectors.csv` and `data/processed/validity_log.csv`

### Statistical Analysis (User Story 3)

To perform separability analysis:

```bash
python code/main.py --mode analysis
```

This will:
1. Load filtered vectors from previous steps
2. Run hypothesis tests (t-test or Wilcoxon)
3. Generate sensitivity reports
4. Save results to `data/processed/statistical_results.json`

## 4. Output Files

After running the pipeline, you will find the following artifacts:

- `data/processed/pairing_config.json`: Configuration for question pairing
- `data/processed/baseline_vectors.csv`: Baseline latent vectors (Unit Story 1)
- `data/processed/filtered_pairs_input_drift.csv`: Pairs filtered due to input drift
- `data/processed/perturbed_vectors.csv`: Noise-augmented vectors (User Story 2)
- `data/processed/validity_log.csv`: Log of validity check results
- `data/processed/statistical_results.json`: Final statistical analysis (User Story 3)
- `data/processed/sensitivity_report.json`: Trade-off curves and collapse points

## 5. Troubleshooting

### Memory Issues

If you encounter memory errors:
- Ensure you have at least 16GB of available RAM
- The pipeline uses streaming/batching by default to respect the 7GB limit
- Reduce the dataset subset size if necessary

### Data Fetch Errors

The pipeline fetches real data from the HuggingFace Hub. If the fetch fails:
- Check your internet connection
- Ensure you have access to the HuggingFace Hub
- The script will fail loudly with a clear error message (no synthetic fallback)

### CPU Performance

Since this pipeline is CPU-only, processing may take time. Consider:
- Running on a subset of the dataset for testing
- Using a machine with more CPU cores

## 6. Next Steps

After completing the baseline and perturbation runs:
1. Review the `validity_log.csv` to understand which pairs passed/failed checks
2. Examine the `sensitivity_report.json` for the validity collapse point
3. Analyze the statistical results to determine if noise injection significantly increased latent separability

For detailed implementation notes, refer to the `specs/001-lm-axive-noise-injection/` directory.