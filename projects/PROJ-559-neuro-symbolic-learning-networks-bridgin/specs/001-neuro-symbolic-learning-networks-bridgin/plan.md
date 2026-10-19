# Implementation Plan: Neuro‑Symbolic Learning Networks

**Branch**: `[PROJ-559-neuro-symbolic]` | **Date**: 2026‑10‑19 | **Spec**: `specs/PROJ-559-neuro-symbolic/spec.md`  
**Input**: Feature specification from `specs/PROJ-559-neuro-symbolic/spec.md`

## Summary
Implement a lightweight neuro‑symbolic explanation framework that (1) ingests math/logic problems from the public **ASSISTments** dataset, (2) generates three distinct explanation artifacts per problem (`neural`, `symbolic`, `neuro‑symbolic`), (3) presents a selected explanation to a Bayesian Knowledge Tracing (BKT) student simulator, (4) logs interaction data (correctness, response time, comprehension rating), (5) calibrates the simulator against a real‑human pilot (≥ 50 participants), (6) runs a mixed‑effects regression on combined simulated + real data (≥ 200 participants) to compare the three conditions on reasoning accuracy, response time, and self‑reported comprehension, and (7) enforces all functional (FR‑001–FR‑022) and success criteria (SC‑001–SC‑012) while staying within GitHub Actions free‑tier limits (≤ 2 CPU cores, ≤ 7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11 (core pipeline), R 4.3+ (optional mixed‑effects via `lme4`), Bash orchestration.
- **Primary Dependencies**: `transformers` (4‑bit quantized TinyLlama‑1.1B‑Chat), `datasets`, `pandas`, `numpy`, `scikit‑learn`, `statsmodels`, `pyyaml`, `rpy2`, `llmxive_toolkit`.
- **Storage**: File‑system under `data/` (raw, processed, traces, pilot, results).
- **Testing**: `pytest` + CI resource‑monitoring scripts.
- **Target Platform**: Linux runner on GitHub Actions (2 vCPU, 7 GB RAM, 14 GB disk).
- **Project Type**: Research pipeline / CLI tool.
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RAM ≤ 7 GB, peak CPU ≤ 2 cores.
- **Constraints**: CPU‑first; if LLM inference exceeds memory, auto‑offload to Kaggle GPU (real 4‑bit model, ≤ 2 h GPU time).
- **Scale/Scope**: ≥ 5 000 interaction logs (≥ 2 000 simulated per condition + ≥ 200 real), ≥ 1 000 problems (stratified across ASSISTments and optional Khan Academy).

## Constitution Check
| Principle | Status | Implementation Strategy |
|-----------|--------|--------------------------|
| **I. Reproducibility** | PASS | Fixed random seeds (`config.yaml`), immutable raw files, deterministic pipelines, CI‑run isolation. |
| **II. Verified Accuracy** | PASS | `tools/reference_validator.py` validates all external URLs against the verified‑datasets block with `CITATION_TITLE_OVERLAP_THRESHOLD = 0.8`. |
| **III. Data Hygiene** | PASS | Raw files checksum‑verified (`sha256` stored in `state/`); all transformations write new files; no PII. |
| **IV. Single Source of Truth** | PASS | Every figure/table generated directly from `data/processed/` via scripts; no manual entry. |
| **V. Versioning Discipline** | PASS | Content‑hashes recorded in `state/projects/...yaml`; any change updates the hash and invalidates dependent artifacts. |
| **VI. Educational Evaluation Rigor** | PASS | Mixed‑effects model includes required covariates; effect sizes with 95 % CI reported; no metric substitution. |
| **VII. Explanation Traceability** | PASS | Each explanation stored under `data/traces/` with metadata (`explanation_id`, `model_version`, timestamps). |

## Project Structure
```text
specs/PROJ-559-neuro-symbolic/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/

projects/PROJ-559-neuro-symbolic/
├── code/
│   ├── config.yaml
│   ├── data/
│   │   ├── download_assistments.py          # T012 – produces data/raw/assistments.csv + checksum
│   │   ├── download_khan.py                 # T012c – graceful timeout, error‑code 1, logs message
│   │   ├── unify_datasets.py                # T012e – merges datasets, produces unified_problems.csv + checksum
│   │   └── validate_schema.py               # T012a – validates unified_problems.csv against problem.schema.yaml
│   ├── generation/
│   │   ├── neural_generator.py
│   │   ├── symbolic_solver.py
│   │   ├── neuro_symbolic.py
│   │   └── batch_generate.py                # orchestrates FR‑002, FR‑017, FR‑018, FR‑019
│   ├── simulation/
│   │   ├── bkt_model.py
│   │   ├── pilot_calibrator.py              # T030a/b/c – consumes data/pilot/real_pilot_data.csv
│   │   ├── simulator.py
│   │   └── run_simulation.py                # FR‑009, FR‑020
│   ├── analysis/
│   │   ├── merge_data.py
│   │   ├── regression_analysis.py           # FR‑006, SC‑003, multiple‑comparison correction
│   │   └── report_generator.py
│   ├── tools/
│   │   └── reference_validator.py
│   └── tests/
│       ├── test_download.py
│       ├── test_generation.py
│       └── test_simulation.py
├── data/
│   ├── raw/
│   ├── processed/
│   ├── traces/
│   └── pilot/
├── contracts/
│   ├── analysis_output.schema.yaml
│   ├── explanation.schema.yaml
│   ├── interaction_log.schema.yaml
│   ├── pilot_data.schema.yaml
│   ├── problem.schema.yaml
│   └── simulation_log.schema.yaml
├── state/
│   └── projects/PROJ-559-neuro-symbolic-learning-networks-bridgin.yaml
├── requirements.txt
└── README.md
```

## Phase‑by‑Phase Plan (covers every FR/SC)

| Phase | Tasks (maps to FR/SC) | Key Outputs |
|-------|-----------------------|--------------|
| **0. CI & Citation Gate** | Run `reference_validator.py` (FR‑022). | Pass/Fail CI gate. |
| **1. Data Ingestion** | - `download_assistments.py` (FR‑001, FR‑007, SC‑008).<br>- `download_khan.py` (optional, FR‑001, FR‑007, SC‑008).<br>- `unify_datasets.py` (FR‑001, FR‑012, FR‑021).<br>- Generate checksums (`state/`), log any missing/corrupt records (FR‑018). | `data/raw/assistants.csv`, optional `khan_academy.csv`, `data/processed/unified_problems.csv`. |
| **2. Schema Validation** | `validate_schema.py` validates `unified_problems.csv` against `problem.schema.yaml` (FR‑001, FR‑018). | Pass/Fail; logs schema violations. |
| **3. Explanation Generation** | `batch_generate.py` loops over problems: <br>• Neural generation via quantized LLM (FR‑002, FR‑017).<br>• Symbolic solving (rule‑based) (FR‑002).<br>• Neuro‑symbolic merging (FR‑002).<br>• Timeout handling (FR‑017) and missing‑record skipping (FR‑018).<br>• Validation of comprehension rating range (FR‑019). | `data/traces/explanation_<condition>_<problem_id>.txt`, metadata JSON, logs of timeouts & skips (SC‑009, SC‑010, SC‑011). |
| **4. Human Pilot Collection** | Manual step: collect ≥ 50 pilot interactions → `data/pilot/real_pilot_data.csv`.<br>Run `pilot_calibrator.py` (FR‑010, SC‑007). | Calibrated BKT parameters, calibration report (RMSE, TOST). |
| **5. Simulation Run** | `run_simulation.py` uses calibrated BKT to simulate ≥ 2 000 students per condition (FR‑009, FR‑020). Logs all required fields (FR‑004, FR‑005). | `data/processed/interaction_logs_simulated.csv`. |
| **6. Real‑Student Data Integration** | Manual step: collect ≥ 200 real interactions → `data/processed/real_student_data.csv`.<br>Merge with simulated logs (`merge_data.py`) adding `data_source` column (FR‑011). | `data/processed/merged_interaction_logs.csv`. |
| **7. Mixed‑Effects Regression** | `regression_analysis.py` fits LMM with fixed effects (condition, prior_knowledge, difficulty, data_source) and random intercepts (problem_id, student_id) (FR‑006).<br>- Applies Holm‑Bonferroni correction for 3 pairwise tests (SC‑003).<br>- Reports Cohen’s d with 95 % CI (SC‑003).<br>- Checks collinearity between difficulty and response time; if VIF > 5, note in diagnostics. | `results/analysis_output.yaml` (conforms to `analysis_output.schema.yaml`). |
| **8. Reporting & CI Summary** | `report_generator.py` creates markdown summary, tables, and CI‑summary metrics (SC‑001, SC‑002, SC‑005, SC‑006, SC‑009‑SC‑012). | `results/report.md`. |
| **9. Resource Monitoring** | Wrapper script records peak CPU/memory (FR‑008). Fails if > 2 cores or > 7 GB (SC‑006). | CI job summary logs. |
| **10. Scope‑Reduction Protocol** | Embedded in `download_khan.py` and `unify_datasets.py`; if Khan missing, limit claims to ASSISTments and log limitation (SC‑001). | Updated `report.md` “Limitations” section. |

### Edge‑Case Handling (US‑4, US‑2, US‑3)
- **Generation timeout** → abort that problem, log, continue (≤ 2 % allowed per SC‑010).  
- **Corrupt problem record** → log warning, skip (≤ 1 % allowed per SC‑011).  
- **Non‑numeric comprehension rating** → validation error, omit record (≤ 0.5 % allowed per SC‑012).  

### Compute Feasibility
- **LLM**: TinyLlama‑1.1B‑Chat quantized to 4‑bit (`bitsandbytes`), ~2 GB VRAM, runs on CPU (< 1 GB RAM). If OOM, auto‑offload to Kaggle GPU (real GPU, no fabrication).  
- **Simulation**: Pure NumPy loops, < 500 MB RAM.  
- **Analysis**: `statsmodels` mixed‑effects on ≤ 10 000 rows, < 1 GB RAM.  

### Power / Sample‑Size (deferred)
- Target power ≥ 0.80 for effect size ≥ 0.1 will be confirmed after data collection; placeholder `[deferred]` used per guidelines.

---
