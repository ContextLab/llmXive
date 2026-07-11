# Quickstart: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for dataset/model downloads)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-861-llmxive-follow-up-extending-appo-agentic
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

## Data Setup

1. **Download Datasets**:
   The system will automatically download GSM and MATH datasets from HuggingFace on first run. Ensure you have sufficient disk space.
   ```bash
   python code/main.py --setup-data
   ```

2. **Verify Checksums**:
   The system will verify the integrity of downloaded data against recorded checksums.

## Running the Pipeline

### 1. Compute Static Scores
Run the static scoring module on a CPU-only environment:
```bash
python code/main.py --stage static --seed 42
```

### 2. Generate Dynamic Scores
Run the APPO rollout module for dynamic scoring:
```bash
python code/main.py --stage dynamic --seed 42
```

### 3. Perform Correlation Analysis
Run the full correlation analysis with permutation test:
```bash
python code/main.py --stage analysis --seed 42 --iterations 10000
```

### 4. View Results
Results are stored in `data/derived/`. Visualizations can be generated using:
```bash
python code/main.py --stage visualize
```

## Testing

Run unit and contract tests:
```bash
pytest tests/
```

Run integration tests with a small batch:
```bash
pytest tests/integration/test_pipeline.py --batch-size=5
```

## Troubleshooting

- **Memory Errors**: Ensure no other heavy processes are running. The system is designed to stay under a specified memory footprint.
- **Timeout Errors**: If the permutation test times out, check the logs for partial results. The system will flag results as "inconclusive" if the timeout triggers.
- **CUDA Errors**: Ensure no GPU is detected. The system should run on CPU only. If CUDA is detected, set `CUDA_VISIBLE_DEVICES=""`.
