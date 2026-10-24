# Implementation Plan: llmXive follow‑up – Graph‑augmented Verifier Evaluation

**Branch**: `001-llmxive-verifier-graph` | **Date**: 2026‑10‑23 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-verifier-graph/spec.md`

## Summary
The project evaluates whether a **CPU‑only symbolic constraint‑graph** preprocessing layer mitigates the degradation of the distilled Edit‑R1 1B verifier on *conflicting* image‑editing instructions. The pipeline:

1. **Download & curate** a balanced 1 000‑prompt dataset (500 conflicting, 500 neutral) from open InstructPix2Pix parquet shards, verifying SHA‑256 checksums.  
2. **Collect human feasibility scores for the entire set of prompts.** (FR‑001 & FR‑009 satisfied).  
3. **Parse** each instruction into a directed constraint graph using spaCy + networkx, employing multiple heuristics (cue‑words, antonym dictionary, temporal markers) (FR‑002, Principle VI).  
4. **Run baseline verifier** on raw prompts (CPU‑only 8‑bit Edit‑R1 1B) with a **runtime target ≤ 2 hours** (SC‑009).  
5. **Randomization & Counterbalancing** (FR‑008, SC‑002) – fixed‑seed permutation of condition order per prompt.  
6. **Run graph‑augmented verifier** with JSON graph context (FR‑004).  
7. **Statistical comparison** (paired test, multiple‑comparison correction, robustness hold‑out, power analysis with contingency) (FR‑005‑FR‑008).  
8. **Generate a machine‑readable report** conforming to `contracts/evaluation_report.schema.yaml` (FR‑010).  

All phases respect the established wall‑clock time limit. and ≤ 7 GB RAM on a GitHub Actions free‑tier runner (Principle I, SC‑002, SC‑003, SC‑009). The baseline runtime estimate is ≈ 0.3 s per prompt ([deferred] total); if the run exceeds 2 h the pipeline aborts and reports the limitation.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `torch==2.3.0` (CPU‑only, 8‑bit quantized)  
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
- **Constraints**: Symbolic parser CPU‑only; baseline verifier runs **CPU‑only 8‑bit** inference (no GPU fallback).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed random seeds (`numpy`, `torch`, `random`); deterministic data loaders (`datasets.load_dataset` with explicit URLs); all scripts are CI‑runnable. |
| II. Verified Accuracy | All external URLs are taken from the verified list in the spec; citation titles meet the required overlap. |
| III. Data Hygiene | Raw parquet files are checksummed; every transformation writes a new file with provenance metadata (`*_provenance.json`). |
| IV. Single Source of Truth | Every figure/table is derived from a single CSV/JSON artifact; no hand‑typed numbers. |
| V. Versioning Discipline | Content hashes of all artifacts are recorded in `state/projects/PROJ-817-...yaml`; any change updates the timestamp. |
| VI. Symbolic Preprocessing Fidelity | Parser uses only spaCy, networkx, and rule‑based logic; no GPU or differentiable components. |
| VII. Conflict‑Agnostic Robustness Validation | Separate analysis for conflicting vs. neutral prompts; paired tests; hold‑out re‑phrased conflict set; multiple‑comparison correction. |

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
│   ├── download.py            # streams verified parquet files, verifies checksums
│   ├── curate.py              # balances, assigns UUIDs, writes to data/results/
│   ├── human_annotation.py    # crowdsourcing wrapper, writes human_validation.csv
│   └── filter_conflicts.py    # heuristic filter for naturally occurring conflicts
├── parser/
│   ├── graph_builder.py       # spaCy + networkx pipeline with multi‑heuristic detection
│   └── utils.py
├── verifier/
│   ├── baseline.py            # runs Edit‑R1 on raw prompts (CPU‑only 8‑bit)
│   └── augmented.py           # runs verifier with graph JSON context + two controls
├── analysis/
│   ├── stats.py               # paired tests, corrections, power checks
│   └── report.py              # writes report.json / report.csv
└── cli/
    └── run_all.py             # orchestrates the full pipeline

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
| **0 – Data Acquisition** | `src/data/download.py` (stream three verified parquet URLs, verify SHA‑256) → `src/data/curate.py` (balance, assign IDs, write to `data/results/curated_prompts.csv`) | FR‑001, FR‑009 (human scores later) | SC‑002, SC‑003 |
| **1 – Human Annotation** | `src/data/human_annotation.py` (crowd‑source **all 1 000** prompts) → merge into `curated_prompts.csv` | FR‑001, FR‑009, FR‑010 (synthetic never used for evaluation) | SC‑001, SC‑006, SC‑007 |
| **2 – Symbolic Graph Construction** | `src/parser/graph_builder.py` (spaCy + networkx, ≤ 30 min) | FR‑002 | SC‑002 |
| **3 – Baseline Verifier Evaluation** | `src/verifier/baseline.py` (CPU‑only 8‑bit Edit‑R1 1B) | FR‑003 | SC‑009 (target ≤ 2 h) |
| **4 – Randomization & Counterbalancing** | Fixed‑seed permutation of condition order per prompt (`numpy.random.seed(12345)`) | FR‑008 | SC‑002 |
| **5 – Graph‑Augmented Evaluation** | `src/verifier/augmented.py` (inject graph JSON, plus two control conditions) | FR‑004 | – |
| **6 – Statistical Analysis** | `src/analysis/stats.py` (paired test, normality check, Wilcoxon fallback, Benjamini‑Hochberg correction, robustness hold‑out, power analysis with contingency for small effect sizes) | FR‑005, FR‑006, FR‑007, FR‑008 | SC‑001‑SC‑008 |
| **7 – Reporting** | `src/analysis/report.py` (generate `report.json` & `report.csv` conforming to contract) | FR‑010 (no synthetic scores) | SC‑001‑SC‑010 |
| **8 – Verification** | `pytest` contract suite | – | – |

All phases are ordered so that data is available before any consumer step, models are fitted before evaluation, and figures/reports are generated last.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None – all requirements fit within a single‑module design respecting CPU‑only constraint (except verifier inference, which now uses 8‑bit CPU quantization) | – | – |

---


