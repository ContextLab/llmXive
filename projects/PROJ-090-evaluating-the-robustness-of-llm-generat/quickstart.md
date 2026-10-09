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

The pipeline can be executed via a single command that performs a lightweight sample run. This satisfies the quickstart verification requirement.

```bash
python -m code.main --run-sample
```

### Expected Output

The command should finish within 30 seconds and print:

```
Sample run completed
```

This confirms that the entry point is correctly wired and the sample execution path works.

## Full Pipeline Execution

For the complete end‑to‑end run (download, perturb, validate, infer, and analyze), execute:

```bash
python code/main.py
```

This will generate all declared artifacts under `data/processed/` and logs under `data/logs/`. [UNRESOLVED-CLAIM: c_46498105 — status=not_enough_info]

## Reproducing Results

1. Ensure `code/utils/seeds.py` has the global seed set (default: `42`).
2. Delete any existing `data/processed/` files to force re-download and re-computation.
3. Run the full pipeline command again.

## Troubleshooting

- **OOM Error**: If the model fails to load, check RAM usage. Low‑bit quantization should keep usage within the resource‑constrained memory budget. If it exceeds, the pipeline will automatically fallback to `starcoder2-1b`. [UNRESOLVED-CLAIM: c_1a214b44 — status=not_enough_info] If the fallback also fails, check `data/logs/halt_report.json` for details.
- **Timeout**: If the pipeline exceeds an acceptable duration threshold, check network speed for model downloads. The StarCoder model size is suitable for standard consumer hardware deployment. The budget includes fallback time.
- **Dataset Error**: If `openai/openai_humaneval` fails to load, verify internet connectivity.
- **Missing Output Files**: If expected JSON files are missing, consult the relevant script logs in `data/logs/` for errors.
