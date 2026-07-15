# Implementation Plan: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Branch**: `001-gene-regulation` | **Date**: 2026-07-14 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project will (1) download the open‑source VulDeePecker and Juliet datasets (≤ 5 000 labeled snippets), (2) run zero‑shot inference with a CPU‑quantized open‑source code LLM (StarCoder‑Base quantized to 4‑bit), (3) extract structural, semantic, and embedding‑based features for each snippet (using an EXTERNAL vulnerability pattern corpus to prevent data leakage), (4) run baseline static analyzers (Bandit for Python, cppcheck for C), and (5) perform the full statistical suite (precision/recall/F1/ROC‑AUC per category, Point-Biserial correlations with multiple‑comparison correction, Binary Logistic Regression, McNemar’s test on matched samples, and a sensitivity analysis on a human‑verified subset). All steps are orchestrated in a reproducible, chunk‑aware pipeline that respects the CPU budget on GitHub Actions.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:
- `datasets` ≥ 2.18.0 (HuggingFace)
- `tree_sitter` ≥ 0.20.0
- `radon` ≥ 6.0.1 (cyclomatic complexity)
- `torch` ≥ 2.3.0 (CPU)
- `bitsandbytes` ≥ 0.43.1 (CPU‑compatible 4‑bit quantization)
- `sentence‑transformers` ≥ 2.7.0 (CodeBERT‑small for embeddings)
- `bandit` ≥ 1.7.8
- `cppcheck` (apt‑package)
- `scikit‑learn` ≥ 1.5.0
- `statsmodels` ≥ 0.14.2
- `pandas` ≥ 2.2.2
- `numpy` ≥ 1.26.4
- `pytest` ≥ 8.2.0

**Storage**: Files under `data/` (raw, processed, results). All intermediate artefacts are version‑hashed.

**Testing**: `pytest` with contract‑based validation (see `contracts/`).

**Target Platform**: Linux x86_64 GitHub Actions runner (2 CPU cores, ≤ 7 GB RAM).

**Project Type**: Research library/CLI pipeline.

**Performance Goals**: Per‑sample LLM inference ≤ 43 s; total wall‑clock ≤ 6 h.

**Constraints**: CPU‑only inference; no GPU unless the fallback off‑load is triggered (not needed with 4‑bit StarCoder). All datasets must be streamed or sampled to stay under RAM limits.

**Scale/Scope**: Up to 5 000 code snippets across C, Python, JavaScript.

## Constitution Check
| Principle | Requirement | How the plan satisfies it |
|-----------|-------------|---------------------------|
| I. Reproducibility | Pin random seeds, deterministic data loaders, fixed dataset versions. | Seeds set in `code/config.py`; dataset versions locked via HF revision tags; all scripts are idempotent. |
| II. Verified Accuracy | All external citations must be validated. | Only the three verified dataset URLs (see `research.md`) and the external CWE corpus source are cited. |
| III. Data Hygiene | Checksums, immutable raw files, derivations written to new files. | Raw downloads checksum‑verified; each transformation writes a new file with a hash‑based filename. |
| IV. Single Source of Truth | Every figure/statistic traces to a single data row. | All metrics are computed directly from `data/processed/*.csv`; no manual transcription. |
| V. Versioning Discipline | Content‑hash artefacts tracked. | `state/projects/PROJ-282...yaml` will store hashes for each artefact. |
| VI. Computational Resource Limits (NON‑NEGOTIABLE) | ≤ 6 h, ≤ 7 GB RAM, per‑sample ≤ 43 s. | CPU‑quantized small-scale model, batch size = 8, streaming dataset; worst‑case runtime estimated at 4.8 h. |
| VII. Baseline Comparison (NON‑NEGOTIABLE) | Must compare against Bandit & cppcheck. | Tasks T030‑T034 explicitly run these tools and generate matching result schemas. |

## Project Structure
```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── prediction_result.schema.yaml
    ├── feature_vector.schema.yaml
    └── analysis_metric.schema.yaml

code/
├── __init__.py
├── config.py            # seeds, paths, constants
├── data/
│   ├── download.py      # fetches VulDeePecker & Juliet
│   ├── preprocess.py    # parses, extracts structural/semantic features
│   ├── embed.py         # loads CodeBERT‑small, computes KNN similarity scores
│   ├── llm_infer.py     # zero‑shot inference with StarCoder
│   ├── static_analyze.py# runs Bandit / cppcheck
│   └── analysis.py      # stats, logistic regression, McNemar, sensitivity
├── utils/
│   ├── batching.py
│   └── logging.py
└── main.py              # orchestrates the pipeline

tests/
├── contract/
│   ├── test_prediction_schema.py
│   ├── test_feature_schema.py
│   └── test_analysis_schema.py
└── integration/
    └── test_end_to_end.py
```

**Structure Decision**: A single `code/` package holds all pipeline stages; this matches the “library/CLI” pattern and keeps the repository minimal.

## Phase Mapping (covers every FR & SC)

| Phase | Tasks | FR(s) addressed | SC(s) addressed |
|-------|-------|-----------------|-----------------|
| **0 – Setup** | Install deps, verify checksums, set seeds. | FR‑001, FR‑030 (constitution) | — |
| **1 – Data Acquisition** | `download.py` streams VulDeePecker & Juliet (≤ 5 000 rows). | FR‑001 | — |
| **2 – Feature Extraction** | `preprocess.py` (AST, cyclomatic, taint APIs). <br> **T021**: `embed.py` loads CodeBERT‑small (4‑bit CPU) and computes KNN similarity (k=5) to an EXTERNAL vulnerability pattern corpus (CWE Top 25). <br> *Implementation Detail*: The script explicitly loads the pre-trained encoder, encodes the external corpus (pre-computed), then iterates through the dataset snippets to compute the average cosine similarity to the top-5 neighbors. | FR‑003, FR‑004 | — |
| **3 – Zero‑Shot LLM Inference** | `llm_infer.py` batches ≤ 8 snippets, runs StarCoder‑Base (4‑bit) on CPU, records `is_correct`, `predicted_label`, `inference_time_ms`. Handles truncation, “uncertain” mapping, and missing ground‑truth exclusion. | FR‑002, FR‑007, FR‑011 (sensitivity) | — |
| **4 – Baseline Static Analysis** | `static_analyze.py` runs Bandit (Python) and cppcheck (C). Results normalized to same schema as LLM. | FR‑008, FR‑009 | — |
| **5 – Metric Computation** | `analysis.py` computes per‑category precision/recall/F1/ROC‑AUC, **Point-Biserial** correlations (with Benjamini‑Hochberg correction), **Binary Logistic Regression** (statsmodels GLM), **McNemar’s test** (on matched samples only), and conducts sensitivity analysis on a random 100‑sample human‑verified subset. | FR‑005, FR‑006, FR‑010, FR‑011 | SC‑001, SC‑002, SC‑003, SC‑004, SC‑006 |
| **6 – Reporting** | Writes JSON/CSV artefacts, generates figures via matplotlib, stores reproducible notebooks. | — | SC‑005 |

All functional requirements (FR‑001 – FR‑011) and success criteria (SC‑001 – SC‑006) are explicitly covered.
