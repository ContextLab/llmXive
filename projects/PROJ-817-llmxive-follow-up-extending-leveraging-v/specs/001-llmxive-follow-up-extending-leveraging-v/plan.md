# Implementation Plan: llmXive follow‑up – Graph‑augmented Verifier Evaluation

**Branch**: `001-llmxive-verifier-graph` | **Date**: 2026‑10‑24 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-leveraging-v/spec.md`

## Summary
The project evaluates whether a **CPU‑only symbolic constraint‑graph** preprocessing layer reduces the alignment degradation of the distilled Edit‑R1 1B verifier on *conflicting* image‑editing prompts. The pipeline:

1. Download and verify three open InstructPixPix parquet shards.  
2. Curate a balanced CSV of **1 000 prompts** (500 conflicting, 500 neutral).  
3. Collect **human feasibility scores for all 1 000 prompts** via crowdsourcing; store in `data/results/human_validation.csv`.  
4. Parse every instruction into a directed constraint graph (spaCy + networkx).  
5. Run baseline verifier (CPU‑only 8‑bit) on raw prompts.  
6. Run graph‑augmented verifier with JSON graph context plus two control contexts.  
7. Perform paired statistical tests (t‑test or Wilcoxon) on the **full 1 000 human‑scored prompts**, with multiple‑comparison correction and a robustness hold‑out.  
8. Generate a machine‑readable report conforming to `contracts/evaluation_report.schema.yaml`.

All phases respect the 2‑core, ≤ 7 GB RAM, ≤ 6 h CI budget (Principles I, III, SC‑002, SC‑003, SC‑009).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `torch==2.3.0` (CPU‑only, 8‑bit quantization)  
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
- **Storage**: Files under `data/` (parquet, CSV, JSON).  
- **Testing**: `pytest` + contract validation.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
- **Constraints**: Symbolic parser CPU‑only; verifier runs **CPU‑only 8‑bit** inference (no GPU fallback).  

## Constitution Check
| Principle | Satisfaction |
|-----------|--------------|
| I. Reproducibility | Fixed random seeds; deterministic data loaders; all scripts runnable on fresh CI. |
| II. Verified Accuracy | All external URLs come from the verified list in the spec; titles meet the overlap threshold. |
| III. Data Hygiene | Raw parquet files streamed, SHA‑256 checksummed, provenance recorded in `data/raw/provenance.json`. |
| IV. Single Source of Truth | Every figure/table derives from a single CSV/JSON artifact; no hand‑typed numbers. |
| V. Versioning Discipline | Content hashes of all artifacts recorded in `state/projects/PROJ-817-…yaml`; timestamps updated on change. |
| VI. Symbolic Preprocessing Fidelity | Parser uses only spaCy, networkx, and rule‑based logic; no GPU or differentiable components. |
| VII. Conflict‑Agnostic Robustness Validation | Separate analyses for conflicting vs. neutral prompts; paired tests; hold‑out re‑phrased set; multiple‑comparison correction. |

## Project Structure
```
specs/001-llmxive-verifier-graph/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── evaluation_report.schema.yaml
└── tasks.md   # generated later

src/
├── data/
│   ├── download.py            # stream verified parquet files, verify checksums
│   ├── curate.py              # balance, assign UUIDs, write curated_prompts.csv
│   ├── conflict_verify.py     # manual/heuristic verification of conflict status
│   ├── human_annotation.py    # crowdsourcing wrapper, writes human_validation.csv (1000 prompts)
│   └── filter_conflicts.py    # heuristic filter, creates balanced CSV
├── parser/
│   ├── graph_builder.py       # spaCy + networkx pipeline, ≤30 min
│   └── utils.py
├── verifier/
│   ├── baseline.py            # CPU‑only 8‑bit inference on raw prompts
│   └── augmented.py           # inference with graph JSON + control contexts
├── analysis/
│   ├── stats.py               # paired tests, corrections, power checks
│   └── report.py              # writes report.json / report.csv
└── cli/
    └── run_all.py             # orchestrates full pipeline

tests/
├── unit/
│   ├── test_graph_builder.py
│   └── test_stats.py
└── contract/
    └── test_evaluation_report.py
```

## Phase Mapping (covers every FR & SC)

| Phase | Tasks | FR(s) addressed | SC(s) addressed |
|-------|-------|-----------------|-----------------|
| **0 – Data Acquisition** | `src/data/download.py` → `src/data/curate.py` → `src/data/conflict_verify.py` | FR‑001, FR‑009 (human scores later) | SC‑002, SC‑003 |
| **0‑b – Conflict Verification** | Manual/heuristic labeling of conflict status (exact 500/500) | FR‑001 (ensures true conflict set) | SC‑002 |
| **1 – Human Annotation (1 000 prompts)** | `src/data/human_annotation.py` (crowd‑source all 1 000 prompts) → merge into `curated_prompts.csv` | FR‑009, FR‑010 (synthetic scores never used) | SC‑001, SC‑006 |
| **2 – Symbolic Graph Construction** | `src/parser/graph_builder.py` (spaCy + networkx, ≤30 min) | FR‑002 | SC‑002 |
| **3 – Baseline Verifier Evaluation** | `src/verifier/baseline.py` (CPU‑only 8‑bit) | FR‑003 | SC‑009 (≤2 h) |
| **4 – Randomization & Counterbalancing** | Fixed‑seed permutation of condition order per prompt | (supports reproducibility) | SC‑002 |
| **5 – Graph‑Augmented Evaluation** | `src/verifier/augmented.py` (graph + two controls) | FR‑004 | – |
| **6 – Statistical Analysis** | `src/analysis/stats.py` (paired test, normality check, Wilcoxon fallback, Benjamini‑Hochberg correction, robustness hold‑out, power analysis) | FR‑005, FR‑006, FR‑008 | SC‑001‑SC‑008 |
| **7 – Reporting** | `src/analysis/report.py` (machine‑readable JSON, CSV) | FR‑010 (no synthetic scores) | SC‑001‑SC‑010 |
| **8 – Verification** | `pytest` contract suite | – | – |

All phases are ordered so that data is available before consumption, models are fitted before evaluation, and reports are generated last.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None – all requirements fit within a single‑module design respecting CPU‑only constraints (baseline inference uses 8‑bit quantization) | – | – |

---

