# Quickstart Guide: llmXive LatentSkill Follow-up

This guide outlines the steps to execute the full pipeline and generate final reports.

## Prerequisites

- Python 3.9+
- System dependencies: `cmake`, `build-essential`
- Hugging Face CLI installed (`pip install huggingface-hub`)

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure system dependencies are installed (if on Linux):
 ```bash
 sudo apt-get update && sudo apt-get install -y cmake build-essential
 ```

## Pipeline Execution

The pipeline is executed in phases. Run the following commands in order:

### Phase 1: Setup & Validation
```bash
python src/validate/citation_check.py
```

### Phase 2: Ingestion (User Story 1)
```bash
python src/ingestion/download_weights.py
python src/ingestion/flatten_lora.py
python src/retrieval/vector_db.py --input data/processed/weights_flattened.npz --output data/processed/skill_index.npz --k 5
```

### Phase 3: Retrieval & Interpolation (User Story 2)
```bash
python src/validation/generate_cv_set.py
python src/validation/generate_eval_tasks.py
python src/validation/generate_proxy_gt.py
python src/retrieval/query.py
python src/retrieval/strategies.py
python src/validation/reconstruction_error.py
python src/validation/linearity_check.py
```

### Phase 4: Evaluation (User Story 3)
```bash
python src/evaluation/verify_memory_footprint.py
python src/evaluation/runner.py --runs 5
python src/evaluation/stats.py
python src/evaluation/report_generator.py
```

### Phase 5: Final Reporting (T085)
```bash
python src/evaluation/summary_generator.py
```

## Output Artifacts

- `data/processed/skill_index.npz`: The skill vector database.
- `data/results/stats_report.json`: Aggregated statistical results.
- `reports/final_report.md`: Detailed final report.
- `reports/summary.md`: High-level summary of findings (T085).

## Troubleshooting

- **CUDA Errors**: If running on a CPU-only environment, ensure the model quantization step (T026a1) was successful and the GGUF model is used.
- **Missing Data**: If `download_weights.py` fails, check `data_sources.yaml` for valid URLs and network connectivity.
- **Memory Issues**: The pipeline is designed to run on constrained runners; if OOM occurs, reduce `N` in `runner.py` or use a smaller model.
