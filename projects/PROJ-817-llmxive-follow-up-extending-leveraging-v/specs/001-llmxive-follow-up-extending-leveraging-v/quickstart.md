# Quickstart: Graph‑augmented Verifier Evaluation (llmXive)

A researcher can reproduce the entire study on a GitHub Actions free‑tier runner (or a local Linux environment) with the commands below.

## 1. Prerequisites
- Python 3.11
- Internet access (to download the InstructPix2Pix parquet files)
- Optional: GPU access (Kaggle free GPU). **The pipeline runs fully on CPU**, so a GPU is not required.

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
# Stream the verified parquet shards and write them to data/raw/
python -m src.data.download

# Build the balanced CSV, add synthetic scores, assign UUIDs, and write to data/results/
python -m src.data.curate
```

- **Provenance**: `data/raw/provenance.json` records the three URLs, their SHA‑256 checksums, and the generated file checksum.

## 4. Conflict set selection (no synthetic generation)
```bash
# Filter natural language prompts for realistic contradictions using heuristic cues
python -m src.data.filter_conflicts
# This creates `data/results/curated_prompts.csv` with an equal number of conflicting and neutral prompts.
```

## 5. Human feasibility annotation (required for evaluation)
```bash
python -m src.data.human_annotation
# Writes `data/results/human_validation.csv` and merges scores into `curated_prompts.csv`.
```

## 6. Symbolic graph construction (CPU‑only)
```bash
python -m src.parser.graph_builder
# Output: data/results/graphs/graph_<prompt_id>.json
# Expected runtime < 30 min on the 2‑core runner (SC‑002).
```

## 7. Baseline verifier evaluation
```bash
python -m src.verifier.baseline
# Produces data/results/baseline_scores.csv
# Uses CPU‑only 8‑bit quantized inference, staying within ≤ 7 GB RAM and **≤ 2 h** runtime (target ≤ 2 h; aborts and reports limitation if exceeded) (SC‑009).
```

## 8. Graph‑augmented verifier evaluation (with controls)
```bash
python -m src.verifier.augmented
# Produces data/results/augmented_scores.csv (conditions: graph_augmented, control_filler, control_empty)
```

## 9. Statistical analysis & report generation
```bash
python -m src.analysis.stats
python -m src.analysis.report
```

- Generates:
  - `analysis/report.json`  (machine‑readable, conforms to contract)
  - `analysis/report.csv`   (human‑readable table for the paper)

## 10. Verification
```bash
pytest tests/contract/test_evaluation_report.py
```

All contract tests must pass; otherwise the CI job fails.

## 11. Expected outputs
| File | Description |
|------|-------------|
| `data/raw/*.parquet` | Original InstructPix2Pix shards (verified URLs). |
| `data/raw/provenance.json` | Checksums and source metadata. |
| `data/results/curated_prompts.csv` | Prompt text + synthetic & **human** feasibility scores (human scores for all prompts). |
| `data/results/human_validation.csv` | Raw crowd ratings. |
| `data/results/graphs/*.json` | One constraint graph per prompt (CPU‑only). |
| `data/results/baseline_scores.csv` | Verifier scores without graph context. |
| `data/results/augmented_scores.csv` | Verifier scores with graph context and two control conditions. |
| `analysis/report.json` | Full statistical results, runtime, memory usage, correlation, correction method. |
| `analysis/report.csv` | Human‑readable summary for inclusion in the manuscript. |

The quickstart now points to the correct module paths (`src.data...`) and includes the new conflict‑filter step and the corrected output path for `curated_prompts.csv`.

---
