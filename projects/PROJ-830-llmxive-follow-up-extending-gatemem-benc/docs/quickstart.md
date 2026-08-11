# Quickstart Guide: GateMem Benchmark Extension

This guide provides step-by-step instructions to set up the environment, download the required dataset, and run the initial evaluation for the GateMem benchmark extension project.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- Access to Hugging Face Hub (for dataset download)

## 1. Project Setup

### Clone the Repository
```bash
git clone <repository-url>
cd PROJ-830-llmxive-follow-up-extending-gatemem-benc
```

### Create a Virtual Environment
It is recommended to use a virtual environment to manage dependencies.
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
Install the required packages listed in `requirements.txt`.
```bash
pip install -r requirements.txt
```

## 2. Dataset Download

This project uses the **GateMem** dataset hosted on Hugging Face. The data loader is configured to stream the dataset to handle memory constraints, but you can also download it manually if preferred.

### Automatic Download (Recommended)
The dataset will be automatically fetched and cached when you run the evaluation pipeline. Ensure you have a stable internet connection.

### Manual Download (Optional)
If you prefer to download the dataset manually:
1. Visit the dataset page on Hugging Face: [GateMem Dataset] (Note: Replace with actual dataset ID if different).
2. Use the Hugging Face CLI or Python library to download:
 ```bash
 pip install huggingface_hub
 huggingface-cli download <dataset-id> --local-dir data/raw
 ```
 Or via Python:
 ```python
 from datasets import load_dataset
 dataset = load_dataset("<dataset-id>", split="train", streaming=True)
 # Process or save as needed
 ```

## 3. Running the First Evaluation

The evaluation pipeline compares the Gatekeeper approach against baseline methods (Retrieval-only and Long-Context).

### Run Access Control Evaluation (User Story 1)
This evaluates unauthorized information leakage rates on specific domains.
```bash
python code/cli/run_evaluation.py --domains medical,office --mode access_control
```

### Run Utility and Forgetting Evaluation (User Story 2)
This evaluates task success rates and deletion compliance.
```bash
python code/cli/run_evaluation.py --domains education,household --mode utility
```

### Run Performance Profiling (User Story 3)
This measures latency and memory usage.
```bash
python code/cli/run_evaluation.py --domains medical --mode profiling
```

### Full Benchmark Suite
To run the complete benchmark across all supported domains and metrics:
```bash
python code/cli/run_evaluation.py --all
```

## 4. Output Files

Results are saved in the `data/processed/` directory:
- `access_control_results.json`: Access control scores.
- `utility_results.json`: Utility and forgetting scores.
- `performance_results.json`: Latency and memory profiling data.
- `final_benchmark_report.md`: Comprehensive summary report.

## 5. Troubleshooting

- **Dataset Fetch Failed**: Ensure your internet connection is stable and you have access to Hugging Face Hub. If using a proxy, configure your environment variables (`HTTP_PROXY`, `HTTPS_PROXY`).
- **Model Load Error**: The DistilBERT model is loaded from the Hugging Face Hub. Ensure you have enough disk space in your cache directory (`~/.cache/huggingface`).
- **Memory Issues**: The pipeline is designed to stream data. If you encounter memory errors, check your system resources or reduce the number of domains processed in a single run.

## 6. Next Steps

- Review the `specs/` directory for detailed design documents.
- Run the contract and integration tests:
 ```bash
 pytest tests/
 ```
- Contribute to the project by implementing pending tasks in `tasks.md`.