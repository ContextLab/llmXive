# Implementation Plan: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

**Branch**: `001-evaluating-code-summarization-bug-localization` | **Date**: 2026-10-19 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-evaluating-code-summarization-bug-localization/spec.md`

## Summary
We will build a reproducible research pipeline that (1) obtains a **verified open Defects4J v2.0** dataset, (2) creates three summary conditions (baseline, rule‑based via srcML, LLM‑generated via CodeLlama‑7B with 8‑bit quantization on a GPU escape hatch), (3) logs simulated participant interactions for CI verification and real interactions for the actual study, and (4) runs a statistically rigorous analysis (GLMM for accuracy, LME for speed) with **Holm‑Bonferroni** correction (α = 0.05) and cluster bootstrap confidence intervals. All scripts are deterministic, seeded (`42`), and produce files that can be validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `linearmodels`, `datasets`, `srcml` (via subprocess), `torch` (8‑bit quantized CodeLlama), `scipy`, `pyyaml`  
- **Storage**: CSV/Parquet files under `data/`  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (CPU‑only) for CI; optional GPU escape hatch on Kaggle for real LLM inference  
- **Project Type**: Research pipeline / CLI tool  
- **Constraints**: ≤ 6 h runtime, ≤ 7 GB RAM, ≤ 14 GB disk, no GPU in CI, all random seeds pinned, Defects4J version pinned (`data/defects4j_version.txt`)  

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All seeds (`42`) are hard‑coded; `requirements.txt` pins exact versions; dataset is loaded from a **verified HuggingFace URL**; scripts are pure functions with deterministic output. |
| II. Verified Accuracy | Citations in `research.md` point only to the three verified Defects4J URLs provided. |
| III. Data Hygiene | Raw downloads are checksum‑verified; derived files are written to new filenames; PII removal is enforced by `code/utils/pii.py`. |
| IV. Single Source of Truth | Every figure/table in the eventual manuscript will be generated from `data/analysis_results/*.json` which trace back to a single row in the interaction log. |
| V. Versioning Discipline | Content hashes of all artifacts are recorded in `state/projects/PROJ-140-.../artifact_hashes`. |
| VI. Human‑Subject Data Protection | Interaction logs are anonymized (SHA‑256 hashed IDs) before committing; original consent files live in `.gitignore`‑ed `data/consent/`. |
| VII. Benchmark Dataset Integrity | Defects4J version (`2.0`) is recorded in `data/defects4j_version.txt`; summaries are stored separately, leaving original source unchanged. |

All principles are satisfied; no violations.

## Project Structure
```text
specs/001-evaluating-code-summarization-bug-localization/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── interaction.schema.yaml
    └── analysis.schema.yaml

code/
├── __init__.py
├── main.py                # CLI entry point
├── config.py
├── data_prep/
│   ├── download_defects4j.py      # T-002 (re‑implemented)
│   └── generate_summaries.py      # T-003a (re‑implemented)
├── simulation/
│   └── simulate_study.py
├── analysis/
│   └── run_statistics.py
├── utils/
│   ├── pii.py
│   └── timing.py
└── llm_gpu/
    └── run_llm_gpu.sh          # Offline GPU escape hatch script

data/
├── raw/
│   └── defects4j.parquet
├── processed/
│   ├── methods.csv
│   ├── summaries_rule.csv
│   └── summaries_llm.csv   # populated only by GPU escape hatch
├── interaction_logs/
│   ├── simulated_logs.csv
│   └── anonymized_logs.csv
├── analysis_results/
│   └── results.json
└── defects4j_version.txt

tests/
├── unit/
│   ├── test_download.py
│   ├── test_generate_summaries.py
│   └── test_analysis.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

.github/
└── workflows/
    ├── ci.yml
    ├── test_reproducibility.yml
    └── validate_citations.yml
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| GPU Escape Hatch for LLM | CodeLlama‑7B cannot finish within 30 s on CPU; attempting a CPU‑only approximation would be fabrication. | Running a tiny toy model would not answer the research question. |
| Dual Data Path (sim vs. real) | CI cannot collect human data nor run GPU inference; we need a deterministic simulation for CI while preserving a real‑mode path for the actual study. | Using only the real path would break CI; using only simulation would make the study impossible. |
| Cluster Bootstrap (participants) | Required to obtain CI for effect sizes with repeated measures; simple normal‑approx CI would be invalid with N = 12. | Parametric CIs ignore within‑subject correlation. |

## Implementation Tasks (mapped to FR/SC)

| Task ID | Description | FR(s) addressed | SC(s) addressed |
|---------|-------------|----------------|-----------------|
| **T-001** | Create `requirements.txt` with exact version pins. | — | I, II |
| **T-002** | `code/data_prep/download_defects4j.py` – load Defects4J via `datasets.load_dataset(..., streaming=True)`, verify SHA‑256 checksums, write to `data/raw/defects4j.parquet`, write version to `data/defects4j_version.txt`. | FR‑001 | I, III, VII |
| **T-003** | `code/data_prep/generate_summaries.py` – (a) extract methods → `data/processed/methods.csv`; (b) rule‑based summaries via srcML → `data/processed/summaries_rule.csv`; (c) **GPU‑only** stub that raises informative error if `--mode=real` without GPU. | FR‑002, FR‑003 | I, III |
| **T-004** | `code/utils/timing.py` – perform loopback latency test, assert ≤ 100 ms, log result. | FR‑003 | I |
| **T-005** | `code/simulation/simulate_study.py` – generate Latin‑square design for 12 participants × 10 tasks/condition, produce `data/interaction_logs/simulated_logs.csv`. | FR‑003 | I |
| **T-006** | `code/utils/pii.py` – hash participant IDs, strip any PII, write `data/interaction_logs/anonymized_logs.csv`. | FR‑003, VI | III, VI |
| **T-007** | `code/analysis/run_statistics.py` – (a) GLMM for accuracy (logit link, random intercept); (b) LME for speed (log‑transformed time, random intercept); (c) compute Odds Ratio & standardized beta; (d) cluster bootstrap (N = 12, seed = 42) for 95 % CI; (e) Holm‑Bonferroni correction (α = 0.05). | FR‑004, FR‑005, FR‑006 | III, IV, V |
| **T-008** | `code/main.py` – orchestrates: download → summaries → latency test → (sim or real) interaction log → analysis → writes `data/analysis_results/results.json`. | FR‑001‑FR‑007 | I |
| **T-009** | `scripts/run_llm_gpu.sh` – **offline manual** step: runs CodeLlama‑7B 8‑bit on Kaggle GPU, writes `data/processed/summaries_llm.csv`. | FR‑002 (real mode) | VII |
| **T-010** | CI workflow `ci.yml` – executes `python -m code.main --mode sim`, runs unit & contract tests, enforces ≤ 6 h runtime via timeout. | FR‑007 | I, V |
| **T-011** | Reproducibility workflow `test_reproducibility.yml` – runs full pipeline on fresh runner, hashes `results.json`, compares to stored reference hash (tolerance = 1e‑6). | FR‑007 | I |
| **T-012** | Citation validation workflow `validate_citations.yml` – runs Reference‑Validator on all markdown files. | — | II |
| **T-013** | Documentation: update `README.md` with OSF publishing instructions, include license, usage notes. | FR‑007 | I, VI |

All functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑005) are covered by at least one task.  

---
