# llmXive: Extending "The Mirage of Optimizing Training Policies"

This project implements an automated research pipeline to verify the existence of a "Mirage of Optimizing Training Policies" (MIPU) gap. It generates a dataset pairing full-precision training signals with ground-truth policy divergence measured by CPU-based quantized inference, trains a lightweight predictor, and statistically validates the bounds.

## Prerequisites

- Python 3.10+
- CUDA-capable GPU (optional, for full-precision training signals) or CPU (slower)
- 16GB+ RAM (for full-precision model loading)
- 32GB+ disk space (for model weights and dataset)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmxive-follow-up
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Configure environment variables:
 - Copy `.env.example` to `.env`.
 - Set `MODEL_PATH` to the path of your Llama-8B model (Hugging Face or local).
 - Set `DATASET_ID` to the Hugging Face dataset ID (e.g., `gsm8k`).

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── cli/ # CLI entry points for pipeline stages
│ │ ├── config/ # Configuration and logging setup
│ │ ├── models/ # Data entities (TrainingSample, etc.)
│ │ ├── services/ # Core logic (feature extraction, inference, etc.)
│ │ └── utils/ # Statistical utilities
│ ├── scripts/ # Setup and utility scripts
│ └── tests/ # Unit and integration tests
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Generated Parquet/JSON artifacts
│ └── models/ # Trained predictor models
├── docs/
│ ├── api.md # API documentation
│ └── reports/ # Final research reports
├── logs/ # Pipeline execution logs
├── requirements.txt
└── README.md
```

## Quickstart

1. **Setup Data Directories**:
 ```bash
 python code/scripts/setup_data_dirs.py
 ```

2. **Generate Dataset (User Story 1)**:
 ```bash
 python code/src/cli/generate_dataset.py
 ```
 This produces `data/processed/training_sample.parquet`.

3. **Validate Features (User Story 1)**:
 ```bash
 python code/src/cli/validate_features_diagnostic.py
 ```

4. **Train Predictor (User Story 2)**:
 ```bash
 python code/src/cli/prepare_data_split.py
 python code/src/cli/train_predictor.py
 ```

5. **Evaluate Predictor (User Story 2)**:
 ```bash
 python code/src/cli/evaluate_on_test.py
 ```

6. **Verify Bounds & Statistics (User Story 3)**:
 ```bash
 python code/src/cli/synchronize_inputs.py
 python code/src/cli/orchestrate_baseline_proxy.py
 # This triggers T027 and T028
 python code/src/cli/verify_bound_consistency.py
 python code/src/cli/aggregate_bound_results.py
 python code/src/cli/run_latency_analysis.py
 ```

7. **Generate Final Report**:
 ```bash
 python code/src/cli/generate_report.py
 ```

## API Documentation

See `docs/api.md` for detailed function signatures and usage examples.

## Testing

Run the test suite:
```bash
pytest code/tests/ -v
```

## License

MIT License.
