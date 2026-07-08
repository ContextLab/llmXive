# Quickstart: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Prerequisites

- Python 3.11+
- Git
- Access to ADReSS GitHub repository (raw text)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd specs/001-statistical-cognitive-decline
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `spaCy` and `en_core_web_sm` model will be installed automatically.*

## Running the Pipeline

### 1. Data Ingestion
Download and clean the ADReSS dataset:
```bash
python code/ingestion.py --dataset adress --output data/interim/cleaned_transcripts.csv
```
*Note: The pipeline fetches raw text from the ADReSS GitHub repository. DementiaBank is excluded.*

### 2. Feature Extraction
Compute linguistic features:
```bash
python code/features.py --input data/interim/cleaned_transcripts.csv --output data/processed/features.csv
```
*Note: Noun/Verb ratio is set to NaN if zero nouns or verbs are detected.*

### 3. Statistical Analysis
Run hypothesis tests and corrections:
```bash
python code/stats.py --input data/processed/features.csv --output data/processed/stats_results.json
```
*Note: Uses Rank-Biserial Correlation for effect sizes.*

### 4. Predictive Modeling
Train models and perform cross-validation:
```bash
python code/modeling.py --input data/processed/features.csv --output data/processed/model_results.json
```
*Note: Evaluates on held-out test set only; Training AUC is not reported.*

### 5. Full Pipeline
Run all steps in sequence:
```bash
python code/main.py
```

## Verification

- **Unit Tests**:
  ```bash
  pytest tests/unit/
  ```
- **Contract Tests**:
  ```bash
  pytest tests/contract/
  ```
- **Integration Test**:
  ```bash
  pytest tests/integration/test_pipeline.py
  ```

## Expected Outputs

- `data/processed/features.csv`: Feature matrix (with NaN for invalid Noun/Verb ratios).
- `data/processed/stats_results.json`: P-values, effect sizes (Rank-Biserial), Bonferroni corrections.
- `data/processed/model_results.json`: AUC, accuracy, F1-score, nested CV metrics.