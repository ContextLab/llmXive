# Quickstart: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Prerequisites

- Python 3.11+
- 7GB+ RAM
- 14GB+ Disk Space
- Git

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Running the Pipeline

The pipeline is executed via a single entry point script.

```bash
# Run the full pipeline (Data -> Split -> Train -> Eval -> Audit)
python code/main_pipeline.py
```

### Step-by-Step Execution

1.  **Constitution Audit (Hard Gate)**:
    - Verifies `constitution.md` title.
    - Exits with code 1 if title is "First-Principles".
    - Output: `data/results/constitution_title_audit.json`.

2.  **Data Ingestion**:
    - Downloads verified HuggingFace datasets (`matbench/elasticity`).
    - Validates schema (elastic_tensor, structure).
    - Checksums raw files.
    - Output: `data/raw/*.parquet`.

3.  **Graph Construction**:
    - Converts structures to graphs (PBC-aware).
    - Output: `data/processed/graphs_v1.parquet`.

4.  **Inter-Family Split**:
    - Stratifies by composite key (Space Group + Motif).
    - Output: `data/processed/split_indices.json`.

5.  **Training**:
    - Trains GNN on CPU (Weighted Loss).
    - Logs memory usage.
    - Output: `data/processed/model_v1.pt`, `data/results/training_logs.json`.

6.  **Evaluation**:
    - Computes RMSE and MAPE on unseen families.
    - Computes 95% CI for MAPE.
    - Output: `data/results/generalization_metrics.json`.

7.  **Inference Benchmark**:
    - Measures time per material.
    - Output: `data/results/inference_benchmark.json`.

8.  **Feature Importance**:
    - Runs SHAP with interaction values.
    - Output: `data/results/feature_importance_report.md`.

## 4. Verification

To verify the results:

```bash
# Check if the model passed the MAPE/RMSE threshold
python code/utils/verify_success_criteria.py --input data/results/generalization_metrics.json

# Verify constitution audit
python code/utils/verify_constitution_title.py
```

## 5. Troubleshooting

- **Memory Error**: Reduce `batch_size` in `code/model/train.py` or enable streaming in `code/data/loader.py`.
- **Constitution Error**: Ensure `constitution.md` title is updated to "Structure-Only Surrogate Model".
- **Data Missing**: Check network connectivity to HuggingFace. Verify checksums in `state/...yaml`.