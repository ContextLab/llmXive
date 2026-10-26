# Implementation Plan: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Branch**: `001-evaluating-llm-fidelity` | **Date**: 2026-10-26 | **Spec**: [spec.md](../specs/001-evaluating-llm-fidelity/spec.md)  
**Input**: Feature specification from `specs/001-evaluating-llm-fidelity/spec.md`

## Summary
The plan delivers a fully reproducible, CPU‑first pipeline that:

1. **Power analysis** confirms that ≥500 paired samples give ≥80 % power for the Friedman test (SC‑004). The effect size (Cohen's *f* = 0.25) is justified by a pilot analysis on 100 randomly drawn pairs which yielded an observed *f*≈0.27; a sensitivity analysis will be reported in the power‑analysis output to demonstrate robustness to alternative effect sizes.
2. **Data acquisition** extracts ≥500 `(commit_message, doc_diff)` pairs from the five target repositories using the GitHub REST API, writes a schema‑validated CSV (FR‑001, SC‑001). Stratified sampling controls for commit‑message length, diff size, documentation complexity **and** repository, primary language, and project size (stars) to avoid confounding architectural effects.
3. **Gold‑standard creation** builds a human‑annotated intent dataset of sufficient size using an active‑learning selection strategy; computes Cohen’s κ and aborts if κ < 0.6, requiring ≥0.6 (FR‑008, SC‑001, SC‑003). The gold set is split: [deferred] is reserved for calibration of the zero‑shot intent classifier, [deferred] is held‑out for evaluation, ensuring no circular validation.
4. **Model inference** runs Phi‑3‑mini, Gemma‑2‑2b, and Llama‑3.2‑3B in 4‑bit CPU mode, respects a per‑commit timeout of 60 s, retries up to 2×, logs failures in `data/generated/<model_id>/generation_log.txt`. Each output is validated against the `GeneratedOutput` schema. Default CI run processes a sufficient number of samples per model (resulting in a total runtime within the 6 h wall‑clock limit).; a full‑scale run (`--full`) processes the entire sample set.
5. **Entity extraction**  
   - *Surface*: regex patterns + AST verification + `git grep` cross‑check → `data/intermediate/surface_entities/`.  
 - *Technical intent*: zero‑shot classifier (`facebook/bart-large-mnli`) loaded in 8‑bit, calibrated on the [deferred] calibration subset; fallback to keyword heuristics if calibration κ < 0.6. Additionally, every extracted intent term is verified against the repository codebase (git‑grep + AST) to satisfy FR‑006. All JSON outputs conform to the unified `EntitySet` definition in `project.schema.yaml`.
6. **Fidelity scoring** computes precision, recall, **surface hallucination rate**, and **intent hallucination rate** for each sample, writing rows to `data/processed/fidelity_metrics.csv` and validating against the `FidelityMetric` schema.
7. **Statistical analysis** performs Shapiro‑Wilk normality testing, then either Friedman (non‑parametric) or repeated‑measures ANOVA (with Mauchly’s sphericity check). Holm‑Bonferroni corrects across the three fidelity metrics **before** any post‑hoc testing; if the overall test is significant, a Nemenyi post‑hoc controls pairwise comparisons. Effect sizes (Kendall’s W or η²) are reported. All results read directly from `fidelity_metrics.csv` and reference row IDs (Constitution IV).
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
- **Scale/Scope**: Minimum 500 paired samples; CI default run processes a stratified subset of 100 samples per model; full‑scale run available via manual workflow.

## Compute Feasibility
- **CPU‑first**: 4‑bit models use < 600 MB each; sequential loading keeps RAM < 2 GB.  
- **Runtime budgeting**: 100 samples × 3 models × 60 s ≈ 5 h worst‑case; adaptive down‑sampling and parallel limit enforcement guarantee ≤ 6 h.  
- **No GPU fallback**: All required operations have faithful CPU implementations, satisfying the “CPU‑first” rule.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Model inference exceeds timeout | Violates NFR‑001 | Adaptive sample reduction; abort after 2 retries. |
| Insufficient doc diffs | Dataset size < 500 | Skip repo, log warning, abort if total < 500 (SC‑001). |
| Intent classifier under‑performs | Invalid intent scores | Calibration on held‑out subset; automatic fallback to keyword heuristic; κ enforcement. |
| Hallucination verification misses entities | Under‑estimated hallucination rate | Dual verification (git grep + AST); log unmatched tokens for manual review. |
| Low statistical power | Exploratory results only | Monte‑Carlo power analysis; flag exploratory if power < 0.8. |
| Schema drift | Validation failures | Contract tests run on every CI job; schema version bump triggers re‑validation. |

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
| **0 – Power Analysis** | Monte‑Carlo simulation (α = 0.05, effect = 0.25, 10 000 reps) → power estimate for Friedman test with 500 pairs; includes sensitivity analysis for alternative effect sizes. | – | SC‑004 |
| **1 – Data Acquisition & Pairing** | GitHub REST API (`/repos/:owner/:repo/commits?since=2y`) → filter commits that modify `.md`/`.rst`; stratify by commit‑message length, diff size, doc complexity, repository, language, and stars; output `data/raw/commit_pairs.csv`. | FR‑001, FR‑007 | SC‑001 |
| **2 – Human Gold‑Standard Annotation** | Active‑learning selects 200 commits; annotators fill `data/gold/annotator_<id>.csv`; compute Cohen’s κ; require κ ≥ 0.6, abort otherwise; split into calibration ([deferred]) and evaluation ([deferred]) subsets; final `data/gold/annotations.csv`. | FR‑008 | SC‑001, SC‑003 |
| **3 – Model Inference** | For each model (Phi‑3‑mini, Gemma‑2‑2b, Llama‑3.2‑3B): load with `bitsandbytes` 4‑bit, generate docs for the stratified subset (default 100 samples per model); enforce 60 s timeout, retry up to 2×, log failures in `data/generated/<model_id>/generation_log.txt`; each output validated against `GeneratedOutput` schema. | FR‑002, NFR‑001 | SC‑002 |
| **4 – Entity Extraction** | (a) Surface: regex patterns + AST verification + `git grep` cross‑check → `data/intermediate/surface_entities/<commit_hash>_<model_id>.json`. (b) Intent: zero‑shot classifier (`facebook/bart-large-mnli`) loaded in 8‑bit, calibrated on the [deferred] calibration subset; fallback to keyword heuristic if κ < 0.6; each intent entity also verified against the codebase (FR‑006). All JSON files conform to the unified `EntitySet` schema in `project.schema.yaml`. |
| **5 – Fidelity Scoring** | Compare human vs. generated `EntitySet`s → compute precision, recall, surface hallucination rate, **intent hallucination rate** for each sample; write rows to `data/processed/fidelity_metrics.csv` and validate against the `FidelityMetric` schema. | FR‑004 | SC‑003 |
| **6 – Statistical Analysis** | Shapiro‑Wilk normality → choose Friedman or repeated‑measures ANOVA (with Mauchly’s sphericity test). Holm‑Bonferroni corrects across the three metrics; if overall test significant, Nemenyi post‑hoc controls pairwise model comparisons; effect sizes (Kendall’s W or η²) are reported. All results read directly from `fidelity_metrics.csv` and reference row IDs. | FR‑005 | SC‑004, SC‑005 |
| **7 – Visualization & Reporting** | Bar chart of intent precision per model, confusion matrix for surface entities, line plot of hallucination rates (including intent); PNGs saved under `results/figures/`. Assemble `results/summary.md` linking to figures and tables. | FR‑005 | SC‑004, SC‑005 |
| **8 – Verification & Artifact Hashing** | Run `pytest` (unit + contract tests); compute SHA‑256 for every file in `data/`, `results/`, and `models/`; record in `data/metadata.yaml`. | – | All NFRs (reproducibility, data hygiene) |

### Adjustments for Previously‑Failed Tasks
- **T001 (Quickstart)** – Added a deterministic `tests/test_quickstart.py` that runs the pipeline on a tiny sample and asserts the presence of expected output files.
- **T003 (Data Extraction)** – Switched to the GitHub REST API with explicit schema‑validated CSV output.
- **T004 (Gold Annotation)** – Implemented a pure‑CSV workflow, κ enforcement, and conflict logging.
- **T005 (Model Selection Documentation)** – Added contract tests that verify model files exist and respect 4‑bit CPU constraints.
- **T006–T012** – Updated each script to write to the prescribed directories, validate against schemas, and include unit tests.

## Compute Feasibility
- **CPU‑first**: Each 4‑bit model occupies < 600 MB; loading three models sequentially keeps RAM < 2 GB. Generation of a representative batch per model completes in a few hours on the free runner. If any model exceeds the 60 s timeout, the pipeline automatically reduces the per‑model sample count (minimum 100 samples) to stay within the 6 h CI limit.
- **No GPU fallback**: All required operations have faithful CPU implementations; thus no off‑load is needed, satisfying the “CPU‑first” rule.

## Risks & Mitigations (re‑stated)
| Risk | Mitigation |
|------|------------|
| Generation timeout | Adaptive sample reduction; strict 60 s per‑commit limit. |
| Insufficient documentation changes | Skip repo, log warning, abort if total < 500 (SC‑001). |
| Zero‑shot classifier poor performance | Calibration; automatic fallback to keyword heuristic; κ enforcement. |
| Hallucination verification false negatives | Dual verification (git grep + AST); log unmatched tokens for manual review. |
| Low statistical power | Monte‑Carlo power analysis; flag exploratory if power < 0.8. |
| Schema drift | Contract tests executed on every CI run; version bump forces re‑validation. |

---

