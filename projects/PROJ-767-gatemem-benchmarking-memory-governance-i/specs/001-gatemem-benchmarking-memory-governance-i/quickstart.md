# Quickstart: GateMem Benchmarking Memory Governance

## Prerequisites

- Python 3.11+
- Git
- 7GB+ RAM (for CPU inference)
- 14GB+ Disk Space

## Installation

1. **Clone and Setup**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-767-gatemem-benchmarking-memory-governance-i
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

2. **Verify Dependencies**
   Ensure `llama-cpp-python` is installed with CPU support (no CUDA):
   ```bash
   python -c "import llama_cpp; print(llama_cpp.__version__)"
   ```

## Running the Benchmark

### 1. Generate Synthetic Data
Generate memory items for $N=4$ principals with 500 items each, seed 42:
```bash
python code/data_gen.py --n 4 --items-per-principal 500 --seed 42 --output data/generated/memories_N4_seed42.json
```

### 2. Execute Task Loop
Run the agent loop with a CPU-quantized model (ensure `model.gguf` is in `data/models/`):
```bash
python code/runner.py \
  --context data/generated/memories_N4_seed42.json \
  --model data/models/llama-3-8b-q4_k_m.gguf \
  --seeds 42 \
  --output data/results/logs_N4_seed42.jsonl
```
*Note: For a full run, iterate seeds 0-4 and $N \in \{2, 4, 8, 16\}$.*

### 3. Compute Metrics
Analyze the logs to generate governance scores and statistical tests (LMM):
```bash
python code/metrics.py \
  --logs data/results/logs_*.jsonl \
  --output data/results/metrics_summary.csv \
  --test lmm
```

### 4. Validate Results
Check the output CSV for the `governance_score`, `lmm_p_value`, and `lmm_effect_size`.
```bash
cat data/results/metrics_summary.csv
```

## Troubleshooting

- **OOM Error**: Reduce `items-per-principal` or use a smaller model (e.g., Mistral-7B).
- **Model Not Found**: Ensure the GGUF file is in `data/models/` and the path is correct.
- **Evaluation Failures**: Check `evaluator.py` for regex patterns; ensure facts are generated in the correct format.

## Reproducibility Check

To verify reproducibility, re-run the full pipeline with the same seeds and compare checksums of the output files:
```bash
md5sum data/results/metrics_summary.csv
```