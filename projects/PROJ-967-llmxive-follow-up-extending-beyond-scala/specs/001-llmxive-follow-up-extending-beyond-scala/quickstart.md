# Quickstart: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Prerequisites
- Python 3.11+
- Git
- Access to the Z-Reward dataset (via HuggingFace or local `data/raw/`)

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala
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

The pipeline is executed sequentially. Each step generates artifacts for the next.

### Step 1: Ingest Data
Loads and cleans the Z-Reward dataset.
```bash
python code/ingest.py
```
*Output*: `data/processed/cleaned_data.csv`

### Step 2: Engineer Features
Calculates entanglement scores and fidelity loss.
```bash
python code/features.py
```
*Output*: `data/processed/features_with_target.csv`

### Step 3: Train & Evaluate
Trains the Random Forest model with 5-fold CV and computes metrics.
```bash
python code/train.py
```
*Output*: `results/results.json`, `results/model.pkl`

### Step 4: (Optional) Inspect Results
View the final metrics:
```bash
cat results/results.json
```

## Verification

To verify the setup, run the test suite:
```bash
pytest tests/
```

## Troubleshooting

- **Memory Error**: If `cleaned_data.csv` is too large, edit `code/ingest.py` to enable sampling (set `sample_size=10000`).
- **Missing Dataset**: Ensure `data/raw/` contains the Z-Reward files or that you are logged into HuggingFace (`huggingface-cli login`).
- **Data Gap**: If the script fails with "Data Gap", the dataset lacks required pre-computed scores. The pipeline cannot proceed without them.