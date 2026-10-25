# Implementation Plan: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

**Branch**: `001-llmxive-cognitive-load` | **Date**: 2026-10-25 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-cognitive-load/spec.md`

## Summary
Create a reproducible pipeline that (1) attempts to download a **verified** subset of 50 failed figures from the HuggingFace dataset `crafterbench-failed` (aborts with a clear error if no open‑source URL exists), (2) provides two editable interfaces (Structured Harness and Natural‑Language Chat) with a fully **counter‑balanced** within‑subjects design and a **minimum 5‑minute wash‑out** (FR‑010), (3) logs every interaction with millisecond precision plus NASA‑TLX scores, (4) validates corrections via exact vector match (primary) and CLIP ViT‑B/32 semantic similarity (secondary), (5) runs a paired **Wilcoxon signed‑rank test** (or paired t‑test if normality holds) on latency, iteration count, NASA‑TLX, and semantic success rate with **Bonferroni‑adjusted α = 0.025 per test** (four metrics), and (6) generates a markdown report. All steps run on the GitHub Actions free‑tier CPU runner; the CLIP model runs on CPU.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==1.26.*`  
  - `scipy==1.13.*`  
  - `opencv-python==4.9.*`  
  - `torch==2.3.*` (CPU‑only)  
  - `torchvision==0.18.*` (CLIP weights)  
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
| I. Reproducibility | Fixed seeds, version‑pinned dependencies, deterministic synthetic fallback if no open dataset is available, single orchestrator `run_pipeline.py`. |
| II. Verified Accuracy | Phase 12 runs the Reference‑Validator Agent on every citation before the final report. |
| III. Data Hygiene | `data/checksums.txt` records SHA‑256 for every generated file; transformations write new files with provenance metadata. |
| IV. Single Source of Truth | All quantitative values derive from immutable JSON‑Lines logs; report references those logs directly. |
| V. Versioning Discipline | All artifacts are version‑controlled; CI computes content hashes stored in `state/projects/...yaml`. |
| VI. Human‑Subject Interaction Logging | `interaction_logger.py` writes immutable raw logs; schema enforced by `contracts/interaction_log.schema.yaml`. |
| VII. Ground‑Truth Validation Protocol | `run_validation.py` performs **exact vector comparison** (primary success) **and** records CLIP semantic similarity (secondary). Primary success is required for inclusion in the primary analysis. |

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
│   └── curate_failed_figures.py          # Downloads verified CrafterBench subset; aborts if no open URL.
├── interfaces/
│   ├── structured_harness.py             # FastAPI /edit endpoint (typed commands)
│   ├── chat_interface.py                 # FastAPI /edit endpoint (NL chat)
│   └── session.py                        # /init_session returns **counterbalanced** order, inserts 5‑min wash‑out, randomizes task order.
├── logger/
│   └── interaction_logger.py             # JSONL writer with ms timestamps, iteration count, NASA‑TLX.
├── validation/
│   ├── vector_match.py                   # Exact JSON vector equality
│   ├── semantic_similarity.py            # CLIP ViT‑B/32 cosine similarity
│   └── run_validation.py                 # Orchestrates both checks, writes SemanticValidation records.
├── analysis/
│   ├── wilcoxon_analysis.py              # Paired Wilcoxon (or paired t) on latency, iterations, NASA‑TLX, semantic success; **excludes aborted tasks**; includes `test_used` field; reports effect size *r* and 95 % CI; also fits a linear mixed‑effects model with expertise covariate.
│   └── retention_check.py                # Enforces ≥ 28 of ≥ 32 participants have valid completed sessions.
├── simulation/
│   ├── power_analysis.py                 # Computes required N for mixed‑effects model with expertise covariate (α = 0.025, d≈0.5, power = 0.80) → ≈ 40 participants; aborts if planned N < required.
│   ├── simulate_participants.py          # Generates deterministic synthetic logs for CI verification.
│   └── human_data_collection.py          # Stub for ingesting real participant logs.
├── utils/
│   ├── seeds.py                          # Central seed management
│   └── checksums.py                      # SHA‑256 helper
└── run_pipeline.py                       # Orchestrates phases 0‑13 in order
```

## Phase‑by‑Phase Task Breakdown (covers all FR/SC)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0 – Environment Setup** | Create `requirements.txt`, pin `seed=42`, add checksum utilities. | I, III, V |
| **1 – Data Curation** | `curate_failed_figures.py` attempts to download a **verified** HuggingFace dataset `crafterbench-failed` containing exactly 50 failed figures. **If no verified open‑source URL exists, the script aborts with an informative error**, signalling that FR‑001 cannot be satisfied until such a dataset is supplied. | FR‑001 (conditional), SC‑004 |
| **2 – Interface Provisioning** | `session.py` implements `/init_session` with **strict counterbalancing**: participants are split as evenly as possible so that the number receiving the Structured harness first equals the number receiving Chat first. Inserts a **5‑minute wash‑out** (FR‑010) and randomizes task order per participant (seed = 42 + participant ID). | FR‑002, VI, methodology-e4287d02, methodology-45a9f363 |
| **3 – Logging Instrumentation** | `interaction_logger.py` writes a JSONL line per edit with millisecond timestamps, iteration number, payload, **and NASA‑TLX score** (`subjective_load`). | FR‑003, VI |
| **4 – Power Analysis** | `power_analysis.py` uses `statsmodels.stats.power` to compute the minimum N for a **mixed‑effects model** with expertise as a covariate, using **α = 0.025** (Bonferroni‑adjusted) and effect size ≈ moderate (e.g., a medium‑sized effect). Required N ≈ a sufficient number of participants to achieve adequate statistical power.; pipeline aborts if the planned N < required, ensuring target power = 0.80 (FR‑009). | FR‑009, SC‑004, methodology-ac73074a |
| **5 – Success Validation** | `run_validation.py` runs `vector_match.py` (**primary success**) **and** `semantic_similarity.py` (records similarity; **semantic_pass** = score ≥ 0.95). `overall_success` mirrors the vector‑match result only; `semantic_pass` is stored separately and does **not** affect inclusion in the primary analysis. | FR‑004, FR‑005, VII |
| **6 – CI‑Only Synthetic Verification** | `simulate_participants.py` creates deterministic synthetic sessions (with a representative set of participants) with timestamps and edits, validated against `interaction_log.schema.yaml`. | SC‑004 (verification) |
| **7 – Retention & Validity Checks (Synthetic)** | `retention_check.py` ensures **≥ 25** of 30 synthetic sessions have at least one primary‑success trial; aborted tasks are **excluded** from latency/iteration calculations. | SC‑004 |
| **8 – Statistical Analysis** | `wilcoxon_analysis.py` reads validated `SemanticValidation` records, computes per‑participant `time_to_success_ms`, `iteration_count`, `subjective_load`, and **semantic_success_rate**. Runs **paired Wilcoxon signed‑rank tests** (`scipy.stats.wilcoxon`) for each metric, **excluding aborted tasks**. Applies **Bonferroni correction for four metrics** (α = 0.025 each). Calculates rank‑biserial effect size *r*, bootstraps confidence intervals (using a large number of resamples), and fits a **linear mixed‑effects model** (`statsmodels`) with `expertise_level` as a fixed effect. Each output record **includes the required `test_used` field** (`"wilcoxon"` or `"paired_t"`). Outputs `outputs/analysis_results.jsonl` conforming to `analysis_result.schema.yaml`. | FR‑006, SC‑001, SC‑002, SC‑003, SC‑006, methodology-6f800d9e, methodology-66949b10, plan_consistency-9077edd4, scientific_soundness-76896dac |
| **9 – Real‑World Retention Check** | `retention_check.py` verifies **≥ 28** of the recruited **≥ 32** participants have completed both interface blocks with at least one primary‑success trial each (SC‑004). If not, the pipeline aborts and flags a redesign. | SC‑004, FR‑009 |
| **10 – Report Generation** | `generate_report.py` consumes `analysis_results.jsonl` and produces `outputs/report.md` with mean/median tables, p‑values, effect sizes, 95 % CIs, **average NASA‑TLX scores**, and a breakdown of success‑rate (vector vs. semantic). | FR‑007, SC‑005 |
| **11 – Contract Validation** | `pytest -q tests/contract` validates all JSON‑Lines files against the three schemas, guaranteeing deterministic, verifiable artifacts. | All FR/SC |
| **12 – Reference Validation** | Runs the Reference‑Validator Agent on all citations (CLIP paper, Smith 2022, etc.) and aborts if any citation fails verification, satisfying Constitution Principle II. | II |
| **13 – Full Pipeline Execution** | `python -m src.run_pipeline --config config.yaml` runs all phases in order, delivering a reproducible end‑to‑end result. | End‑to‑end reproducibility |

### Coverage Matrix
| FR / SC | Mapped Phase(s) |
|---------|-----------------|
| FR‑001 | Phase 1 (conditional abort if no verified source) |
| FR‑002 | Phase 2 |
| FR‑003 | Phase 3 |
| FR‑004 | Phase 5 |
| FR‑005 | Phase 5 |
| FR‑006 | Phase 8 |
| FR‑007 | Phase 10 |
| FR‑008 | Phase 3 (NASA‑TLX captured) |
| FR‑009 | Phase 4 |
| FR‑010 | Phase 2 (5‑minute wash‑out) |
| FR‑011 | Phase 8 (excludes aborted tasks) |
| FR‑012 | Phase 8 (expertise covariate) |
| SC‑001 | Phase 8 |
| SC‑002 | Phase 8 |
| SC‑003 | Phase 5 & Phase 8 |
| SC‑004 | Phase 4, Phase 6, Phase 7, Phase 9 |
| SC‑005 | Phase 10 (runtime ≤ 6 h) |
| SC‑006 | Phase 8 (NASA‑TLX) |
| SC‑007 | Phase 4 (power analysis for mixed‑effects) |

---



## projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/specs/001-llmxive-follow-up-extending-crafter-a-mu/research.md
# Research: llmXive follow‑up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

## Objective
Evaluate whether a **structured typed‑edit harness** reduces **objective latency** (`time‑to‑success`), **iteration count**, and **subjective cognitive load** (NASA‑TLX) relative to a **natural‑language chat interface** when participants correct localized errors in scientific figures, while controlling for participant expertise.

## Dataset Strategy
| Need | Availability | Action |
|------|--------------|--------|
| Failed figure generations with ground‑truth layout vectors (≈ 50 items) | **CrafterBench** – *NO verified open‑source URL* (see verified datasets block). | The curation script (`curate_failed_figures.py`) will **abort** if no verified source is provided. **Specification must be updated** to supply an open, programmatically downloadable subset (or an alternative dataset) before the study can proceed (FR‑001). |
| Pre‑trained visual similarity model | CLIP ViT‑B (available via `torchvision` / `transformers`) – CPU‑only weights auto‑downloaded from HuggingFace. | Load on CPU; weights cached locally. |
| Human participant logs | Not needed for CI; will be collected in the field study. | `human_data_collection.py` (stub) will ingest real logs when available. |
| NASA‑TLX questionnaire | Publicly described in NASA‑TLX literature. | Integrated into UI; scores (0‑100) stored per task. |
| Participant expertise questionnaire | Self‑report (0‑5 Likert). | Collected at session start; stored as `expertise_level` in `ParticipantSession`. |

## Methodology
1. **Within‑Subjects Counterbalanced Design**  
   - Each **real** participant completes the same 50 tasks.  
   - Interface order is **randomized** (seed = 42 + participant ID) **and fully counterbalanced**: half of participants receive the Structured harness first, half receive Chat first, guaranteeing equal numbers for each first‑interface condition.  
   - A **5‑minute wash‑out interval** separates the two interface blocks (FR‑010).  
   - Task order is shuffled per participant (seed = 42 + participant ID).  

2. **A‑Prior Power Analysis**  
   - `power_analysis.py` computes the minimum N for a **mixed‑effects model** with expertise as a covariate, using **α = 0.025** (Bonferroni‑adjusted) and effect size ≈ 0.5.  
   - Required N ≈ 40 participants; the pipeline aborts if the planned N < required, ensuring target power = 0.80 (FR‑009).  

3. **Instrumentation (Construct Validity)**  
   - Every edit triggers `interaction_logger.py`, writing a JSONL line with millisecond timestamps, iteration number, payload, **and NASA‑TLX score** (`subjective_load`).  
   - For **real** participants, timestamps reflect actual wall‑clock time.  
   - For **synthetic** CI verification, deterministic timestamps are generated (seeded) to guarantee reproducibility.  

4. **Success Definition**  
   - **Primary success** = **exact vector match** (`vector_match.py`).  
   - **Secondary validation** = CLIP ViT‑B/32 cosine similarity **≥ 0.95** (`semantic_similarity.py`).  
   - `overall_success` mirrors the vector‑match result only; `semantic_pass` is recorded separately and does **not** affect inclusion in the primary analysis.  

5. **Statistical Testing**  
   - Paired Wilcoxon signed‑rank test (`scipy.stats.wilcoxon`) on per‑participant differences for `time_to_success_ms`, `iteration_count`, `subjective_load`, and **semantic_success_rate**.  
   - **Bonferroni correction for four metrics** (α = 0.025 per test).  
   - Effect size *r* = Z / √N; 95 % CI for the median difference via bootstrap (1 000 resamples).  
   - **Exploratory covariate analysis**: Linear mixed‑effects model includes `expertise_level` as a fixed effect (FR‑012).  

6. **Retention & Validity Checks**  
   - `retention_check.py` ensures **≥ 28** of the recruited **≥ 32** participants have completed both interface blocks with at least one primary‑success trial each (SC‑004).  
   - If the criterion is not met, the pipeline aborts and flags a redesign.  

7. **Edge‑Case Handling**  
   - **Timeout** (> 15 min) → logged as `"aborted"`; **aborted tasks are excluded** from latency and iteration analyses (FR‑011).  
   - **Corrupted ground‑truth** → task skipped; N adjusted accordingly.  
   - **Semantic score 0.94–0.95** → flagged for manual review; does **not** affect primary success status.  

## Decision / Rationale
| Component | CPU‑first or GPU‑escape? | Reason |
|-----------|--------------------------|--------|
| Synthetic data generation | **CPU‑first** (NumPy, Pandas) | Minimal resource usage; suitable for CI verification. |
| CLIP ViT‑B/32 semantic similarity | **CPU‑first** (torch CPU backend) | Model size (~300 MB) fits comfortably on the runner. |
| Statistical analysis | **CPU‑first** (SciPy, Statsmodels) | Pure CPU libraries. |
| Full pipeline (CI verification) | **CPU‑first** | Entire pipeline stays within runtime and memory budget. |
| Real‑world similarity model (if larger later) | **GPU‑escape** (Kaggle) – not required now. | Placeholder for future scaling. |

## Expected Deliverables
- `data/figures/` and `data/ground_truth/` (synthetic surrogate now; real subset to replace when a verified open source is supplied).  
- `data/logs/` (raw interaction logs, JSONL, schema‑validated, including `subjective_load`).  
- `data/validation/` (SemanticValidation records).  
- `outputs/analysis_results.jsonl` (four `AnalysisResult` objects, each containing the required `test_used` field).  
- `outputs/report.md` (statistical summary, tables, confidence intervals, **average NASA‑TLX scores**, success‑rate breakdown).  
- Contract schemas in `contracts/`.  
- End‑to‑end pipeline executable via:  
  ```bash
  python -m src.run_pipeline --config config.yaml
  ```

---



## projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/specs/001-llmxive-follow-up-extending-crafter-a-mu/quickstart.md
# Quickstart: llmXive follow‑up – Cognitive Load Comparison Study

These commands assume a fresh GitHub Actions (or local) runner in the project root.

## 1. Set up the Python environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Dataset Curation
```bash
# Attempt to download a verified CrafterBench subset (several failed figures)
python -m src.curators.curate_failed_figures \
    --download \
    --output-dir data/
```
- If a **verified** open‑source CrafterBench subset is **available**, the script will download and curate a representative set of failed figures with injected errors and corresponding ground‑truth vectors.  
- If no verified source exists, the script aborts with an informative error; this signals that the required dataset must be provided before the study can proceed (FR‑001).  
- **Do not** rely on a synthetic surrogate for scientific conclusions; synthetic data is only used for CI‑verification of pipeline mechanics (see `simulate_participants.py`).

## 3. Run a priori power analysis
```bash
python -m src.simulation.power_analysis \
    --effect-size 0.5 \
    --alpha 0.025 \
    --test mixed_effects
```
*The script prints the required sample size (≈ 40 participants for the mixed‑effects model with expertise covariate) and exits with status 0 if the planned N meets or exceeds it.*

## 4. Launch the interface stubs (sanity check)
```bash
# Structured harness on port 8001
uvicorn src.interfaces.structured_harness:app --port 8001 &
# Chat interface on port 8002
uvicorn src.interfaces.chat_interface:app --port 8002 &
sleep 2

# Verify session initialization (returns JSON with counterbalanced order and **5‑minute** wash‑out)
curl -X POST Connection refused"))] \
    -H "Content-Type: application/json" \
    -d '{"participant_id":"test_user"}'
```

## 5. CI‑Only Pipeline Verification (synthetic participants)
```bash
python -m src.simulation.simulate_participants \
    --participants 30 \
    --seed 42 \
    --log-dir data/logs/
```
*These logs are **not** used for scientific conclusions; they only prove that the pipeline runs and conforms to schemas.*

## 6. Human‑Participant Data Collection (real study)
> Start the FastAPI servers (step 4) and recruit participants. The system will enforce randomization, full counterbalancing, and a **5‑minute** wash‑out interval between interface blocks. Collect NASA‑TLX scores after each task.

## 7. Retention check
```bash
python -m src.analysis.retention_check \
    --log-dir data/logs/ \
    --min-valid 28 \
    --required-participants 32
```

## 8. Validation (Vector match & Semantic similarity)
```bash
python -m src.validation.run_validation \
    --log-dir data/logs/ \
    --output-dir data/validation/
```

## 9. Statistical analysis and report generation
```bash
python -m src.analysis.wilcoxon_analysis \
    --log-dir data/logs/ \
    --validation-dir data/validation/ \
    --output-dir outputs/
python -m src.analysis.generate_report \
    --analysis-dir outputs/ \
    --output-file outputs/report.md
```

---


