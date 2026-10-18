# Quickstart: Graph‑augmented Verifier Evaluation (llmXive)

A researcher can reproduce the entire study on a GitHub Actions free‑tier runner (or a local Linux environment) with the commands below.

## 1. Prerequisites
- Python 3.11
- Internet access (to download the InstructPix2Pix parquet files)
- Optional: GPU access (Kaggle free GPU). The pipeline will automatically offload verifier inference if a CUDA device is unavailable.

## 2. Setup
```bash
# Clone the repository (assumed already present)
git checkout 001-llmxive-verifier-graph

# Create a fresh virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt

# Download the spaCy English model
python -m spacy download en_core_web_sm
```

## 3. Data download & curation
```bash
# Stream the three verified parquet shards and write them to data/raw/
python -m src.data.download

# Build the balanced CSV, add synthetic scores, and assign UUIDs
python -m src.data.curate
```
- **Provenance**: `data/raw/provenance.json` records the three URLs, their SHA‑256 checksums, and the generated file checksum.

## 4. Human feasibility annotation (required for evaluation)
```bash
python -m src.data.human_annotation
```
- This script launches a lightweight web form (or MTurk batch) for **all 1 000 prompts**.  
- Results are saved to `data/human_validation.csv` and merged into `data/curated_prompts.csv` as the `human_score` column.

## 5. Symbolic graph construction (CPU‑only)
```bash
python -m src.parser.graph_builder
# Output: data/graphs/graph_<prompt_id>.json
# Expected runtime < 30 min on the 2‑core runner (SC‑002).
```

## 6. Baseline verifier evaluation
```bash
python -m src.verifier.baseline
# Produces data/baseline_scores.csv
# If no CUDA device is present, the script triggers the Kaggle GPU escape hatch automatically.
# Baseline runtime must be ≤ 2 h (SC‑009) and will be logged.
```

## 7. Graph‑augmented verifier evaluation (with controls)
```bash
python -m src.verifier.augmented
# Produces data/augmented_scores.csv (conditions: graph_augmented, control_filler, control_empty)
```

## 8. Statistical analysis & report generation
```bash
python -m src.analysis.stats
python -m src.analysis.report
# Generates:
#   - data/report.json  (machine‑readable, conforms to contract)
#   - data/report.csv   (human‑readable table for the paper)
```

## 9. Verification
```bash
pytest tests/contract/test_evaluation_report.py
```
All contract tests must pass; otherwise the CI job fails.

## 10. Expected outputs
| File | Description |
|------|-------------|
| `data/raw/*.parquet` | Original InstructPix2Pix shards (verified URLs). |
| `data/raw/provenance.json` | Checksums and source metadata. |
| `data/curated_prompts.csv` | Prompt text + synthetic & **human** feasibility scores. |
| `data/human_validation.csv` | Raw crowd ratings. |
| `data/graphs/*.json` | One constraint graph per prompt (CPU‑only). |
| `data/baseline_scores.csv` | Verifier scores without graph context. |
| `data/augmented_scores.csv` | Verifier scores with graph context and two control conditions. |
| `data/report.json` | Full statistical results, runtime, memory usage, correlation, correction method. |
| `data/report.csv` | Human‑readable summary for inclusion in the manuscript. |

## 11. GPU Escape Hatch Note
If `torch.cuda.is_available()` returns `False`, the verifier scripts automatically re‑run on a free Kaggle GPU (the platform detects the CUDA error and performs the off‑load). No code changes are required; just ensure the `torch` and `transformers` versions support `device="cuda"`.

---
