# Quickstart: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

## Prerequisites

- Python 3.11+
- Sufficient RAM (required for 4-bit quantized model)
- vCPUs (minimum)
- Internet access (for dataset/model download)

## Installation

1. **Clone the repository** and navigate to the project directory.
 ```bash
 git clone <repo-url>
 cd projects/PROJ-090-evaluating-the-robustness-of-llm-generat
 ```

2. **Create a virtual environment** and install dependencies.
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

3. **Verify dataset access** (optional but recommended).
 ```bash
 python -c "import datasets; d = datasets.load_dataset('openai/openai_humaneval', split='test'); print(f'Loaded {len(d)} tasks')"
 ```

## Running the Pipeline

The pipeline is executed via the main script. It performs all steps: download, perturb, validate, infer, and analyze.

```bash
python code/main.py
```

### Expected Output

Upon successful completion, the following files will be generated in the `data/processed/` directory:

- `perturbation_candidates_raw.json`: All generated variants.
- `perturbation_candidates_validated.json`: High-fidelity variants (>0.95 similarity).
- `inference_logs.json`: Execution results (pass/fail/timeout).
- `calibration_report.json`: Final statistical analysis and sensitivity report.

### Logs

Runtime logs and error reports are stored in `data/logs/`:
- `halt_report.json`: Summary of runtime errors (OOM, timeouts), including fallback triggers.

## Reproducing Results

To reproduce results exactly:

1. Ensure `code/utils/seeds.py` has the global seed set (default: `42`).
2. Delete any existing `data/processed/` files to force re-download and re-computation.
3. Run `python code/main.py` again.

## Troubleshooting

- **OOM Error**: If the model fails to load, check RAM usage. Low-bit quantization should keep usage within a resource-constrained memory budget. If it exceeds, the pipeline will automatically fallback to `starcoder2-1b`. If the fallback also fails, check `data/logs/halt_report.json` for details.
- **Timeout**: If the pipeline exceeds an acceptable duration threshold, check network speed for model downloads. The StarCoder model is of a size suitable for standard consumer hardware deployment. The budget includes fallback time.
- **Dataset Error**: If `openai/openai_humaneval` fails to load, verify internet connectivity. The verified URL is `.
- **Missing Output Files**: If `data/processed/calibration_report.json` is missing, the statistical analysis step failed. Check `code/analysis/statistics.py` and the `data/logs/halt_report.json` for errors.