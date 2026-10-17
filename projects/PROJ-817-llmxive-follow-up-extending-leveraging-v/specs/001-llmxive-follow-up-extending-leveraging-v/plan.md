# Implementation Plan: llmXive follow-up: extending "Leveraging Verifier-Based Reinforcement Learning in Image Editing"

**Branch**: `001-llmxive-verifier-graph` | **Date**: 2026-10-16 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-verifier-graph/spec.md`

## Summary
The project evaluates whether a CPU‑only symbolic constraint‑graph preprocessing layer can mitigate the degradation of the distilled Edit‑R1 1B verifier on conflicting image‑editing instructions.

* **Baseline** – Run the verifier on a curated [deferred]‑prompt dataset (500 conflicting, 500 neutral) and record alignment scores versus **human‑annotated feasibility scores** (primary ground‑truth) (FR‑001, FR‑003). Synthetic feasibility scores are generated only to create realistic conflicting prompts; they are **not** used for the main statistical evaluation.
* **Symbolic Parser** – Build a spaCy + networkx pipeline that extracts principles, temporal relations, and contradictions into directed graphs (FR‑002, Principle VI).  
* **Graph‑Augmented Evaluation** – Feed the JSON graphs into the verifier’s prompt template under a `Context:` section, plus two control conditions (random filler context, empty graph) to isolate the effect of graph content (FR‑004).  
* **Statistical Comparison** – Perform a paired test (t‑test or Wilcoxon) on the conflicting subset, comparing verifier scores **against human feasibility scores** (not synthetic). Compute the **mean alignment‑score difference** (SC‑001), apply multiple‑comparison correction (FR‑007), and verify **effect‑size consistency** between primary and hold‑out sets (SC‑005).  
* **Power Analysis** – An a priori calculation (G*Power) shows that 500 conflicting prompts give ≥0.85 power to detect a medium effect (Cohen’s d≈0.5) at α = 0.05; we will increase to 600 if the observed variance exceeds expectations.  
* **Human Feasibility Validation** – Collect independent human judgments on a random sample of **all 1000 prompts** (or at least 200) via a lightweight crowdsourcing form; these human scores constitute the primary ground‑truth for alignment evaluation. If the correlation between synthetic and human scores falls below 0.6, we will flag the synthetic heuristic and rely exclusively on human scores.  
* **Runtime & Resource Checks** – Verify parser runtime ≤ 30 min, total RAM ≤ 7 GB, and total wall‑clock ≤ 6 h. Because the 1B verifier exceeds the CPU memory budget, inference will be executed on a **GPU escape hatch** (Kaggle free GPU) using 8‑bit quantisation; the pipeline will automatically offload when `torch.cuda.is_available()` is false on the runner.  

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:  
- `torch==2.3.0` (CPU‑first, with optional CUDA offload)  
- `transformers==4.44.0`  
- `datasets==2.21.0`  
- `spacy==3.7.4` (with the `en_core_web_sm` model)  
- `networkx==3.3`  
- `pandas==2.2.2`  
- `scipy==1.13.1`  
- `statsmodels==0.14.2`  
- `tqdm==4.66.5`  

**Storage**: Files under `data/` (raw parquet, curated CSV, graph JSON, result CSVs).  
**Testing**: `pytest` for unit tests of parser and contracts.  
**Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ≤ 7 GB RAM).  
**Performance Goals**: Complete end‑to‑end pipeline ≤ 6 h, parser ≤ 30 min, memory ≤ 7 GB.  
**Constraints**: CPU‑only symbolic module (Principle VI); reproducibility (Principle I).  
**Scale/Scope**: [deferred] prompts (500 conflicting, 500 neutral) generated from public InstructPix2Pix shards with synthetic conflict injection.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed random seeds; deterministic synthetic conflict generation; data fetched from canonical HF URLs each run. |
| II. Verified Accuracy | All dataset and model URLs are verified; citation titles meet overlap thresholds. |
| III. Data Hygiene | Raw parquet files are checksummed; all transformations write new files with provenance in filenames. |
| IV. Single Source of Truth | Every figure/table traces to a single row in the CSV artifacts; no hand‑typed numbers. |
| V. Versioning Discipline | Content hashes recorded in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Symbolic Preprocessing Fidelity | Parser uses only spaCy, networkx, and rule‑based logic; no GPU components. |
| VII. Conflict‑Agnostic Robustness Validation | Separate analysis for conflicting vs. neutral, paired tests, hold‑out re‑phrased set, and effect‑size consistency check. |

## Project Structure
### Documentation (this feature)
```text
specs/001-llmxive-verifier-graph/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── evaluation_report.schema.yaml
└── tasks.md   # (generated later)
```

### Source Code
```text
src/
├── data/
│   ├── download.py            # fetch raw InstructPix2Pix parquet files
│   ├── curate.py              # build curated CSV with synthetic feasibility scores
│   └── conflict_generator.py  # inject contradictions into neutral prompts
├── parser/
│   ├── graph_builder.py       # spaCy + networkx pipeline
│   └── utils.py
├── verifier/
│   ├── baseline.py            # run Edit‑R1 verifier on raw prompts (CPU/GPU fallback)
│   └── augmented.py           # run verifier with graph JSON context and control conditions
├── analysis/
│   ├── stats.py               # paired test, effect size, FDR correction, power calc
│   └── report.py              # generate final CSV/JSON report
└── cli/
    └── run_all.py             # orchestrates full pipeline
tests/
├── unit/
│   ├── test_graph_builder.py
│   └── test_stats.py
└── contract/
    └── test_evaluation_report.py
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None – all requirements fit within a single‑module design respecting CPU‑only constraint (except verifier inference, which uses GPU escape hatch) and the 6‑hour runtime budget. |
