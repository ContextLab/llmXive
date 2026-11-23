# Quickstart: llmXive follow-up: extending "SWE-Explore"

## Prerequisites

- Python 3.11+
- Git
- Sufficient Disk Space (for datasets and cache)
- Internet access (for downloading datasets)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-897-llmxive-follow-up-extending-swe-explore
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import transformers; import bitsandbytes; import scipy; import jsonschema; print('All dependencies installed.')"
    ```

## Data Download

The pipeline automatically downloads the SWE-Explore dataset on first run. To manually verify:
```bash
python code/data/download.py
# Output: data/raw/bench.final.public.jsonl (approx. significant size)
```

## Running the Pipeline

### Step 1: Data Curation & Validation
Generate the "hard" and "synthetic" subsets, validate, and checksum.
```bash
python code/data/curate.py
# Outputs: data/curated/hard_subset.jsonl, data/curated/synthetic_ambiguous.jsonl, data/results/validation_report.md
```

### Step 2: Static Baseline Run
Run the one-shot agent on the curated set.
```bash
python code/main.py --mode static
# Outputs: data/results/baseline_logs.jsonl
```

### Step 3: Iterative Agent Run
Run the -turn iterative agent (8-bit quantized) with turn-limit sweep.
```bash
python code/main.py --mode iterative
# Outputs: data/results/iterative_logs.jsonl (includes logs for 1, 2, and 3 turns)
```

### Step 4: Metric Calculation & Statistics
Compute coverage, ranking, precision, and perform Wilcoxon/Bonferroni tests (with tie-handling).
```bash
python code/main.py --mode stats
# Outputs: data/results/metrics.csv, data/results/statistics.json
```

## Validation

Verify the results:
```bash
python -m pytest tests/
```
Check the `data/results/statistics.json` for the `significant` flag and `data/results/metrics.csv` for `feasibility_pass`.

## Troubleshooting

- **OOM Error**: Ensure `bitsandbytes` is installed and the model is loading in 8-bit mode. If still failing, reduce `batch_size` in `code/config.py` or switch to a smaller model (TinyLlama).
- **Dataset Missing**: Re-run `python code/data/download.py` to ensure the Hugging Face cache is populated.
- **Static Analysis Failure**: If `pylint` crashes, the agent treats it as a neutral signal and proceeds (as per Edge Case handling).
- **Schema Validation**: If tests fail, check `contracts/*.yaml` for updates and ensure `code/` outputs match.
