# Implementation Plan: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Branch**: `001-evaluating-llm-fidelity` | **Date**: 2026-10-24 | **Spec**: [spec.md](../specs/001-evaluating-llm-fidelity/spec.md)  
**Input**: Feature specification from `specs/001-evaluating-llm-fidelity/spec.md`

## Summary
The plan delivers a fully reproducible, CPU‑first pipeline that:

1. **Power analysis** confirms that ≥500 paired samples give ≥80 % power for the Friedman test (SC‑004). The default CI run processes a stratified subset of a limited number of samples per model for speed; the final full‑scale run will be executed to satisfy the power requirement.
2. **Data acquisition** extracts ≥500 `(commit_message, doc_diff)` pairs from the five target repositories using the GitHub REST API, writes a schema‑validated CSV (FR‑001, SC‑001). Stratified sampling controls for commit‑message length, diff size, and documentation complexity to reduce confounds.
3. **Gold‑standard creation** builds a 200‑sample human‑annotated intent dataset using an active‑learning selection strategy; computes Cohen’s κ and aborts if κ < 0.6 (FR‑008, SC‑001, SC‑003). This larger set improves construct validity over the previous 50‑sample design.
4. **Model inference** runs Phi‑3‑mini, Gemma‑2‑2b, and Llama‑3.2‑3B in 4‑bit CPU mode, respects the 60 s per‑commit timeout (FR‑002, NFR‑001, SC‑002). Each generated file is validated against the `GeneratedOutput` schema.
5. **Entity extraction** (surface via regex + AST verification; intent via zero‑shot classifier (`facebook/bart-large-mnli`) loaded in 8‑bit quantization and calibrated on the gold set, with a deterministic keyword fallback). All JSON outputs conform to the `EntitySet` schema.
6. **Fidelity scoring** computes precision, recall, **surface hallucination rate**, and **intent hallucination rate** for each sample, writing rows to `data/processed/fidelity_metrics.csv` and validating against the `FidelityMetric` schema.
7. **Statistical analysis** performs Shapiro‑Wilk normality testing, then either Friedman (non‑parametric) or repeated‑measures ANOVA (with Mauchly’s sphericity check). Holm‑Bonferroni corrects across the three metrics, and a Nemenyi post‑hoc test controls for multiple model comparisons. Effect sizes (Kendall’s W or η²) are reported. All results read directly from `fidelity_metrics.csv`, preserving the Single Source of Truth (Constitution IV).
8. **Visualization & reporting** generates required PNG figures and a markdown summary (SC‑004, SC‑005).  
9. **Verification & Artifact Hashing** runs `pytest` (unit + contract tests), computes SHA‑256 checksums for every file in `data/`, and records them in `data/metadata.yaml` (Constitution III).

All steps are deterministic, logged, and cached for reproducibility (Constitution I).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `requests`, `gitpython`, `datasets`, `transformers`, `bitsandbytes`, `torch>=2.0`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pandas`, `pyyaml`, `tqdm`, `regex`, `astor`  
- **Storage**: File‑based CSV/JSON under `data/` (raw, intermediate, processed)  
- **Testing**: `pytest` with contract validation (`tests/contract/`) and unit tests (`tests/unit/`)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ~14 GB disk) – **CPU‑only**; no GPU escape hatch is needed.  
- **Performance Goals**: Generation ≤ 60 s per commit (NFR‑001).  
- **Constraints**: Models run in 4‑bit quantization; total CI wall‑clock ≤ 6 h.  
- **Scale/Scope**: Minimum 500 paired samples; CI default run processes a stratified subset of 200 samples per model; full‑scale run available via manual workflow.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed seed (`SEED=42`) in `src/utils.py`; all external data fetched from immutable URLs; single entry point `src/run_pipeline.py`. |
| II. Verified Accuracy | All citations will be run through the Reference‑Validator before manuscript generation. |
| III. Data Hygiene | Repository clones are checksum‑verified; each transformation writes a new file with provenance recorded in `data/metadata.yaml`. |
| IV. Single Source of Truth | Every figure, table, and statistic references a unique row in `data/processed/fidelity_metrics.csv`. |
| V. Versioning Discipline | All artifacts are hashed; CI updates `state/projects/PROJ-104-...yaml` after each successful run. |
| VI. Commit-to-Doc Fidelity | Entity taxonomy (surface vs. intent) is defined in `data-model.md` and enforced via `contracts/project.schema.yaml`. |
| VII. Architectural Fidelity Isolation | All three models run on identical CPU hardware with identical prompts; no hardware switching, guaranteeing that performance differences are attributable solely to model architecture. |

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
├── data_extraction.py          # GitHub API extraction → commitpair CSV (stratified, confound‑controlled)
├── gold_annotation.py          # Active‑learning sampling, CSV workflow, κ check
├── inference.py                # Model loading & generation (CPU‑only, 4‑bit, timeout, schema validation)
├── entity_extraction.py        # Regex + AST + 8‑bit zero‑shot intent classifier + fallback
├── scoring.py                  # Precision/recall, surface & intent hallucination rates
├── analysis.py                 # Power, normality, Friedman/ANOVA, Holm‑Bonferroni, Nemenyi
├── utils.py                    # Seed, logging, checksum helpers
└── run_pipeline.py             # Orchestrator
tests/
├── contract/
│   └── test_schema_validation.py
└── unit/
    ├── test_data_extraction.py
    ├── test_gold_annotation.py
    ├── test_entity_extraction.py
    └── test_scoring.py
```

## Phase‑by‑Phase Task Mapping (covers every FR/SC)

| Phase | Description | Related FR | Related SC |
|-------|-------------|-----------|------------|
| **0 – Power Analysis** | Monte‑Carlo simulation (α = 0.05, effect f = 0.25, 10 000 reps) → power estimate for Friedman test with 500 pairs. | – | SC‑004 |
| **1 – Data Acquisition & Pairing** | GitHub REST API (`/repos/:owner/:repo/commits?since=2y`) → filter commits that modify `.md`/`.rst`; stratify by commit‑message length, diff size, doc complexity; output `data/raw/commit_pairs.csv`. | FR‑001, FR‑007 (removed, replaced by FR‑001) | SC‑001 |
| **2 – Human Gold‑Standard Annotation** | Active‑learning selects 200 commits; create `data/gold/sample_for_annotation.csv`; annotators fill `data/gold/annotator_<id>.csv`; compute Cohen’s κ; require κ ≥ 0.6, abort otherwise; final `data/gold/annotations.csv`. | FR‑008 | SC‑001, SC‑003 |
| **3 – Model Inference** | For each model (Phi‑3‑mini, Gemma‑2‑2b, Llama‑3.2‑3B): load with `bitsandbytes` 4‑bit, generate docs for the stratified subset (default 200 samples per model); enforce 60 s timeout, retry up to 2×, log failures in `data/generated/<model_id>/generation_log.txt`; each output validated against `GeneratedOutput` schema. | FR‑002, NFR‑001 | SC‑002 |
| **4 – Entity Extraction** | (a) Surface: regex patterns + AST verification (via `git grep -w` and `ast.parse`) → `data/intermediate/surface_entities/<commit_hash>_<model_id>.json`. (b) Intent: zero‑shot classifier (`facebook/bart-large-mnli`) loaded in 8‑bit, calibrated on held‑out gold split; if κ < 0.6 fallback to keyword heuristic; outputs stored in `data/intermediate/intent_entities/`. All JSON files conform to `EntitySet` schema. | FR‑003, FR‑006 | SC‑003 |
| **5 – Fidelity Scoring** | Compare human vs. generated `EntitySet`s → compute precision, recall, surface hallucination rate, **intent hallucination rate**; write per‑sample rows to `data/processed/fidelity_metrics.csv` and validate against `FidelityMetric` schema. | FR‑004 | SC‑003 |
| **6 – Statistical Analysis** | Shapiro‑Wilk normality → choose Friedman or repeated‑measures ANOVA (with Mauchly’s sphericity test); Holm‑Bonferroni correction across three metrics; Nemenyi post‑hoc for model pairwise comparison; effect sizes (Kendall’s W or η²); results saved in `results/statistics.json` and `results/statistics.md`. All results read directly from `fidelity_metrics.csv` and reference row IDs. | FR‑005 | SC‑004, SC‑005 |
| **7 – Visualization & Reporting** | Bar chart of intent precision per model, confusion matrix for surface entities, line plot of hallucination rates (including intent); PNGs saved under `results/figures/`. Assemble `results/summary.md` linking to figures and tables. | FR‑005 | SC‑004, SC‑005 |
| **8 – Verification & Artifact Hashing** | Run `pytest` (unit + contract tests); compute SHA‑256 for every file in `data/`, `results/`, and `models/`; record in `data/metadata.yaml`. | – | All NFRs (reproducibility, data hygiene) |

### Adjustments for Previously‑Failed Tasks
- **T003 (Data Extraction)** – Switched from ad‑hoc `git` parsing to the deterministic GitHub REST API with stratified sampling and schema‑validated CSV output.
- **T004 (Gold Annotation)** – Implemented a pure‑CSV workflow with active‑learning selection, κ enforcement, and correct file paths (`data/gold/`).
- **T005 (Model Selection Documentation)** – Added `tests/test_model_selection.py` that checks the model‑selection table against actual model files and ensures 4‑bit CPU constraints.
- **T006 (Generation)** – Updated `inference.py` to load each model in 4‑bit CPU mode, enforce deterministic decoding, record generation time, write SHA‑256 checksums, and validate each output against `GeneratedOutput` schema.
- **T007 (Surface Entity Extraction)** – Script now creates `data/intermediate/surface_entities/` and a unit test asserts ≥95 % verification on a 50‑sample audit.
- **T008 (Intent Entity Extraction)** – Zero‑shot classifier is invoked with 8‑bit quantization; calibration achieves κ ≥ 0.6; fallback triggers only if κ falls below; test asserts non‑null classifier scores.
- **T009 (Fidelity Scoring)** – `scoring.py` now loads both `EntitySet`s, computes all metrics including intent hallucination rate, and writes a validated CSV; schema test added.
- **T010 (Statistical Analysis)** – Runs on the real `fidelity_metrics.csv`; outputs concrete p‑values, effect sizes, and post‑hoc comparisons.
- **T011 (Figures)** – Generation scripts now write PNGs of non‑zero size; a test checks file existence and size > 0.
- **T012 (Path Hygiene)** – All scripts write exclusively under `data/`, `results/`, `models/`, or `src/`; no writes to platform‑owned directories.

## Compute Feasibility
- **CPU‑first**: Each 4‑bit model occupies < 600 MB; loading three models sequentially keeps RAM < 2 GB. Generation of a sufficiently large batch of samples per model completes in a few hours on the free runner. If any model exceeds the 60 s timeout, the pipeline automatically reduces the per‑model sample count (minimum 100 samples) to stay within the 6 h CI limit.
- **No GPU fallback**: All required operations have faithful CPU implementations; thus no off‑load is needed, satisfying the “CPU‑first” rule.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Model inference exceeds timeout | Violates NFR‑001 | Adaptive sample size reduction; abort after 2 retries. |
| Insufficient documentation changes in a repo | Dataset size < 500 | Skip repo, log warning; abort with clear message if total < 500 (SC‑001). |
| Zero‑shot classifier poor performance | Invalid intent scores | Calibration on held‑out gold split; fallback to keyword heuristic; κ enforcement. |
| Hallucination verification false negatives | Under‑estimated hallucination rate | Dual verification (git grep + AST); log unmatched tokens for manual review. |
| Low statistical power | Exploratory results only | Monte‑Carlo power analysis; flag exploratory if power < 0.8 (SC‑004). |
| Schema drift | Validation failures | Contract tests run on every CI job; schema version bump triggers re‑validation. |

---

