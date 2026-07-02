# Quickstart: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Prerequisites
- Python 3.11+
- Git
- Access to the verified MyPersonality dataset (Holistic AI HuggingFace hub)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-138-the-effects-of-gamified-habit-tracking-o
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *All packages are CPU‑compatible and version‑pinned.*

## Data Setup

1. **Download the dataset** (expects the verified subset containing habit‑tracking fields):
   ```bash
   mkdir -p data/raw
   wget "https://huggingface.co/datasets/holistic-ai/Personality_mypersonality/resolve/main/data/test-00000-of-00001-c96a814948b69df7.parquet" -O data/raw/mypersonality.parquet
   ```

2. **Checksum verification** (optional but required by the Constitution):
   ```bash
   sha256sum data/raw/mypersonality.parquet > data/raw/checksum.txt
   ```

## Running the Full Pipeline

```bash
python code/main.py
```

The script will:

1. **Ingest & validate** the dataset (Phase 1).  
2. **Create** `data/consent/` and store any consent documentation found with the dataset.  
3. **Validate** the cleaned CSV against `contracts/dataset.schema.yaml`.  
4. **Fit** the logistic regression model, run bootstrapping, cross‑validation, and sensitivity analysis.  
5. **Generate** visualizations (`docs/plots/`) and the final HTML report (`docs/report.html`).  
6. **Validate** the results JSON against `contracts/output.schema.yaml`.

### Expected Outputs
- `data/processed/cleaned_data.csv` – analysis‑ready dataset.  
- `data/processed/results.json` – model coefficients and bootstrap CI.  
- `docs/plots/` – adherence distribution, interaction plot, bootstrap histogram.  
- `docs/report.html` – complete reproducible research report.  

## Testing

Run the test suite to ensure contract compliance and logical correctness:

```bash
pytest tests/ -v
```

- **Contract Tests** (`tests/contract/`) confirm that both input and output files satisfy their respective JSON‑Schema definitions.  
- **Unit Tests** (`tests/unit/`) verify adherence flag logic and VIF handling.  
- **Integration Test** (`tests/integration/`) executes the pipeline on a tiny synthetic dataset to confirm end‑to‑end functionality.

## Troubleshooting

- **Data Insufficiency**: If required habit‑tracking columns are missing, the pipeline stops with a clear error; check the dataset version or contact the data provider.  
- **Model Convergence Issues**: The pipeline automatically adds a small L2 regularisation term and retries; consult `logs/modeling.log` for details.  
- **Memory Limits**: The dataset is small (< 10 MB); if memory errors occur, reduce the number of bootstrap iterations in `code/config.py`.

## Next Steps

- Review the generated `docs/report.html` for statistical results and visualizations.  
- Verify that all Success Criteria (SC‑001 – SC‑005) are satisfied; note that SC‑005 now measures **p‑value stability** rather than false‑positive rates, per the updated methodology.  
- Submit the results for peer review.
