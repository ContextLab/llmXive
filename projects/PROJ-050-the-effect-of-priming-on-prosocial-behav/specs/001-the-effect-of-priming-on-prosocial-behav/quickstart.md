# Quickstart: The Effect of Priming on Prosocial Behavior in Online Communities

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-050-the-effect-of-priming-on-prosocial-behav
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Data Ingestion & Preprocessing
Download and process the data:
```bash
python code/data/download.py
python code/data/preprocess.py
```
*Output*: `data/processed/comments_anonymized.csv`

### Step 2: Scoring
Compute sentiment and prosocial scores:
```bash
python code/data/score.py
```
*Output*: `data/processed/scored_comments.csv`

### Step 3: Validation (Manual Annotation Required)
This step requires **human intervention** to ensure construct validity.
1. Run the extraction script to get a stratified sample:
   ```bash
   python code/validation/kappa.py --extract
   ```
2. Manually annotate the generated sample file (`data/validation_sample.csv`) using the provided codebook. Two independent raters must code the "prosocial action" binary flag.
3. Run the calculation script with the annotated file:
   ```bash
   python code/validation/kappa.py --calculate
   ```
*Output*: `results/validation_report.json` (Must show Kappa ≥ 0.7).

### Step 4: Statistical Analysis
Run the analysis (LMM):
```bash
python code/analysis/stats.py
python code/analysis/viz.py
```
*Output*: `results/analysis_report.json`, `results/boxplot.png`

## Validation
To verify the prosocial lexicon and VADER scores:
```bash
python code/validation/kappa.py --calculate
```
*Expected*: Cohen's Kappa ≥ 0.7 in `results/validation_report.json`.

## Troubleshooting
- **Memory Error**: Reduce the sample size in `code/config.py` (e.g., `MAX_COMMENTS = 5000`).
- **Dataset Missing**: Ensure the HuggingFace URL in `code/config.py` is accessible.
- **PII Leak**: Run `python code/data/check_pii.py` to scan `data/processed/` for plaintext usernames.