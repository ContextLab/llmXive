# Quickstart: Evaluating the Effectiveness of Retrieval-Augmented Generation for Code Search

## Prerequisites

- Python 3.11+
- `pip`
- Sufficient RAM (minimum), 14GB disk (minimum)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download the dataset** (automatically via `ir-datasets` on first run):
   ```bash
   python src/data/download.py
   ```

## Running the Pipeline

### Standard Run (a series of queries)

The research question remains: [Research Question]
The method remains: [Method]
The references remain: [References]
```bash
python src/cli/main.py --queries 50 --mode standard
```
- Downloads CodeSearchNet.
- Computes semantic descriptors (query/GT only).
- Runs BM25, Dual-Encoder, and RAG pipelines.
- Outputs `data/processed/results.csv` and `data/processed/plots/`.

### Resource-Constrained Run
```bash
python src/cli/main.py --queries 50 --mode constrained
```
- Limits FAISS index to 1GB RAM.
- Uses a multi-layer transformer for generation.
- Outputs `data/processed/degradation_report.csv`.

### Correlation Analysis
```bash
python src/analysis/correlation.py --input data/processed/results.csv
```
- Computes Spearman's rho, Pearson's r, and multivariate regression.
- Outputs `data/processed/correlations.json`.

### Control Experiment (Masking)
```bash
python src/analysis/control_experiment.py --input data/processed/results.csv
```
- Masks API/doc tokens and re-runs correlation.
- Outputs `data/processed/control_results.json`.

### Label Noise Estimation
```bash
python src/analysis/label_noise.py --input data/raw/codesearchnet.jsonl
```
- Performs manual spot-check (or simulates if automated).
- Outputs `data/processed/label_noise.json`.

## Output Format

### results.csv
```csv
query_id,method,ndcg_at_10,precision_at_10,recall_at_10,api_density,doc_density,naming_consistency,bleu_score,rouge_score
q001,bm25,0.45,0.30,0.50,0.12,0.05,0.85,0.0,0.0
q001,dual_encoder,0.52,0.35,0.55,0.12,0.05,0.85,0.0,0.0
q001,rag,0.60,0.40,0.60,0.12,0.05,0.85,0.45,0.50
...
```

### correlations.json
```json
{
  "api_density": {
    "pearson_r": 0.35,
    "spearman_rho": 0.32,
    "p_value": 0.01,
    "significance": "significant"
  },
  "doc_density": {
    "pearson_r": 0.12,
    "spearman_rho": 0.10,
    "p_value": 0.25,
    "significance": "non-significant"
  },
  "naming_consistency": {
    "pearson_r": 0.45,
    "spearman_rho": 0.42,
    "p_value": 0.005,
    "significance": "significant"
  }
}
```

### Plots
- `data/processed/plots/api_density_vs_delta.png`
- `data/processed/plots/doc_density_vs_delta.png`
- `data/processed/plots/naming_consistency_vs_delta.png`

## Troubleshooting

- **OOM Error**: If the process exceeds available memory capacity, the job will fail. (no GPU offload). Reduce the query count or use `--mode constrained`.
- **Model Load Failed**: If 4-bit quantization fails, the system attempts to load a smaller model. If that fails, the job terminates.
- **Data Download Failed**: Ensure internet access and that `ir-datasets` is installed.