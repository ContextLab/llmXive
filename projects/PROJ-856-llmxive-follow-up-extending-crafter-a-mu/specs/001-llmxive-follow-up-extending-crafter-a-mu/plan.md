# Implementation Plan: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

**Branch**: `001-llmxive-cognitive-load` | **Date**: 2026-10-24 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-cognitive-load/spec.md`

## Summary
Create a fully reproducible pipeline that (1) **attempts** to download a static subset of 50 failed figure generations from CrafterBench (if a verified open‑source URL exists); if no verified URL is available the pipeline **aborts** with a clear error, (2) deploys two editing interfaces (Structured Harness and Natural‑Language Chat) with **within‑subjects counterbalanced ordering** and a **10‑minute wash‑out interval**, (3) logs every interaction with millisecond precision and records NASA‑TLX scores, (4) validates each corrected figure via **exact vector match** (primary success) and records a **CLIP ViT‑B/32 semantic similarity** score (secondary validation), (5) conducts paired statistical tests on **all trials** (censoring aborted tasks) and includes a covariate for expertise, and (6) generates a complete markdown report. All steps run on the GitHub Actions free‑tier CPU runner; the CLIP model runs on CPU. A **Reference‑Validation** step ensures all citations satisfy Constitution Principle II.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==1.26.*`  
  - `scipy==1.13.*`  
  - `opencv-python==4.9.*`  
  - `torch==2.3.*` (CPU‑only)  
  - `torchvision==0.18.*` (for CLIP ViT‑B/32)  
  - `ftfy==6.1.*`  
  - `transformers==4.41.*`  
  - `fastapi==0.111.*`  
  - `uvicorn==0.30.*`  
  - `jsonschema==4.22.*`  
  - `statsmodels==0.14.*` (power analysis & mixed‑effects)  
  - `pytest==8.2.*`  
- **Storage**: `data/` (figures, ground‑truth vectors, logs, validation records).  
- **Testing**: `pytest -q tests/contract` validates JSON‑Lines files against schemas in `contracts/`.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: End‑to‑end ≤ 6 h wall‑clock, ≤ 7 GB RAM, ≤ 2 CPU cores.  
- **Constraints**: Must satisfy all Constitution Principles I‑VII; no external credentials; deterministic seeds (`seed=42`).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed seeds, version‑pinned dependencies, deterministic synthetic data generation **only** when a verified dataset is unavailable, single orchestrator `run_pipeline.py`. |
| II. Verified Accuracy | Added **Phase 12 – Reference Validation** that runs the Reference‑Validator Agent on every citation before final report. |
| III. Data Hygiene | `data/checksums.txt` records SHA‑256 for every generated file; transformations write new files with provenance metadata. |
| IV. Single Source of Truth | All quantitative values derive from immutable JSON‑Lines logs; report references those logs directly. |
| V. Versioning Discipline | All artifacts are version‑controlled; CI computes content hashes stored in `state/projects/...yaml`. |
| VI. Human‑Subject Interaction Logging | `interaction_logger.py` writes immutable raw logs; schema enforced by `contracts/interaction_log.schema.yaml`. |
| VII. Ground‑Truth Validation Protocol | `run_validation.py` performs **exact vector comparison** (primary success) **and** records CLIP semantic similarity (secondary). Primary success is required for inclusion in the primary analysis; secondary score is reported separately. |

## Project Structure
### Documentation
```
specs/001-llmxive-cognitive-load/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── interaction_log.schema.yaml
    ├── semantic_validation.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code
```
src/
├── curators/
│   └── curate_failed_figures.py          # Attempts to download a **verified** CrafterBench subset of exactly 50 failed figures. If no verified URL exists, the script aborts with an informative error.
├── interfaces/
│   ├── structured_harness.py             # FastAPI endpoint /edit (typed commands)
│   ├── chat_interface.py                 # FastAPI endpoint /edit (natural language)
│   └── session.py                        # /init_session returns counterbalanced order, inserts **10‑minute wash‑out**, randomizes task order per participant
├── logger/
│   └── interaction_logger.py             # JSONL writer with ms timestamps, iteration count, NASA‑TLX score
├── validation/
│   ├── vector_match.py                   # Exact JSON vector equality
│   ├── semantic_similarity.py            # CLIP ViT‑B/32 feature extraction + cosine similarity
│   └── run_validation.py                 # Orchestrates both checks, writes SemanticValidation records (primary_success = vector_match)
├── analysis/
│   ├── wilcoxon_analysis.py              # Paired Wilcoxon (or paired t‑test if normal) on **all trials**; aborted tasks are **right‑censored** at 15 min; includes mixed‑effects model with expertise covariate; excludes only truly missing data.
│   └── retention_check.py                # Enforces ≥ 28 valid sessions out of ≥ 32 recruited participants (SC‑004)
├── simulation/
│   ├── power_analysis.py                 # α = 0.025, effect size d≈0.5 → required N is of a modest magnitude (e.g., on the order of tens).
│   ├── simulate_participants.py          # Generates deterministic synthetic logs for CI verification
│   └── human_data_collection.py          # Stub for ingesting real participant logs (future use)
├── utils/
│   ├── seeds.py                          # Central seed management
│   └── checksums.py                      # SHA‑256 helper
└── run_pipeline.py                       # Orchestrates steps 0‑13 in order
```

## Phase‑by‑Phase Task Breakdown (covers all FR/SC)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0 – Environment Setup** | Create `requirements.txt`, pin `seed=42`, add checksum utilities. | I, III, V |
| **1 – Data Curation** | `curate_failed_figures.py` **attempts** to download a **verified** CrafterBench subset of exactly 50 failed figures. **If no verified URL exists, the script aborts with an informative error**; this highlights the current limitation of FR‑001. | FR‑001, SC‑004 |
| **2 – Interface Provisioning** | `session.py` implements `/init_session` with **counterbalanced order**, inserts a **10‑minute wash‑out interval**, and **randomizes task order** per participant (seed = 42 + participant ID). `structured_harness.py` and `chat_interface.py` expose `/edit` endpoints (FastAPI). 200 OK responses are verified via CI. | FR‑002, VI, methodology‑1fee2458 |
| **3 – Logging Instrumentation** | `interaction_logger.py` writes a JSONL line per edit with millisecond timestamps, iteration number, payload, **and NASA‑TLX score** (`subjective_load`). Timestamps reflect real wall‑clock time for human participants; synthetic runs generate deterministic timestamps. | FR‑003, VI, methodology‑bd2bfc9f |
| **4 – Power Analysis** | `power_analysis.py` uses `statsmodels.stats.power.WilcoxonPower` (Monte‑Carlo fallback) with **α = 0.025** (Bonferroni‑adjusted) and effect size d ≈ 0.5 to compute required N (≈ 33). The pipeline aborts if the planned N < required, guaranteeing target power. | FR‑009, SC‑004 |
| **5 – Success Validation** | `run_validation.py` runs `vector_match.py` (**primary success**) **and** `semantic_similarity.py` (records similarity score; **semantic_pass** = score ≥ 0.95). **Overall_success is defined **solely** by the vector‑match result**; the semantic_pass field is stored as a secondary metric and does **not** affect inclusion in the primary analysis. | FR‑004, FR‑005, VII |
| **6 – CI‑Only Pipeline Verification** | `simulate_participants.py` creates a set of synthetic sessions, each with a representative number of tasks, using deterministic timestamps and random edits. Logs are validated against `interaction_log.schema.yaml`. These logs prove that the pipeline runs and conforms to schemas; they are **not** used for scientific inference. | SC‑004 (verification) |
| **7 – Retention & Validity Checks (Synthetic)** | `retention_check.py` ensures **≥ 25** of 30 synthetic sessions have at least one successful trial. Aborted tasks are **right‑censored** at 15 min. | SC‑004 |
| **8 – Statistical Analysis** | `wilcoxon_analysis.py` reads validated `SemanticValidation` records, computes per‑participant `time_to_success_ms` (or censored at 15 min), `iteration_count`, and `subjective_load`. It runs paired Wilcoxon signed‑rank tests (`scipy.stats.wilcoxon`) for each metric, applies Bonferroni correction (α = 0.025 per metric), calculates rank‑siserial effect size *r*, bootstraps a 95 % CI (1 000 resamples), and **fits an exploratory linear mixed‑effects model** (`statsmodels`) with `expertise_level` as a fixed effect. **Aborted tasks are included as right‑censored observations**, eliminating asymmetric bias. Outputs `outputs/analysis_results.jsonl` conforming to `analysis_result.schema.yaml`. | FR‑006, SC‑001, SC‑002, SC‑003, methodology‑c565edb0 |
| **9 – Real‑World Retention Check** | After human data collection, `retention_check.py` verifies that **≥ 28** of the recruited **≥ 32** participants have completed both interface blocks with at least one primary‑success trial each (SC‑004). If the criterion is not met, the pipeline aborts and flags a redesign. | SC‑004, FR‑009 |
| **10 – Report Generation** | `generate_report.py` consumes `analysis_results.jsonl` and produces `outputs/report.md` with mean/median tables, p‑values, effect sizes, confidence intervals, **average NASA‑TLX scores per interface**, and a breakdown of success‑rate (vector vs. semantic). | FR‑007, SC‑005 |
| **11 – Contract Validation** | `pytest -q tests/contract` validates all JSON‑Lines files against the three schemas. | All FR/SC (ensures deterministic, verifiable artifacts) |
| **12 – Reference Validation** | Runs the Reference‑Validator Agent on all citations (CLIP ViT‑B/32, Smith 2022, etc.) and aborts if any citation fails verification, satisfying Constitution Principle II. | II |
| **13 – Full Pipeline** | `python -m src.run_pipeline --config config.yaml` runs all phases in order. | End‑to‑end reproducibility |

### Coverage Matrix
| FR / SC | Mapped Phase(s) |
|---------|-----------------|
| FR‑001 | Phase 1 (currently aborts if no verified source; pending dataset provision) |
| FR‑002 | Phase 2 |
| FR‑003 | Phase 3 |
| FR‑004 | Phase 5 |
| FR‑005 | Phase 5 |
| FR‑006 | Phase 8 |
| FR‑007 | Phase 10 |
| FR‑008 | Phase 3 (NASA‑TLX captured in InteractionLog) |
| FR‑009 | Phase 4 |
| FR‑010 | Phase 2 (10‑minute wash‑out) |
| FR‑011 | Phase 8 (aborted tasks censored, not excluded) |
| FR‑012 | Phase 8 (covariate in mixed‑effects) |
| SC‑001 | Phase 8 |
| SC‑002 | Phase 8 |
| SC‑003 | Phase 5 & Phase 8 |
| SC‑004 | Phase 4, Phase 6, Phase 7, Phase 9 |
| SC‑005 | Phase 10 (runtime ≤ 6 h) |
| SC‑006 | Phase 8 (NASA‑TLX) |
| SC‑007 | Phase 4 (power analysis) |

---


## projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/specs/001-llmxive-follow-up-extending-crafter-a-mu/research.md

# Research: llmXive follow‑up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

## Objective
Evaluate whether a **structured typed‑edit harness** reduces **objective latency** (`time‑to‑success`), **iteration count**, and **subjective cognitive load** (NASA‑TLX) relative to a **natural‑language chat interface** when participants correct localized errors in scientific figures, while controlling for participant expertise.

## Dataset Strategy
| Need | Availability | Action |
|------|--------------|--------|
| Failed figure generations with ground‑truth layout vectors (≈ 50 items) | **CrafterBench** – *NO verified open source URL* (see verified datasets block). | **Currently unavailable as a verified open‑source download.** `curate_failed_figures.py` will **abort** if a download is attempted without a verified URL, highlighting the need for an open dataset to satisfy FR‑001. Once such a source is provided, the same script will ingest it without modification. |
| Pre‑trained visual similarity model | CLIP ViT‑B/32 (available via `torchvision` / `transformers`) – CPU‑only weights auto‑downloaded from HuggingFace. | Load on CPU; weights cached locally. |
| Human participant logs | Not needed for CI; will be collected in the field study. | `human_data_collection.py` (stub) will ingest real logs when available. |
| NASA‑TLX questionnaire | Publicly described in the NASA‑TLX literature. | Integrated into UI; scores (0‑100) stored per task. |
| Participant expertise questionnaire | Self‑report (0‑5 Likert). | Collected at session start; stored as `expertise_level` in `ParticipantSession`. |

## Methodology
1. **Within‑Subjects Counterbalanced Design**  
   - Each **real** participant completes the same 50 tasks.  
   - Interface order is **randomized** (seed = 42 + participant ID) **and fully counterbalanced** across participants.  
   - A **10‑minute wash‑out interval** separates the two interface blocks to mitigate carry‑over learning (FR‑010).  
   - **Task order** is shuffled per participant (seed = 42 + participant ID) to further reduce practice effects.  

2. **A‑Prior Power Analysis**  
   - `power_analysis.py` computes the minimum N for a paired Wilcoxon test with **α = 0.025** (Bonferroni‑adjusted) and effect size *d* ≈ 0.5.  
   - Required N is approximately a moderate sample size (on the order of dozens). The pipeline aborts if the planned N < required, ensuring the target power = 0.80 (FR‑009).  

3. **Instrumentation (Construct Validity)**  
   - Every edit triggers `interaction_logger.py`, which writes a JSONL line with millisecond timestamps, iteration number, payload, **and NASA‑TLX score** (`subjective_load`).  
   - For **real** participants, timestamps reflect actual wall‑clock time → valid measure of cognitive load.  
   - For **synthetic** verification, deterministic timestamps are generated (seeded) to ensure reproducibility.  

4. **Success Definition**  
   - **Primary success** = **exact vector match** (`vector_match.py`).  
   - **Secondary validation** = CLIP ViT‑B/32 cosine similarity **≥ 0.95** (`semantic_pass`).  
   - The primary success flag (`overall_success`) mirrors the vector‑match result only; the `semantic_pass` field records whether the CLIP similarity meets the 0.95 threshold but **does not** affect inclusion in the primary analysis.  

5. **Statistical Testing**  
   - **All trials** are included. For trials that reach the 15‑minute timeout without primary success, the observed time is treated as a **right‑censored** value at 15 min (to avoid asymmetric bias).  
   - Paired Wilcoxon signed‑rank test (`scipy.stats.wilcoxon`) on per‑participant differences for `time_to_success_ms`, `iteration_count`, and `subjective_load`.  
   - **Bonferroni correction** for the three metrics (α = 0.025 each).  
   - Effect size *r* = Z / √N; 95 % CI for the median difference via bootstrap (1 000 resamples).  
   - **Exploratory covariate analysis**: Linear mixed‑effects model includes `expertise_level` as a fixed effect (FR‑012).  

6. **Retention & Completion Checks**  
   - After real data collection, `retention_check.py` verifies that **≥ 28** of the recruited **≥ 32** participants have completed both interface blocks with at least one primary‑success trial each (SC‑004).  
   - If the criterion is not met, the pipeline aborts and flags a redesign.  

7. **Edge‑Case Handling**  
   - **Timeout** → logged as `"aborted"`; time recorded as censored at 15 min and included in analysis as a right‑censored observation.  
   - **Corrupted ground‑truth** → task skipped; N adjusted accordingly.  
   - **Semantic score 0.94–0.95** → flagged for manual review; does **not** affect primary success status.  

## Decision / Rationale
| Component | CPU‑first or GPU‑escape? | Reason |
|-----------|--------------------------|--------|
| Synthetic data generation | **CPU‑first** (NumPy, Pandas) | Minimal resource usage; fallback when real data unavailable. |
| CLIP ViT‑B/32 semantic similarity | **CPU‑first** (torch CPU backend) | Model size (~300 MB) fits comfortably on the runner. |
| Statistical analysis | **CPU‑first** (SciPy, Statsmodels) | Pure CPU libraries. |
| Full pipeline (CI verification) | **CPU‑first** | Entire pipeline stays within runtime and memory budget. |
| Real‑world similarity model (if larger model later) | **GPU‑escape** (Kaggle) – not required now. | Placeholder for future scaling. |

## Expected Deliverables
- `data/figures/` and `data/ground_truth/` (will contain the real CrafterBench subset once a verified open source becomes available).  
- `data/logs/` (raw interaction logs, JSONL, schema‑validated, including `subjective_load`).  
- `data/validation/` (SemanticValidation records).  
- `outputs/analysis_results.jsonl` (three `AnalysisResult` objects: time_to_success_ms, iteration_count, subjective_load).  
- `outputs/report.md` (statistical summary, tables, confidence intervals, **average NASA‑TLX scores**, success‑rate breakdown).  
- Contract schemas in `contracts/`.  
- End‑to‑end pipeline executable via:  
  ```bash
  python -m src.run_pipeline --config config.yaml
  ```

---

