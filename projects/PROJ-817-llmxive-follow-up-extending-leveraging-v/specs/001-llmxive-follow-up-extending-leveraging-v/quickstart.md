# Quickstart: llmXive Verifier Graph Augmentation Study

This guide walks a researcher through a single CI‑compatible run that reproduces all results.

## 1. Prerequisites
- GitHub Actions runner (or local Linux environment) with Python 3.11.
- Internet access to download the InstructPix2Pix shards.
- Optional: GPU access (Kaggle free GPU) – the pipeline will automatically offload if necessary.

## 2. Setup
```bash
# Clone the repository (assumed already present)
git checkout 001-llmxive-verifier-graph

# Create a fresh virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## 3. Data download & curation
```bash
python -m src.data.download               # pulls the three parquet files into data/raw/
python -m src.data.curate                 # creates data/curated_prompts.csv (adds synthetic_score)
python -m src.data.conflict_generator     # injects contradictions into neutral prompts → conflicting set
```

## 4. Human feasibility validation (required for primary evaluation)
```bash
python -m src.data.human_annotation       # launches a lightweight web form or MTurk batch for **all 1000 prompts**
# Results are saved to data/human_validation.csv and merged into data/curated_prompts.csv as the `human_score` column.
```

## 5. Symbolic graph construction
```bash
python -m src.parser.graph_builder         # reads curated_prompts.csv, writes JSON graphs to data/constraint_graphs/
# Logs runtime; should finish < 30 minutes (SC‑002).
```

## 6. Baseline verifier evaluation
```bash
python -m src.verifier.baseline            # produces data/baseline_scores.csv
# This script will request a CUDA device; if unavailable it will trigger the GPU escape hatch.
# Baseline runtime must be ≤ 2 h (SC‑009) and will be logged automatically.
```

## 7. Graph‑augmented verifier evaluation
```bash
python -m src.verifier.augmented           # produces data/augmented_scores.csv and control condition files
```

## 8. Statistical analysis & report generation
```bash
python -m src.analysis.stats               # runs paired tests (conflicting & neutral), control comparison, robustness check, correlation, correction
python -m src.analysis.report              # writes analysis/report.json and report.csv
# The report includes SC‑001 (mean diff), SC‑004 (p < 0.05), SC‑005 (robustness p ≥ 0.05), SC‑006 (baseline mean ± SD), SC‑007 (Pearson r ≥ 0.5), SC‑008 (effect size ≥ 0.5).
```

## 9. Expected outputs
| File | Description |
|------|-------------|
| `data/curated_prompts.csv` | Prompt text + synthetic & **human** feasibility scores. |
| `data/constraint_graphs/*.json` | One graph per prompt (structural abstraction only). |
| `data/baseline_scores.csv` | Verifier scores without graph context (aligned to human scores). |
| `data/augmented_scores.csv` | Verifier scores with graph context and control runs. |
| `analysis/report.json` | Full statistical results, runtime, memory usage, baseline runtime, correlation. |
| `analysis/report.csv` | Human‑readable table for inclusion in the paper. |

## 10. Verification
Run the contract tests to ensure schema compliance:
```bash
pytest tests/contract/test_evaluation_report.py
```
All tests must pass before the CI job is considered successful.

## 11. GPU Escape Hatch Note
If the runner reports `torch.cuda.is_available() == False`, the verifier scripts automatically switch to the Kaggle GPU escape hatch (the platform will re‑run the same command on a free GPU). No code changes are required; just ensure the `torch` and `transformers` versions support `device="cuda"`.

---

