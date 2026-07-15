# Quickstart: llmXive follow-up: extending "Qwen-AgentWorld: Language World Models for General Agents"

## 1. Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace datasets (public)
- Sufficient RAM (for CPU-quantized model inference)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Acquisition

The pipeline automatically downloads datasets from verified sources upon first run. To manually verify or force download:

```bash
python -m code.utils.loaders --download
```

This will populate `data/raw/` with the AgentWorld datasets and compute checksums.

## 4. Running the Pipeline

Execute the full analysis pipeline:

```bash
python -m code.main --seed 42
```

This will:
1. Build the Ground Truth Oracle.
2. Generate CoT traces (if not pre-existing) using a CPU-quantized model.
3. Extract and validate rules against the Oracle.
4. Run the divergence analysis on a representative set of tasks.
5. Perform the paired permutation test.
6. Generate the final report in `data/processed/divergence_report.json`.

## 5. Verifying Results

To verify the reproducibility of a specific run:

```bash
pytest tests/integration/test_pipeline.py --seed 42
```

To check data integrity:

```bash
python -m code.utils.checksums --verify
```

## 6. Expected Output

- `data/processed/divergence_report.json`: Contains counts of Hallucinations, Rule Gaps, and statistical significance.
- `data/processed/oracle_graph.json`: The deterministic state transition graph.
- `data/processed/extracted_rules.json`: The set of logical rules inferred from traces (with validation flags).

## 7. Troubleshooting

- **Checksum Mismatch**: Ensure the network connection is stable and re-run `python -m code.utils.loaders --download`.
- **Memory Error**: The pipeline uses streaming for large datasets. If memory errors persist, reduce the number of tasks in `config.yaml` (not recommended for final runs).
- **Rule Extraction Failure**: Check the `Extraction Uncertainty` count in the report; high uncertainty may indicate ambiguous traces.
- **CPU Inference Slow**: Ensure the model is loaded in Int4 precision (`device_map="cpu"`, `load_in_4bit=True`).