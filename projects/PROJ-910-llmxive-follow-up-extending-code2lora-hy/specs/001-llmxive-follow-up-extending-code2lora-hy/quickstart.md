# Quickstart: llmXive follow-up: extending "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution"

## 1. Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or a local environment with ≥7 GB RAM.

## 2. Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-910-llmxive-follow-up-extending-code2lora-hy
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins CPU-only versions of `torch` and `transformers`.*

## 3. Data Setup

1. **Download the dataset**:
 The script will automatically download `RepoPeftBench` from the verified HuggingFace URL.
 ```bash
 python -m code.main --setup-data
 ```
 *Alternatively, manually download from:

2. **Verify checksums**:
 Ensure the downloaded file matches the expected hash in `state/artifact_hashes.yaml`.

## 4. Running the Pipeline

### 4.1 Feature Extraction & Adapter Generation
```bash
python -m code.main --mode generate --repo-id <repo_id>
```
- Extracts AST features.
- Generates LoRA adapter.
- Saves to `data/adapters/`.

### 4.2 Evaluation
```bash
python -m code.main --mode evaluate --adapter-path data/adapters/<repo_id>.safetensors
```
- Runs on RepoPeftBench test set.
- Outputs exact-match scores and latency.

### 4.3 Sensitivity Analysis
```bash
python -m code.main --mode sensitivity
```
- Runs multiple feature subsets.
- Generates `sensitivity_curve.csv`.

## 5. Reproducibility

- **Random Seeds**: Set in `code/utils/config.py`.
- **Environment**: Use the provided `Dockerfile` (if available) or `requirements.txt` to ensure identical dependencies.
- **CI Execution**: Push to `001-ast-based-adapter-generation` branch to trigger GitHub Actions workflow.

## 6. Troubleshooting

- **Memory Error**: Reduce the number of repositories processed in one batch.
- **AST Parsing Error**: Check `logs/parsing_warnings.log` for skipped files.
- **Checkpoint Incompatibility**: Ensure the base model path matches the expected architecture.
