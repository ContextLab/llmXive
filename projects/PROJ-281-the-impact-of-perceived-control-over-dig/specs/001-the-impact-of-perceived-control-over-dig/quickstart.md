# Quickstart: 001-perceived-control-anxiety

## Prerequisites

- Python 3.10+
- `pip` or `poetry`
- Internet access (for initial download only)

## Installation

1. **Clone the repository** (or navigate to the project directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions to ensure reproducibility.*

## Running the Pipeline

Execute the full pipeline from ingestion to visualization:

```bash
python code/main.py
```

### Steps Performed
1. **Ingestion**: Downloads the dataset from HuggingFace and saves to `data/raw/`.
2. **Anxiety Scoring**: Runs the pre-trained model on text (CPU) and saves scores to `data/processed/`.
3. **Control Proxy Extraction**: Extracts metadata-based proxies and saves to `data/processed/`.
4. **Analysis**: Merges data, filters by confidence, runs Shapiro-Wilk, and calculates correlation.
5. **Visualization**: Generates `results/plot.png`.

## Verifying Results

- **Check Logs**: Look for `INFO: Correlation coefficient: ...` and `INFO: P-value: ...`.
- **Visual Output**: Open `results/plot.png` to see the scatter plot.
- **Data Integrity**: Verify `data/processed/final_analysis.csv` contains no nulls in `anxiety_score` or `control_proxy`.

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, reduce the sample size in `code/config.py` (e.g., `SAMPLE_SIZE = 5000`).
- **Model Load Error**: Ensure `transformers` and `torch` are installed for CPU. Do not install `torch` with CUDA support.
- **Dataset Missing**: If the dataset is not found, check the `# Verified datasets` block for the correct ID.
