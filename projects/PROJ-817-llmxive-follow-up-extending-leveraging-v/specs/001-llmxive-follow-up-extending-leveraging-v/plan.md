# Implementation Plan: llmXive follow‑up – Graph‑augmented Verifier Evaluation

**Branch**: `001-llmxive-verifier-graph` | **Date**: 2026-10-22 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-llmxive-verifier-graph/spec.md`

## Summary
The project evaluates whether a **CPU‑only symbolic constraint‑graph** preprocessing layer mitigates the degradation of the distilled Edit‑R1 1B verifier on *conflicting* image‑editing instructions.  

Key steps:

1. **Download & curate** a balanced prompt dataset (equal numbers of conflicting and neutral) from the open InstructPix2Pix parquet shards.  
2. **Collect human feasibility scores for **all 1 000 prompts** (FR‑001 & FR‑009 reconciled).  
3. **Parse** each instruction into a directed constraint graph using spaCy + networkx (FR‑002, Principle VI).  
4. **Run baseline verifier** on raw prompts (FR‑003).  
5. **Run graph‑augmented verifier** with the JSON graph supplied as context (FR‑004).  
6. **Statistical comparison** (paired test, multiple‑comparison correction, robustness hold‑out) (FR‑005‑FR‑008).  
7. **Report generation** conforming to `contracts/evaluation_report.schema.yaml` (SC‑001 – SC‑010).  

All phases respect the prescribed wall‑clock time constraint. and ≤ 7 GB RAM limits (FR‑008) and are fully reproducible (Principle I).

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
- **Performance Goals**: End‑to‑end ≤ 6 h; parser ≤ 30 min; baseline verifier ≤ 2 h; peak RAM ≤ 7 GB.  
- **Constraints**: Symbolic parser CPU‑only; baseline verifier runs **CPU‑only 8‑bit quantized inference** (no GPU escape hatch).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed seeds (`numpy`, `torch`, `random`); deterministic data loaders (`datasets.load_dataset` with explicit URLs); all scripts are CI‑runnable. |
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
│   ├── curate.py              # builds balanced CSV, assigns UUIDs, adds synthetic scores
│   ├── human_annotation.py    # crowdsourcing wrapper, writes human_validation.csv
│   └── conflict_generator.py  # deterministic rule‑based contradiction injection
├── parser/
│   ├── graph_builder.py       # spaCy + networkx pipeline
│   └── utils.py
├── verifier/
│   ├── baseline.py            # runs Edit‑R1 on raw prompts (CPU‑only 8‑bit)
│   └── augmented.py           # runs verifier with graph JSON context + controls
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
| **0 – Data Acquisition** | `download.py` (stream three verified parquet URLs, verify SHA‑256) → `curate.py` (balance, assign IDs, compute synthetic feasibility) | FR‑001, FR‑009 (human scores later) | SC‑002, SC‑003 |
| **1 – Human Annotation** | `human_annotation.py` (crowd‑source **all 1 000** prompts) → merge into `curated_prompts.csv` | FR‑001, FR‑009, FR‑010 | SC‑001, SC‑006, SC‑007 |
| **2 – Symbolic Graph Construction** | `graph_builder.py` (spaCy + networkx, ≤ 30 min) | FR‑002 | SC‑002 |
| **3 – Baseline Verifier Evaluation** | `baseline.py` (run Edit‑R1 1B **CPU‑only 8‑bit**; no GPU) | FR‑003 | SC‑009 |
| **4 – Randomization & Counterbalancing** | For each prompt, randomly permute the order of condition execution (baseline, graph‑augmented, control‑filler, control‑empty) using a fixed seed. | – | – |
| **5 – Graph‑Augmented Evaluation** | `augmented.py` (inject graph JSON, plus two control conditions) | FR‑004 | – |
| **6 – Statistical Analysis** | `stats.py` (paired test, normality check, Wilcoxon fallback, Benjamini‑Hochberg correction, robustness hold‑out, power analysis) | FR‑005, FR‑006, FR‑07, FR‑008 | SC‑001‑SC‑008 |
| **7 – Reporting** | `report.py` (generate `report.json` & `report.csv` conforming to contract) | FR‑010 (no synthetic scores used) | SC‑001‑SC‑010 |
| **8 – Verification** | `pytest` contract suite | – | – |

All phases are ordered so that data is available before any consumer step, models are fitted before evaluation, and figures/reports are generated last.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None – all requirements fit within a single‑module design respecting CPU‑only constraint (except verifier inference, which now uses 8‑bit CPU quantization) | – | – |

---

