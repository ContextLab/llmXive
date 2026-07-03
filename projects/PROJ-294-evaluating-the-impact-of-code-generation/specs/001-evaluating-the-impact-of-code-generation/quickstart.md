# Quickstart: Evaluating the Impact of Code Generation Models on Code Testability

## Prerequisites

- Python 3.10+
- `git`
- Access to HuggingFace (required for dataset download).

## Installation

1. **Clone the repository** (or navigate to the project directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-294-evaluating-the-impact-of-code-generation/code/requirements.txt
   ```
   *All versions are pinned to ensure reproducibility on CI.*

## Running the Pipeline

The pipeline can be executed via a single entry‑point script or step‑by‑step.

### Option A: Full Pipeline (Recommended)

```bash
cd projects/PROJ-294-evaluating-the-impact-of-code-generation/code/
python run_pipeline.py
```

`run_pipeline.py` orchestrates:

1. Data download (HumanEval)  
2. Citation validation (`validate_citations.py`)  
3. Code generation (`generate_code.py`)  
4. Static analysis (`analyze_metrics.py`)  
5. Dynamic execution & coverage (`run_tests.py`)  
6. Statistical analysis (`stats.py`)  
7. Decoupling analysis (`stats.py` – optional flag)  
8. Versioning update (`update_state.py`)  
9. Visualization (`visualize.py`)  
10. Report generation (`report.py`)

### Option B: Step‑by‑Step

```bash
# 1. Download data
python download_data.py

# 2. Validate citations
python validate_citations.py

# 3. Generate code (350M model)
python generate_code.py --model codegen-350M-mono --tasks 50

# 4. Analyze static metrics
python analyze_metrics.py

# 5. Run dynamic tests & coverage
python run_tests.py

# 6. Perform statistical analysis
python stats.py

# 7. Update state hashes
python update_state.py

# 8. Visualize & create report
python visualize.py
python report.py
```

## Verification

- Verify `data/analysis/metrics.json` contains non‑null entries for all successful samples.  
- Verify `results/stats.json` contains test statistics, p‑values, and power estimates.  
- Verify `results/results_report.md` includes figures, statistical conclusions, and the limitations discussion.  
- Verify `results/logs/errors.log` lists any generation, parsing, or execution failures.  
- Run the full test suite:
  ```bash
  pytest tests/unit/
  ```

## Troubleshooting

- **Memory Error**: If a model fails to load, ensure you are using the 350M variant; larger models are not supported on the free tier.  
- **Syntax Errors**: Generated code that fails Python's `ast.parse` is skipped and logged; the pipeline continues with remaining samples.  
- **Timeouts**: Generation retries up to 3 times; persistent failures are recorded as `generation_status = "timeout"`.  
- **Execution Failures**: If a snippet crashes during testing, `pass_rate` is recorded as 0.0 and `dynamic_branch_coverage` may be null; the failure is logged.
