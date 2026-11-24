# Implementation Plan: Neuro‑Symbolic Learning Networks

**Branch**: `[PROJ-559-neuro-symbolic]` | **Date**: 2026‑10‑23 | **Spec**: `specs/PROJ-559-neuro-symbolic/spec.md`  
**Input**: Feature specification from `specs/PROJ-559-neuro-symbolic/spec.md`

## Summary
Implement a lightweight neuro‑symbolic explanation pipeline that (1) downloads the public ASSISTments dataset **and** the Khan Academy dataset (both required), (2) generates three explanation artifacts per problem, (3) presents each explanation to a deterministic BKT‑based student simulator via a well‑defined API (FR‑003), (4) logs simulated and real student interactions, (5) calibrates the BKT simulator on a human pilot, (6) runs mixed‑effects regressions—exploratory on the combined simulated + real dataset and primary on the real‑only dataset—while respecting GitHub Actions free‑tier limits (≤ 2 CPU cores, ≤ 7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11 (core), R 4.3+ (optional, for `lme4` via `rpy2`)  
- **Primary Dependencies**: `transformers[bitsandbytes]`, `datasets`, `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `rpy2`, `llmxive_toolkit`.  
- **Storage**: Files under `data/` (raw, processed, traces, pilot, results).  
- **Target Platform**: GitHub Actions Linux runner (2 vCPU, 7 GB RAM, a disk with sufficient storage capacity (approximately tens of gigabytes)).  
- **Compute Strategy**: CPU‑first using 4‑bit quantized TinyLlama‑1.1B‑Chat; if OOM, automatic off‑load to a free Kaggle GPU (real GPU, no fabrication).  
- **Scale/Scope**: ≥ 5 000 interaction records for analysis (SC‑002); ≥ 200 real participants for primary inference; ≥ 2 000 simulated students per condition (exploratory only).  

## Constitution Check
| Principle | Status | Implementation |
|-----------|--------|----------------|
| **I. Reproducibility** | PASS | Fixed seeds (`config.yaml`), immutable raw files, deterministic pipelines, CI isolation. |
| **II. Verified Accuracy** | PASS | `tools/reference_validator.py` runs at pipeline start with threshold 0.8; all external URLs verified (ASSISTments). |
| **III. Data Hygiene** | PASS | SHA‑256 checksums recorded in `state/`; no in‑place modifications; PII never stored. |
| **IV. Single Source of Truth** | PASS | All figures/tables generated directly from `data/processed/` via scripts; no manual entry. |
| **V. Versioning Discipline** | PASS | Content hashes stored in `state/projects/...yaml`; any change invalidates dependent artifacts. |
| **VI. Educational Evaluation Rigor** | PASS | Mixed‑effects model includes required covariates; effect sizes with 95 % CI; no metric substitution. |
| **VII. Explanation Traceability** | PASS | Every explanation saved under `data/traces/` with JSON metadata linking problem, model version, and condition. |

## Project Structure
```text
specs/PROJ-559-neuro-symbolic/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis_output.schema.yaml
    ├── explanation.schema.yaml
    ├── interaction_log.schema.yaml
    ├── pilot_data.schema.yaml
    ├── problem.schema.yaml
    └── simulation_log.schema.yaml
```

## Phase‑by‑Phase Plan (covers every FR & SC)

| Phase | Tasks (FR → SC) | Key Outputs |
|-------|-----------------|-------------|
| **0. Citation Gate** | Run `tools/reference_validator.py` (FR‑022). **Fail** CI if any URL has title‑overlap < 0.8. | Pass/Fail gate. |
| **1. Data Ingestion** | • `data/download_assistments.py` fetches ASSISTments CSV (FR‑001, FR‑007, SC‑008).<br>• `data/download_khan.py` **must** fetch the Khan Academy dataset (FR‑001). If the download fails (no verified URL or timeout), the pipeline aborts with exit 1 and logs a clear error (FR‑007, SC‑008).<br>• Generate SHA‑256 checksums (data hygiene).<br>• `data/unify_datasets.py` merges the two sources, **enforces ≥ 30 % representation from each source** (FR‑012, FR‑021). | `data/raw/assistments.csv`, `data/raw/khan_academy.csv`, checksums, `data/processed/unified_problems.csv`. |
| **2. Schema Validation** | `data/validate_schema.py` validates `unified_problems.csv` against `contracts/problem.schema.yaml` (FR‑001, FR‑018). Abort on error. | Validation log; guaranteed schema conformity. |
| **3. Explanation Generation** | `generation/batch_generate.py` iterates over `unified_problems.csv`:<br>• Neural: `neural_generator.py` (quantized LLM, FR‑002).<br>• Symbolic: `symbolic_solver.py` (rule‑based, FR‑002).<br>• Neuro‑symbolic: `neuro_symbolic.py` merges both (FR‑002).<br>• Enforce per‑problem generation timeout (`config.yaml` default 180 s) – on timeout log error, skip problem (FR‑017, SC‑010).<br>• Detect corrupt problem records, log warning, skip (FR‑018, SC‑011).<br>• **Validate each generated explanation JSON metadata against `contracts/explanation.schema.yaml`; CI fails on violations** (plan‑consistency‑54cdec41).<br>• **Record generation success rate; CI fails if < 95 % of problems have all three explanations** (SC‑001). | `data/traces/` files, generation summary CSV, timeout & skip counts, validation log. |
| **4. API Delivery to Simulator (FR‑003)** | `simulation/present_to_simulator.py` loads each explanation file and calls the deterministic API `simulator.run_explanation(explanation_path)` for the BKT‑based student simulator. Logs the API call and ensures a deterministic mapping between `problem_id`, `condition`, and the simulator invocation. | Confirmation log of API calls; no data mutation. |
| **5. Human Pilot Collection (FR‑010)** | 1. Manual collection of ≥ 50 participants across three explanation conditions; stored as `data/pilot/real_pilot_data.csv`.<br>2. **Validate pilot CSV against `contracts/pilot_data.schema.yaml`; abort on schema violation** (plan‑consistency‑9cd9c8a0).<br>3. Calibrate the BKT simulator:<br>&nbsp;&nbsp;`simulation/pilot_calibrator.py` fits BKT parameters, computes RMSE, TOST. If calibration fails (RMSE > 0.15, diff > 0.02, or TOST p < 0.10) the pipeline aborts (FR‑010). | Calibrated `simulation/config.yaml`, calibration report. |
| **6. Simulation Run (FR‑009, FR‑004, FR‑005, FR‑019)** | `simulation/run_simulation.py` uses calibrated BKT to simulate **≥ 2 000** students per condition.<br>• For each problem‑explanation pair, the simulator is invoked via the deterministic API (Phase 4).<br>• Logs fields per FR‑004, FR‑005; validates comprehension rating range (FR‑019).<br>• **Validate simulated logs against both `contracts/interaction_log.schema.yaml` and `contracts/simulation_log.schema.yaml`; CI fails on violations** (plan‑consistency‑d2c59896).<br>• **SC‑005 checks**: ≥ 99 % of logs contain all required fields; response‑time histogram has no > 5 s gaps (≤ 2 consecutive empty bins). Violations are reported in CI summary. | `data/processed/interaction_logs_simulated.csv`. |
| **7. Real‑Student Data Integration (FR‑011)** | 1. Manual collection of ≥ 200 participants; stored as `data/processed/real_student_data.csv`.<br>2. **Validate real CSV against `contracts/interaction_log.schema.yaml`; abort on error** (plan‑consistency‑4f97c6b9).<br>3. Merge simulated and real logs into `data/processed/merged_interaction_logs.csv` (adds `data_source` column). | Merged CSV ready for analysis. |
| **8. Mixed‑Effects Regression** | **Exploratory Diagnostics (Combined Data)**:<br>• `analysis/exploratory_regression.py` runs the mixed‑effects model on the **combined** dataset (simulated + real) **solely for diagnostics** (SC‑009, SC‑010, SC‑011). Reports effect sizes, CI widths, and `data_source` effect (not used for primary inference).<br>**Primary Inference (Real‑Only Data)**:<br>• `analysis/regression_analysis.py` fits a mixed‑effects model **only on the real‑student subset** (FR‑006, FR‑011).<br>• Fixed effects: `condition`, `prior_knowledge_score`, `difficulty`.<br>• Random intercepts: `problem_id`, `student_id`.<br>• **No `data_source` fixed effect** (methodology‑7140b7f8).<br>• Compute Cohen’s d with 95 % CI for each pairwise condition comparison (SC‑003).<br>• Apply Holm‑Bonferroni correction for multiple comparisons.<br>• **Validate output against `contracts/analysis_output.schema.yaml`**.<br>• **SC‑002 check**: abort if total interaction records < 5 000. | `results/analysis_output.yaml` (primary), `results/exploratory_output.yaml` (diagnostics). |
| **9. Reporting & CI Summary** | `analysis/report_generator.py` produces `results/report.md` containing:<br>• Primary regression table and effect sizes (real‑only).<br>• Exploratory diagnostics summary (combined).<br>• Calibration statistics (RMSE, TOST).<br>• SC‑001, SC‑005, SC‑009‑SC‑012 metrics (generation success, timeout counts, missing‑record counts, invalid‑rating counts).<br>• Resource usage summary (peak CPU ≤ 2 cores, RAM ≤ 7 GB) (SC‑006). | Human‑readable markdown report. |
| **10. Resource Monitoring** | `tools/resource_monitor.py` wraps the entire pipeline, records peak CPU cores and RAM; fails with exit 1 if > 2 cores or > 7 GB (FR‑008, SC‑006). | CI job summary logs. |
| **11. Scope‑Reduction Protocol** | If Khan download fails (no verified source), the pipeline aborts with a clear error (see Phase 1). This satisfies FR‑001’s requirement for both datasets and flags the limitation for a future spec amendment. | Updated CI exit behavior. |

### Edge‑Case Handling (US‑4, US‑2, US‑3)
- **Explanation timeout** → counted, logged, skipped; must stay ≤ 2 % of problems (SC‑010).  
- **Corrupt problem record** → warning, skip; ≤ 1 % allowed (SC‑011).  
- **Non‑numeric comprehension rating** → validation error, record omitted; ≤ 0.5 % allowed (SC‑012).

### Compute Feasibility
- **CPU‑First**: TinyLlama‑1.1B‑Chat quantized to 4‑bit runs < 2 GB RAM, < 2 CPU cores per inference.  
- **GPU Escape Hatch**: If CPU OOM occurs, the script re‑executes with `device="cuda"` on a free Kaggle GPU (real off‑load). No fabricated CPU surrogate is used.  
- **Streaming**: Large CSVs processed with `datasets.load_dataset(..., streaming=True)` to keep RAM under 7 GB.  
- **Runtime**: End‑to‑end ≤ 5 h on the free CI runner; GPU off‑load adds ≤ 2 h, still within the 6 h job limit.  

---


