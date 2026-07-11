# Quickstart: llmXive follow-up: extending "Agentic Abstention: Do Agents Know When to Stop Instead of Act?"

## Prerequisites

- Python 3.11+
- Git
- A minimal compute configuration (e.g., a small number of CPU cores and moderate memory) compatible with GitHub Actions free-tier constraints.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-918-llmxive-follow-up-extending-agentic-abst
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Preparation

1. **Generate Synthetic Data**:
   - Run the synthetic agent simulator to generate the primary dataset.
   ```bash
   python code/simulation/synthetic_generator.py --output data/raw/synthetic_dataset.parquet
   ```
   - *Note: Real benchmark data is unverified; synthetic data is the default.*

2. **Verify Checksums**:
   ```bash
   sha256sum data/raw/*.parquet > data/checksums.txt
   ```

## Running the Pipeline

### Step 1: Feature Extraction
```bash
python code/data/extract_features.py \
  --input data/raw/synthetic_dataset.parquet \
  --output data/processed/features.parquet
```

### Step 2: Train Meta-Critic
```bash
python code/models/train_meta_critic.py \
  --input data/processed/features.parquet \
  --output models/meta_critic.pkl
```

### Step 3: Run Simulation
```bash
python code/simulation/run_meta_critic.py \
  --model models/meta_critic.pkl \
  --features data/processed/features.parquet \
  --output results/meta_critic_results.json
```

### Step 4: Statistical Analysis (Survival Analysis)
```bash
python code/analysis/statistical_tests.py \
  --input results/meta_critic_results.json \
  --baseline results/convolve_baseline.json \
  --output results/statistical_results.json
```

### Step 5: Sensitivity Analysis
```bash
python code/analysis/sensitivity_analysis.py \
  --input results/meta_critic_results.json \
  --thresholds 0.4,0.45,0.5,0.55,0.6 \
  --output results/sensitivity_analysis.csv
```

## Validation

1. **Schema Validation**:
   ```bash
   pytest tests/contract/test_dataset_schema.py
   ```

2. **Reproducibility Check**:
   - Re-run pipeline with the same random seed and verify identical outputs.

## Troubleshooting

- **Memory Error**: Reduce dataset subset size or increase RAM (if possible).
- **Missing Dataset**: Synthetic data is used by default. If real data is added, ensure it passes schema validation.
- **Collinearity Warning**: Review feature correlations; adjust model if necessary.

## Next Steps

- Review `research.md` for detailed methodology.
- Run `pytest tests/` for full test suite.
- Contribute to `paper/` with results from `results/`.