# Quickstart: llmXive follow-up: extending "OCC-RAG: Optimal Cognitive Core for Faithful Question Answering"

## Prerequisites

- Python 3.11+
- Sufficient RAM (for sampled data)
- Git
- Access to OCC-RAG model checkpoint and 50k synthetic corpus (**manual fetch required**)

## Installation

1. **Clone Repository**:
 ```bash
 git clone <repo_url>
 cd projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 # venv\Scripts\activate # Windows
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Setup

1. **Download Data**:
 - Fetch OCC-RAG model checkpoint from original project repository (GitHub/Zenodo).
 - Download a large-scale synthetic multi-hop QA corpus.
 - Place in `data/raw/`.
 - **If data is not available, the pipeline will halt with 'DATA_UNAVAILABLE'.**

2. **Verify Checksums**:
 ```bash
 python code/utils/verify_checksums.py
 ```

## Execution Pipeline

### Step 1: Sensitivity Analysis
```bash
python code/sensitivity_analysis.py --sample-size [variable] --masking-unit head
```
- Outputs: `data/processed/sensitivity_results.csv`

### Step 2: Prune Model
```bash
python code/_prune_model.py --retention-pct 50
```
- Outputs: `data/processed/pruned_model_weights.pt`

### Step 3: Fine-Tune Pruned Model
```bash
The research question and method are defined in the planning document, with implementation details to be determined in the subsequent phase, as supported by prior work ().
```
- Outputs: `data/processed/finetuned_model.pt`

### Step 4: Statistical Validation
```bash
python code/04_statistical_validation.py
```
- Outputs: `data/processed/statistical_results.json`

## Validation

- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **Contract Tests**: `pytest tests/contract/` (validates against `contracts/` schemas)

## Troubleshooting

- **OOM Errors**: Reduce `--sample-size` in Step 1.
- **CUDA Errors**: Ensure `torch` is installed without CUDA support (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Data Not Found**: Verify manual fetch of OCC-RAG model and corpus.