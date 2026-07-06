# Quickstart: Evaluating Prompting Strategies for Code Generation

## 1. Prerequisites

*   **OS**: Linux (required for `resource.setrlimit` and Docker/subprocess isolation).
*   **Python**: 3.11+
*   **Memory**: Minimum 7 GB RAM (GitHub Actions Free Tier).
*   **Disk**: Minimum 14 GB (for model cache and datasets).

## 2. Installation

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd projects/PROJ-028-evaluating-the-effectiveness-of-differen
pip install -r requirements.txt
```

**Dependencies**:
*   `transformers>=4.30.0`
*   `torch>=2.0.0` (CPU version)
*   `datasets>=2.14.0`
*   `scipy>=1.10.0`
*   `pytest>=7.0.0`
*   `psutil>=5.9.0`

## 3. Running the Pipeline

### Baseline (Zero-Shot)
Run the baseline with multiple seeds on a subset of tasks (for testing):

```bash
python -m src.cli.main \
  --strategy zero-shot \
  --seeds 3 \
  --max-tasks 50 \
  --output-dir data/results/baseline
```

### Full Evaluation (Zero-shot, Few-shot, CoT)
Run the full experiment (up to 500 tasks, 3 seeds, k=10 for advanced):

```bash
python -m src.cli.main \
  --strategies zero-shot few-shot cot \
  --seeds 3 \
  --max-tasks 500 \
  --k-samples 10 \
  --output-dir data/results/full_run
```

*   `--k-samples`: Number of samples per task (zero-shot and few-shot settings).
*   `--max-tasks`: Limits the dataset size to ensure runtime < 6h.

### Statistical Analysis
After the pipeline completes, run the analysis script:

```bash
python -m src.analysis.stats \
  --input-dir data/results/full_run \
  --output data/reports/final_report.json
```

## 4. Verification

### Unit Tests
Run the test suite to verify sandbox and prompt logic:

```bash
pytest tests/unit/ -v
```

### Integration Tests
Run a small end-to-end test (a limited set of tasks):

```bash
pytest tests/integration/test_pipeline.py -v
```

### Contract Validation
Validate the output JSON against the schema:

```bash
pytest tests/contract/test_schemas.py -v
```

## 5. Expected Outputs

*   **JSON Reports**: `data/results/*/strategy_seed.json`
*   **Summary Report**: `data/reports/final_report.json` (contains pass@1, pass@10, p-values).
*   **Resource Log**: `data/logs/execution.log` (peak RAM, total time).

## 6. Troubleshooting

*   **OOM Error**: If the process crashes due to memory, check `data/logs/execution.log`. The system should have automatically switched to FP16. If not, reduce `--max-tasks`.
*   **Timeout Errors**: If `timeout_rate` is high, the generated code may be too complex. The system handles this gracefully; the rate is reported in the final report.
*   **Parsing Failures**: If `parsing_success_rate` < 90%, check the `extracted_code` logic in `src/evaluation/prompts.py`.
