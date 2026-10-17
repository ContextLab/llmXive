# Implementation Plan: llmXive follow-up: extending "Leveraging Verifier-Based Reinforcement Learning in Image Editing"

**Branch**: `001-llmxive-verifier-graph` | **Date**: 2026-10-16 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-verifier-graph/spec.md`

## Summary
The project evaluates whether a CPU‑only symbolic constraint‑graph preprocessing layer can mitigate the degradation of the distilled Edit‑R1 1B verifier on conflicting image‑editing instructions.

* **FR‑001 / FR‑009** – Curate a balanced 1000‑prompt dataset (500 conflicting, 500 neutral) **and collect human feasibility scores for **all 1000 prompts** via crowdsourcing (no “or at least 200” clause).  
* **FR‑002** – Build a spaCy + networkx pipeline that parses each instruction into a directed constraint graph (nodes = principles, edges = temporal or contradiction relations). The graph JSON contains **only abstract principle identifiers and edge labels**; no full paraphrased clauses are included (Graph abstraction constraint).  
* **FR‑003** – Run the baseline Edit‑R1 verifier on raw prompts, recording alignment scores against the human feasibility scores.  
* **FR‑004** – Feed the generated graphs as **structured JSON context** into the verifier’s prompt template and re‑run the evaluation (graph‑augmented condition).  
* **FR‑005 / FR‑006 / FR‑007** – Perform paired statistical tests (t‑test or Wilcoxon) on the **conflicting subset** and also on the **neutral subset** to ensure no degradation (SC‑006). Apply Benjamini‑Hochberg correction across all hypothesis tests.  
* **FR‑008** – Ensure total wall‑clock ≤ 6 h and peak RAM ≤ 7 GB.  
* **FR‑010** – Use **only human‑annotated scores** for all evaluation metrics; synthetic scores are excluded from analysis.

### Success‑Criteria Mapping
| SC ID | Requirement in Plan |
|-------|----------------------|
| SC‑001 | Report the **mean alignment‑score difference** (graph‑augmented minus baseline) for the conflicting subset. |
| SC‑002 | Measure and assert that the **symbolic parser runtime ≤ 30 min** (tied to SC‑002). |
| SC‑003 | Log peak RAM ≤ 7 GB (already part of FR‑008). |
| SC‑004 | Require **p < 0.05** for the primary improvement (paired test) after multiple‑comparison correction. |
| SC‑005 | Robustness check: effect‑size drop on hold‑out re‑phrased conflicts must be **non‑significant (p ≥ 0.05)**. |
| SC‑006 | Report **baseline verifier average alignment score** on the conflicting subset (mean ± SD). |
| SC‑007 | Compute **Pearson r ≥ 0.5** between verifier scores (both baseline and augmented) and human scores. |
| SC‑008 | Require **effect size ≥ 0.5** for the primary improvement. |
| SC‑009 | Record **baseline verifier runtime ≤ 2 h** on the full 1000‑prompt dataset (CPU‑only fallback). |
| SC‑010 | Use the baseline alignment score (from SC‑006) as the reference point for all improvement calculations. |

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:
- `torch==2.3.0` (CPU‑first, optional CUDA for GPU escape hatch)
- `transformers==4.44.0`
- `datasets==2.21.0`
- `spacy==3.7.4` + `en_core_web_sm`
- `networkx==3.3`
- `pandas==2.2.2`
- `numpy==2.0.0`
- `scipy==1.13.1`
- `statsmodels==0.14.2`
- `tqdm==4.66.5`
- `psutil==5.9.8`

**Storage**: Files under `data/` (raw parquet, curated CSV, graph JSON, result CSVs).  
**Testing**: `pytest` for unit tests and contract validation.  
**Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
**Performance Goals**: End‑to‑end ≤ 6 h, parser ≤ 30 min, baseline verifier ≤ 2 h CPU (or GPU escape hatch), memory ≤ 7 GB.  
**Constraints**: CPU‑only symbolic module; GPU offload only for the 1B verifier inference.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed random seeds; deterministic data processing; canonical HF URLs. |
| II. Verified Accuracy | All dataset and model URLs are from the verified list; citation titles meet overlap thresholds. |
| III. Data Hygiene | Raw parquet files are checksummed; every transformation writes a new file with provenance. |
| IV. Single Source of Truth | Every figure/table traces back to a single row in the CSV artifacts; no hand‑typed numbers. |
| V. Versioning Discipline | Content hashes recorded in `state/projects/...yaml`; any artifact change updates the timestamp. |
| VI. Symbolic Preprocessing Fidelity | Parser uses only spaCy, networkx, rule‑based logic; no GPU or differentiable components. |
| VII. Conflict‑Agnostic Robustness Validation | Separate analysis for conflicting vs. neutral prompts; paired tests; hold‑out re‑phrasing robustness check; effect‑size consistency requirement. |

## Project Structure
### Documentation (this feature)
```
specs/001-llmxive-verifier-graph/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── evaluation_report.schema.yaml
└── tasks.md   # generated later
```

### Source Code
```
src/
├── data/
│   ├── download.py            # fetch raw InstructPix2Pix parquet files
│   ├── curate.py              # build curated CSV, add human_score
│   ├── conflict_generator.py  # inject contradictions into neutral prompts
│   └── human_annotation.py    # launch crowdsourcing, write human_validation.csv
├── parser/
│   ├── graph_builder.py       # spaCy + networkx pipeline (abstraction constraint)
│   └── utils.py
├── verifier/
│   ├── baseline.py            # run Edit‑R1 verifier on raw prompts
│   └── augmented.py           # run verifier with graph JSON context + controls
├── analysis/
│   ├── stats.py               # paired tests, correlation, effect sizes, corrections
│   └── report.py              # generate report.json & report.csv
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
| None – all requirements fit within a single‑module design respecting CPU‑only constraint (except verifier inference, which uses the GPU escape hatch) | – | – |

---

