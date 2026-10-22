# Implementation Plan: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Branch**: `001-evaluating-llm-fidelity` | **Date**: 2026-10-22 | **Spec**: [spec.md](../specs/001-evaluating-llm-fidelity/spec.md)  
**Input**: Feature specification from `specs/001-evaluating-llm-fidelity/spec.md`

## Summary
The project delivers a fully reproducible, CPU‑first pipeline (no GPU fallback) that:

1. **Verifies statistical power** for a Friedman test with ≥500 paired samples, using explicit α = 0.05, two‑tailed, medium effect size (Cohen’s f = 0.25).  
2. **Extracts** ≥500 `(commit_message, doc_diff)` pairs from five popular Python repositories using the GitHub REST API, applying **stratified sampling** to balance repository‑level documentation style, commit frequency, and domain complexity.  
3. **Creates** a **human‑annotated gold‑standard** of 50 commit pairs, annotated independently by two annotators; inter‑annotator agreement (Cohen’s κ) is required to be ≥0.6, with disagreements resolved by a senior reviewer.  
4. **Runs inference** with three open‑source LLMs (Phi‑3‑mini, Gemma‑2‑2b, Llama‑3.2‑3B) in 4‑bit CPU mode. If any model exceeds the 60 s per‑commit timeout, the pipeline **reduces the per‑model sample size** (keeps total runtime ≤ 6 h) rather than switching hardware, preserving architectural isolation.  
5. **Extracts entities**:  
   - **Surface** – expanded regex patterns for file paths, function signatures (including multi‑line), class definitions, version numbers, imports, and variable assignments; any regex‑missed token is recovered via **AST verification** (walking the cloned repository).  
 - **Technical Intent** – zero‑shot classifier (`facebook/bart-large-mnli`) calibrated on a **held‑out validation split** ([deferred] of the human‑annotated gold set). If κ < 0.6, the pipeline falls back to a **simple keyword‑heuristic extractor** (keywords: because, fix, improve, handle, prevent).
6. **Computes** precision/recall for both categories, hallucination rate, and aggregates metrics into `data/processed/fidelity_metrics.csv`.  
7. **Performs statistical analysis**: normality testing → Friedman chi‑square (or repeated‑measures ANOVA if normal) → Holm‑Bonferroni correction across intent precision, surface precision, hallucination rate; reports effect sizes (Kendall’s W or η²).  
8. **Generates** visualizations (bar charts, confusion matrices) and a markdown summary.  
9. **Executes** the full pipeline on every push via GitHub Actions, caching model weights and uploading artifacts; all outputs are validated against the consolidated schema (`contracts/project.schema.yaml`).

All steps are deterministic, schema‑validated, and respect the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `requests`, `gitpython`, `datasets`, `transformers`, `bitsandbytes`, `torch>=2.0`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pandas`, `pyyaml`, `tqdm`, `astor`  
- **Storage**: File‑based CSV/JSON under `data/` (raw, intermediate, final)  
- **Testing**: `pytest` with contract validation in `tests/contract/`  
- **Target Platform**: Linux GitHub Actions runner (several CPU cores), ~7 GB RAM, ~several GB disk) – **CPU‑only**; no GPU escape hatch.  
- **Performance Goals**: Generation ≤60 s per commit on CPU (NFR‑001).  
- **Constraints**: Models run in 4‑bit quantization; total wall‑clock time ≤ 6 h per CI job.  
- **Scale/Scope**: Minimum 500 paired samples; default CI run processes a **stratified random subset of 200 samples** to stay within compute limits; a manual workflow can process the full set.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed random seed (`SEED=42`) in `src/utils.py`; all external data fetched from immutable URLs; single entry point `src/run_pipeline.py` orchestrates the workflow. |
| II. Verified Accuracy | All citations will be run through the Reference‑Validator before manuscript generation (per constitution). |
| III. Data Hygiene | Repository clones are checksum‑verified; each transformation writes a new file with provenance recorded in `data/metadata.yaml`. |
| IV. Single Source of Truth | Every figure, table, and metric references a unique row in `data/processed/fidelity_metrics.csv`. |
| V. Versioning Discipline | All artifacts are hashed; CI updates `state/projects/PROJ-104-...yaml` after each successful run. |
| VI. Commit-to-Doc Fidelity | Entity taxonomy (surface vs. intent) is defined in `data-model.md` and enforced via `project.schema.yaml`. |
| VII. Architectural Fidelity Isolation | All models run on the **same CPU hardware**; no hardware switching, ensuring differences are attributable solely to architecture. |

## Project Structure
```text
specs/001-evaluating-llm-fidelity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── project.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

Source code (single‑repo):
```text
src/
├── data_extraction.py          # GitHub API extraction → commitpair CSV
├── gold_annotation.py          # Human annotation workflow (2 annotators, κ≥0.6)
├── inference.py                # Model loading & generation (CPU‑only, adaptive sample size)
├── entity_extraction.py        # Regex + AST + zero‑shot classifier + heuristic fallback
├── scoring.py                  # Precision/recall & hallucination calculations
├── analysis.py                 # Power, normality, Friedman/ANOVA, corrections
├── utils.py                    # Seed, logging, checksum helpers
└── run_pipeline.py             # Orchestrator
tests/
├── contract/
│   └── test_schema_validation.py
└── unit/
    ├── test_data_extraction.py
    └── test_entity_extraction.py
```

## Phases & Task Mapping (covers all FR/SC)

| Phase | Description | Related FR | Related SC |
|-------|-------------|-----------|------------|
| **0 – Power Analysis** | Monte‑Carlo simulation (α = 0.05, f = 0.25, 10 000 reps) to estimate power for Friedman test with 500 pairs. | – | SC‑004 |
| **1 – Data Acquisition & Pairing** | Use GitHub REST API (`/repos/:owner/:repo/commits`) with `since=2 years ago`; stratified sampling ensures each repo contributes ~100 pairs; keep only `.md`/`.rst` files; fetch raw diffs via `git show <sha>`. Output `data/raw/commit_pairs.csv`. | FR‑001, FR‑007 | SC‑001 |
| **2 – Human Gold‑Standard Annotation** | Randomly sample 50 commit hashes; two independent annotators label intent entities using the taxonomy; compute Cohen’s κ; require κ ≥ 0.6; resolve disagreements; store in `data/gold/annotations.csv`. | FR‑008 | SC‑001, SC‑003 |
| **3 – Model Inference** | Benchmark each model on a set of pilot commits.; if any exceed 60 s, reduce per‑model sample size (maintain total ≤ 200 for CI). Generate docs with 4‑bit quantization, retry up to 2× on failure, log failures. | FR‑002, NFR‑001 | SC‑002 |
| **4 – Entity Extraction** | (a) Surface: expanded regex + AST verification (file paths, multi‑line signatures, classes, imports, version numbers). (b) Intent: zero‑shot classifier calibrated on held‑out [deferred] of gold set; if κ < 0.6, use keyword‑heuristic extractor. | FR‑003, FR‑006 | SC‑003 |
| **5 – Fidelity Scoring** | Compute per‑sample precision/recall for intent & surface, hallucination rate; write `data/processed/fidelity_metrics.csv`. | FR‑004 | SC‑003 |
| **6 – Statistical Analysis** | Normality test → Friedman (or repeated‑measures ANOVA) → Holm‑Bonferroni correction across intent precision, surface precision, hallucination rate; report effect sizes. | FR‑005 | SC‑004 |
| **7 – Visualization & Reporting** | Bar chart of intent precision per model, confusion matrix for surface entities, hallucination‑rate line plot; assemble `results/summary.md`. | FR‑005 | SC‑004, SC‑005 |

### How T003 & T004 are Fixed
* **T003 (Data Extraction)** – Switched to deterministic GitHub REST API with stratified sampling; output is a CSV that validates against the `CommitPair` schema.  
* **T004 (Gold Annotation)** – Implemented a reproducible human‑annotation workflow with dual annotators and κ ≥ 0.6, eliminating the previous unattended rule‑based step.

---

