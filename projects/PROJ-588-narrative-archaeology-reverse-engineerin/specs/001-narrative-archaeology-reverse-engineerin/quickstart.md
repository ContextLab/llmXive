# Quickstart: Narrative Archaeology

## Prerequisites

- Python 3.11+
- `pip`
- Access to GitHub Actions (for CI execution)
- Internet connection (for dataset download)

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

### 1. Download Data
```bash
python src/data/download.py
```
This script fetches the Natural Stories dataset from the verified HuggingFace repository and stores it in `data/raw/`.

### 2. Preprocess Data
```bash
python src/data/preprocess.py --subjects 10
```
This script runs nilearn/niworkflows preprocessing on a subject subset.

### 3. Segment Events
```bash
python src/data/segment.py
```
Aligns event labels to the BOLD timecourse.

### 4. Run RSA Analysis
```bash
python src/models/rsa.py
```
Computes dissimilarity matrices and performs permutation testing.

### 5. Run Decoding Analysis
```bash
python src/models/decoder.py
```
Trains linear classifiers and evaluates accuracy.

### 6. Visualize Results
```bash
python src/viz/plot_results.py
```
Generates plots of RSA matrices and decoding accuracy.

## Testing

```bash
pytest tests/
```

## Notes

- The pipeline is designed to run on GitHub Actions free-tier (limited vCPU and RAM).
- Random seeds are pinned for reproducibility.
- All data artifacts are checksummed.