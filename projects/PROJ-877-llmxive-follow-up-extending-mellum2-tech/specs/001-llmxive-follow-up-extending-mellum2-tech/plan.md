# Implementation Plan: llmXive follow-up: extending "Mellum2 Technical Report"

**Branch**: `001-llmxive-complexity-loss` | **Date**: 2026-10-15 | **Spec**: `specs/001-llmxive-follow-up-extending-mellum2-tech/spec.md`  
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-mellum2-tech/spec.md`

## Summary
The project investigates whether static code complexity metrics (cyclomatic complexity, nesting depth, repetition ratio) correlate with per‑token prediction loss (and entropy) from a frozen LLM, and whether non‑linear structural thresholds exist. The pipeline:

1. **Power analysis** to determine feasible sample size `N` per language (Python, Java).  
2. **Download** a stratified sample of public repositories (codeparrot/github-code) – if unavailable, the pipeline logs the limitation and aborts (see Dataset Strategy).  
3. **Static analysis** with CodeQL & tree‑sitter to label each code chunk.  
4. **KenLM n‑gram model** for token‑frequency normalization (FR‑010).  
5. **CPU‑only LLM inference** (Mistral‑7B, fallback TinyLlama‑1.1B) to record per‑token loss & entropy (FR‑003).  
6. **Aggregation** to repository‑level means.  
7. **Statistical analysis**: Pearson & Spearman correlations (FR‑004), piecewise regression / change‑point detection (FR‑005), sensitivity sweep (FR‑006), block permutation test (FR‑007) with FDR correction (FR‑008).  
8. **Cross‑language validation** on the held‑out Java subset (FR‑009).  
9. **Human‑benchmark validation** (FR‑011) – if no verified benchmark is found, a limitation report is generated.  
10. **Outputs**: JSON report, Parquet tables, and figures.

All steps are deterministic, logged, and produce files that match the schemas in `contracts/`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `transformers`, `torch`, `tree-sitter`, `codeql`, `scikit-learn`, `statsmodels`, `pwlf`, `ruptures`, `pandas`, `pyarrow`, `matplotlib`, `seaborn`, `kenlm`  
- **Storage**: Ephemeral local filesystem (`/tmp` or `workspace/`). Processed artifacts stored under `data/processed/` as Parquet (snappy).  
- **Testing**: `pytest` with contract validation (`jsonschema`).  
- **Target Platform**: GitHub Actions `ubuntu-latest` (2 CPU, ~7 GB RAM, no GPU).  
- **Performance Goals**: ≤ 6 h total wall‑clock; ≤ 60 s per‑chunk inference; ≤ 7 GB RAM.  
- **Constraints**: CPU‑only inference (`device="cpu"`); strict per‑chunk timeout; exponential back‑off retries (max 3).  
- **Scale/Scope**: Aim for `N = 500` repositories per language (adjusted by Phase‑0 power analysis).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Random seeds are fixed in `code/config.py`; dataset fetched via `datasets.load_dataset` on every run; `requirements.txt` pins all versions. |
| II. Verified Accuracy | All citations point to the verified HuggingFace URL(s) listed in the “Verified datasets” block; no unverified URLs are used. |
| III. Data Hygiene | Raw downloads are checksummed (`sha256sum`) and recorded; transformations write new Parquet files; no in‑place edits. |
| IV. Single Source of Truth | Every figure/table references a specific row in a Parquet artifact; the final JSON report contains pointers to those rows. |
| V. Versioning Discipline | Content hashes are stored in `state/projects/PROJ-877-...yaml`; any artifact change updates the hash and timestamp. |
| VI. Static Analysis Inference Independence | Static analysis (CodeQL/tree‑sitter) runs **before** any LLM forward pass; no label is fed back into the model. |
| VII. Non‑Linear Threshold Detection Rigor | Piecewise regression (`pwlf`) and change‑point detection (`ruptures`) are mandatory; linear regression is only a baseline. |

All principles are satisfied; no violations detected.

## Project Structure
```text
specs/001-llmxive-follow-up-extending-mellum2-tech/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis.schema.yaml
    ├── code_chunk.schema.yaml
    ├── correlation_result.schema.yaml
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── threshold_result.schema.yaml

code/
├── __init__.py
├── config.py                # seeds, paths, hyper‑params
├── requirements.txt
├── data/
│   ├── download.py          # FR‑001
│   ├── static_analysis.py   # FR‑002
│   └── ngram.py             # FR‑010
├── inference/
│   ├── engine.py            # FR‑003
│   └── metrics.py           # FR‑004 helper
├── analysis/
│   ├── correlation.py       # FR‑004
│   ├── thresholds.py        # FR‑005, FR‑006
│   ├── significance.py      # FR‑007, FR‑008
│   └── validation.py        # FR‑009, FR‑011
├── viz/
│   └── plots.py             # scatter, piecewise fits
├── main.py                  # orchestrates phases, enforces ordering
└── utils/
    └── logging.py
```

## Complexity Tracking
No extra complexity beyond the modular pipeline; each phase is isolated to respect memory/cpu limits.

## Phase Execution Order (enforced by `code/main.py`)

| Phase | Description | FR/SC Covered |
|------|-------------|---------------|
| 0 | **Power & Feasibility Analysis** – compute MDES, set `N` per language. | SC‑005 |
| 1 | **Dataset Download & Stratified Sampling** – stream `codeparrot/github-code`, filter Python/Java, enforce `N` rows per language, write `data/processed/raw_samples.parquet`. | FR‑001, T002 |
| 2 | **Static Analysis** – CodeQL + tree‑sitter → enrich `CodeChunk`. | FR‑002, Edge Cases |
| 3 | **KenLM n‑gram Model** – build 5‑gram model for normalization. | FR‑010 |
| 4 | **LLM Inference** – CPU‑only forward pass, record loss/entropy, retry logic. | FR‑003, Edge Cases |
| 5 | **Aggregation** – repo‑level means (`RepositoryAggregate`). | FR‑004 |
| 6 | **Correlation Computation** – Pearson & Spearman, store `CorrelationResult`. | FR‑004, SC‑001 |
| 7 | **Threshold Detection** – piecewise regression, AIC/BIC comparison, sensitivity sweep. | FR‑005, FR‑006, SC‑002 |
| 8 | **Permutation Test & Multiple‑Comparison Correction** – block permutes at repo level, apply FDR. | FR‑007, FR‑008, SC‑003 |
| 9 | **Cross‑Language Validation** – repeat steps 6‑8 on Java subset. | FR‑009, SC‑004 |
|10 | **Human Benchmark Validation** – attempt load of CodeXGLUE; if unavailable, generate limitation report. | FR‑011 |
|11 | **Report Generation** – JSON report + figures, conform to `contracts/output.schema.yaml`. | All SCs |

Each phase writes a deterministic Parquet/JSON artifact that can be validated against the corresponding schema in `contracts/`.

---
