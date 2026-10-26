# Quickstart: GateMem Benchmark Extension

A step‑by‑step guide to set up the environment, fetch the real GateMem dataset, and run the evaluation pipeline.

## Prerequisites
- Python 3.9+  
- `pip`  
- At least **14 GB** disk space and **8 GB** RAM (streaming avoids full load).  

## 1. Environment Setup
```bash
# Clone the repository (assumes you are at the project root)
git clone 
cd PROJ-830-llmxive-follow-up-extending-gatemem-benc

# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Dataset Download
The GateMem dataset is publicly available on Hugging Face.

### Automatic fetch (preferred)
```bash
python src/utils/data_loader.py
```
This script will:
1. Stream the four domain splits from the verified URL.  
2. Validate each episode against `gatemem_episode.schema.yaml`.  
3. Compute SHA‑256 checksums and store them in `state/artifact_hashes.yaml`.  
4. Abort with exit 1 if any validation fails (per FR‑001).

### Manual fetch (optional)
```python
from datasets import load_dataset

# Example for the education split
ds = load_dataset(
    "Ray368/GateMem",
    split="education",
    streaming=True
)

# Optionally write to local file
with open("data/raw/gatemem_education.jsonl", "w", encoding="utf-8") as f:
    for ex in ds:
        f.write(json.dumps(ex) + "\n")
```

## 3. Run Evaluations

### Gatekeeper
```bash
python src/cli/run_evaluation.py --mode gatekeeper --domains medical,office,education,household
```

### Retrieval‑only Baseline
```bash
python src/cli/run_evaluation.py --mode retrieval_only --domains medical,office,education,household
```

### Long‑Context Baseline
```bash
python src/cli/run_evaluation.py --mode long_context --domains medical,office,education,household
```

All commands write per‑pipeline results to `data/processed/` and log profiling info.

## 4. Full Statistical Analysis & Report
```bash
python src/stats/comparison.py --run-full
```
This will:
- Fit the **Logistic GLMM** (binary outcomes) as the primary analysis.  
- Apply **Holm‑Bonferroni** correction across the six primary tests **and** any fallback tests.  
- Produce `data/processed/statistical_results.json` and a human‑readable markdown report at `data/results/final_benchmark_report.md`.

## 5. Generate Final Evaluation Output
```bash
python src/cli/run_evaluation.py --generate-output
```
The command writes `data/processed/final_output.json` which conforms to `contracts/output.schema.yaml`.  

## 6. Verify Outputs
After the run, you should see the following files:

- `data/processed/gatekeeper_results.jsonl`  
- `data/processed/retrieval_only_results.jsonl`  
- `data/processed/long_context_results.jsonl`  
- `data/processed/unified_metrics.json`  
- `data/processed/statistical_results.json`  
- `data/samples/failure_cases.json` (stratified by domain)  
- `data/processed/final_output.json` (validated against `output.schema.yaml`)  

Run the test suite to ensure contract compliance:

```bash
pytest -q
```

Any failure related to data integrity, checksum mismatches, or schema violations must be addressed before proceeding.

## 7. Common Failure Modes
| Symptom | Likely Cause | Fix |
|---|---|---|
| `ConnectionError` in `data_loader.py` | Internet blocked or HF URL changed | Verify connectivity; re‑run the loader. |
| Checksum mismatch | Corrupted download | Delete `data/raw/*` and `state/artifact_hashes.yaml`, then re‑run the loader. |
| Out‑of‑memory crash | Accidental non‑streaming load | Ensure `datasets.load_dataset(..., streaming=True)` is used; keep batch size ≤ 200. |
| Model download fails twice | Cache corruption | Delete `~/.cache/huggingface/transformers/distilbert-base-uncased-finetuned-sst-2-english` and re‑run. The script will retry once automatically. |
| Intent‑mapping accuracy < 80 % | Poor sentiment‑to‑intent mapping | Review the mapping logic; consider refining the label mapping or collecting more annotated data. |

**License Note**: The GateMem dataset is released under a **CC‑BY‑4.0** license, permitting redistribution and commercial‑free use, satisfying Constitution Principle III.  

---

