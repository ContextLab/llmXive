# Tasks: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001-evaluating-the-impact-of-llm-generated-c/contracts/`.

The study must deliver a three‑condition experimental dataset (LLM / Human / None), automated readability metrics computed against both source code and human docstring, a fully within‑subject human‑study data merge, and a complete statistical analysis (power analysis, one‑way ANOVA, correlation).  
Tasks are ordered to respect data flow and to produce an early end‑to‑end result on a small sample before scaling to the full dataset.

---

### Phase 1: Setup and first end‑to‑end analysis  

- [X] **T012** **Verify pinned requirements file for reproducibility**  
  *Implement* `src/utils/verify_requirements.py` that:  
  - Checks that `requirements.txt` exists at the repository root and is non‑empty.  
  - Optionally verifies that its SHA‑256 hash matches the entry in `data/artifact_hashes.yaml`.  
  - Emits a boolean flag and logs to `data/requirements_check.log`.  
  *Verification*:  
  – Pipeline aborts if the requirements file is missing or empty, ensuring compliance with Constitution Principle I.  

- [ ] **T001** [US-1] **Download & validate CodeSearchNet Python snippets (including log generation)**   <!-- FAILED-IN-EXECUTION: scripts/run_tests.sh exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  *Implement* `src/data/download.py` that:  
  - Downloads the verified CodeSearchNet Python parquet files via `hf_hub_download` with a 3‑attempt retry loop that **raises** on final failure.  
  - Parses columns tolerant to naming (`code`/`docstring` or `func_code_string`/`func_documentation_string`). Abort with a clear error if neither schema is present.  
  - Takes a deterministic seeded subset (`PROJECT_SEED=42`) of **N = 500** snippets.  
  - Validates docstring relevance (non‑empty, ≥ 5 tokens, not boiler‑plate).  
  - Writes **valid** records to `data/raw_snippets.jsonl` and `data/validated_snippets.jsonl`.  
  - Writes excluded records with a `reason` field to `data/excluded_records.json`.  
  - Records SHA‑256 checksums of the downloaded parquet files in `data/artifact_hashes.yaml`.  
  - **Writes** a log file `data/dataset_preparation.log` summarising total records, valid count, excluded count, and compliance with SC‑006.  
  *Verification*:  
  – Script exits with status 0.  
  – `data/dataset_preparation.log` exists and contains the three counts.  
  – `data/validated_snippets.jsonl` contains ≥ 150 valid snippets.  
  – Pytest `src/tests/test_download.py` asserts correct column mapping and log creation.  

- [ ] **T004** [US-3] **Validate environment and recruitment tools**   <!-- FAILED-IN-EXECUTION: src/utils/validate_environment.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/utils/validate_environment.py exit=1 -->
  *Implement* `src/utils/validate_environment.py` that:  
  - Checks that all required packages import successfully.  
  - Verifies available RAM and disk headroom (≤ 7 GB usage) using `psutil`.  
  - Confirms presence of a valid HuggingFace token and successful ping to the HF Inference API.  
  - Performs a real authenticated GET to the Prolific API to ensure reachability.  
  - Loads `data/consent_form.pdf` to guarantee it is readable.  
  - Emits a boolean `success` flag and writes `data/recruitment_validation.log` detailing each check.  
  *Verification*:  
  – `success=True` and the log contains no error entries when the environment is ready.  
  – If any check fails, the script exits with a non‑zero status, halting downstream tasks (SC‑007).  

- [ ] **T002** [US-1] **Generate deterministic LLM comments via HuggingFace Inference API**  
  *Implement* `src/data/generate_comments.py` that:  
  - Reads `data/validated_snippets.jsonl`.  
  - **Uniformly truncates** each snippet to ≤ 2048 tokens using `tiktoken` at the nearest newline; logs each truncation to `data/truncation_warnings.log`. The truncation is applied *before* any variant generation, ensuring the same truncated code is used for LLM, human, and no‑comment conditions (preserving experimental control per Principle VII).  
  - Calls **CodeLlama‑7B‑Instruct** (`codellama/CodeLlama-7b-Instruct-hf`) via the HF Inference API with deterministic decoding (`temperature=0.0`, `top_p=1.0`, `seed=42`).  
  - Implements ≤ 3 retries per request with exponential backoff (base 60 s).  
  - Writes `data/llm_comments.jsonl` containing `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty string).  
  - Includes batch checkpointing: after each successful batch, appends to a checkpoint file `data/generation_checkpoint.json` so a failed run can resume without re‑processing completed snippets.  
  - **Writes** a detailed `data/generation.log` capturing start/end timestamps, batch statuses, and any unrecoverable errors; the script exits with a non‑zero code only on unrecoverable failures after logging.  
  *Verification*:  
  – Every `snippet_id` from `validated_snippets.jsonl` appears exactly once in `llm_comments.jsonl`.  
  – `llm_comment` is non‑empty; `no_comment` is `""`.  
  – No snippet exceeds the token limit; any truncation is recorded.  
  – The script can be re‑run after interruption and resumes from the last checkpoint.  

- [ ] **T003** [US-2] **Compute dual‑reference readability metrics for all comment conditions**  
  *Implement* `src/data/metrics.py` that:  
  - Consumes `data/llm_comments.jsonl`.  
  - For each `snippet_id` creates three rows (conditions `llm`, `human`, `none`) in `data/readability_metrics.csv`.  
  - Computes BLEU (nltk), ROUGE‑L (rouge_score), and Sentence‑BERT cosine similarity (`sentence-transformers/multi-qa-mpnet-base-dot-v1`; fallback to `all-MiniLM-L6-v2` on OOM) **against the source code** and **against the human docstring** for `llm` and `human` conditions.  
  - Normalises all scores to the range [0, 1]; for `none` rows sets metric fields to `null`, `Comment_Length = 0`, `Flesch_Kincaid_Grade = 0`.  
  - Adds `Comment_Length` (character count) and `Flesch_Kincaid_Grade` (via `textstat`).  
  - Processes data in streaming batches to stay ≤ 7 GB RAM and ≤ 30 min CPU time (SC‑005).  
  *Verification*:  
  – Each `snippet_id` appears three times with correct `condition` values.  
  – Metric columns are floats in [0, 1] or `null` for `none`.  
  – `src/tests/test_metrics.py` validates metric values on fixed fixtures (tolerance 0.001) and that identical strings yield a score of 1.0.  

- [ ] **T005** [US-3] **Conduct the within‑subject user study**  
  *Implement* `src/data/conduct_user_study.py` that:  
  - Uses the Prolific API to create a study where **each participant evaluates every selected snippet under all three comment conditions** (fully within‑subject design, satisfying FR‑008).  
  - Randomises the presentation order per participant using a Latin‑Square scheme to eliminate order effects.  
  - Records for each trial: `completion_time_sec`, binary `accuracy`, and a 1‑5 Likert `subjective_helpfulness`.  
  - Stores results in `data/human_study_responses.csv` with columns `participant_id`, `snippet_id`, `condition`, `completion_time_sec`, `accuracy`, `subjective_helpfulness`.  
  - Fails loudly (non‑zero exit) if the study cannot be launched or required assets are missing.  
  *Verification*:  
  – CSV contains exactly three rows per participant‑snippet (one per condition).  
  – All fields are non‑null and conform to `contracts/dataset.schema.yaml`.  
  – A pytest `src/tests/test_user_study.py` checks schema compliance.  

- [ ] **T006** [US-2] **Merge human‑study data with comments and metrics**  
  *Implement* `src/data/prepare.py` that:  
  - Loads `data/human_study_responses.csv`, `data/llm_comments.jsonl`, and `data/readability_metrics.csv`.  
  - Verifies the within‑subject design: each participant has exactly three rows per snippet covering all conditions, and across participants each snippet appears equally in all conditions.  
  - Merges on `snippet_id` + `condition` to produce `data/merged_dataset.csv` that validates against `contracts/dataset.schema.yaml`.  
  - Aborts with a clear error if any design check fails or required files are missing.  
  *Verification*:  
  – Every row in `merged_dataset.csv` contains all required fields; `null` appears only in metric columns for `condition="none"`.  
  – Design balance check passes; a pytest `src/tests/test_prepare.py` asserts the balance.  

- [ ] **T007** [US-3] **Power analysis (ANOVA) and sample‑size justification**  
  *Implement* in `src/data/analysis.py` a power analysis using `statsmodels.stats.power.FTestAnovaPower` with:  
  - Effect size f = 0.25, α = 0.05, within‑subject correlation ρ = 0.5.  
  - Compute the required per‑group sample size and compare with the actual number of participants recruited.  
  - Write `results/power_report.txt` containing `effect_size`, `alpha`, `required_sample_per_group`, `achieved_power`, and a plain‑text statement indicating whether the target power (≥ 0.80) is met (FR‑007, SC‑009).  
  *Verification*:  
  – Report includes all four numeric fields and the target statement.  
  – If `achieved_power < 0.80`, a limitation note is present.  
  – JSON schema validation is performed by `src/tests/test_analysis_power.py`.  

- [ ] **T008** [US-3] **One‑way ANOVA on completion time and accuracy**  
  *Implement* in `src/data/analysis.py`:  
  - **Completion time**: ordinary least‑squares one‑way ANOVA (`statsmodels.formula.api.ols`) with factor `condition`; compute F, p‑value, `df_between`, `df_within`; set `reject_null` based on α = 0.05.  
  - **Accuracy**: apply arcsine‑sqrt transformation to binary accuracy values, then run the same OLS one‑way ANOVA pipeline.  
  - Output `results/analysis_results.json` containing `anova_time` and `anova_accuracy` objects that conform to `contracts/analysis.schema.yaml`.  
  *Verification*:  
  – JSON validates against the schema.  
  – `p_value` fields are floats in [0, 1]; `reject_null` correctly reflects `p < 0.05`.  
  – A synthetic fixture test asserts that both ANOVA results are produced and that `reject_null` matches the computed p‑value.  

- [ ] **T009** [US-3] **Correlation analysis (human‑reference metrics only)**  
  *Implement* in `src/data/analysis.py` that:  
  - Aggregates `data/merged_dataset.csv` per `snippet_id` (mean `completion_time_sec`, mean `accuracy`, mean `subjective_helpfulness`) **only for the `llm` condition**.  
  - Computes Pearson correlations between each of the four metrics (`BLEU`, `ROUGE_L`, `Semantic_Similarity`, `Comment_Length`) **using the human‑reference scores** and each outcome (`completion_time_sec`, `accuracy`, `subjective_helpfulness`).  
  - Applies Bonferroni correction for the 12 tests (α = 0.05/12).  
  - Appends a `correlation_metrics` array to `results/analysis_results.json` with fields `metric`, `outcome`, `pearson_r`, `p_value_raw`, `p_value_corrected` (exactly one entry per metric‑outcome pair, matching the schema).  
  *Verification*:  
  – All 12 metric‑outcome combinations appear once.  
  – Corrected p‑values are reported; non‑significant results are included honestly.  
  – `src/tests/test_correlation.py` validates the array length and schema conformity.  

- [ ] **T010** [US-3] **Generate figures and results summary**  
  *Create*:  
  - `figures/fig_time_by_condition.pdf` – box‑plot of completion time by condition with 95 % confidence intervals.  
  - `figures/fig_corr_heatmap.png` – heat‑map of the Pearson correlation matrix (metrics vs. outcomes).  
  - `results/results_summary.md` that:  
    * cites exact rows in `merged_dataset.csv` for each reported statistic,  
    * summarizes power analysis, ANOVA, and correlation findings,  
    * explicitly notes any limitations (e.g., power shortfall, truncation events, metric proxy status), and  
    * provides a reproducibility checklist.  
  *Verification*:  
  – Figures open without error and have labeled axes and legends.  
  – Summary references each result artifact and reports negative findings honestly.  
  – A pytest `src/tests/test_figures.py` checks that the figure files exist and are non‑empty.  

- [ ] **T011** [US-3] **Contract validation, feasibility measurement, and quickstart documentation**  
  *Add*:  
  - `src/tests/test_contracts.py` that validates `data/merged_dataset.csv` and `results/analysis_results.json` against their respective schemas.  
  - Runtime measurement (peak RSS, wall‑clock) using `psutil`; write `results/feasibility_report.txt` asserting RAM ≤ 7 GB and metric‑stage wall‑clock ≤ 30 min (SC‑010).  
  - Verify the presence of a pinned `requirements.txt` at the repository root; fail if missing (addresses reproducibility).  
  - Update `quickstart.md` with commands for:  
    1. Running the early‑checkpoint pipeline on 10 snippets (produces a miniature end‑to‑end result).  
    2. Running the full pipeline.  
    Include a handoff note for the paper‑stage.  
  *Verification*:  
  – `pytest -q` passes all tests.  
  – `feasibility_report.txt` meets limits.  
  – `quickstart.md` reproduces the full run from scratch.  

---  

### Dependencies and requirement coverage  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 | T001 |
| FR‑002 | T002 |
| FR‑003 | T003 |
| FR‑004 | T006 |
| FR‑005 | T008 |
| FR‑006 | T004 |
| FR‑007 | T007 |
| FR‑008 | T005 |
| FR‑009 | T011 |
| SC‑001 | T001, T002, T003, T005, T006, T008, T009 |
| SC‑002 | T002, T003, T005 |
| SC‑003 | T003, T009 |
| SC‑004 | T008 |
| SC‑005 | T003 |
| SC‑006 | T001 |
| SC‑007 | T004 |
| SC‑008 | T002 |
| SC‑009 | T007 |
| SC‑010 | T011 |

All tasks respect the data‑flow ordering: download → validation → environment check → comment generation → metric computation → user study → merge → power analysis → one‑way ANOVA → correlation → figures → validation & documentation.  

---  

### Notes on Experimental Control  

- Truncation of code snippets to 2048 tokens (T002) is performed **once**, prior to generating any comment variant, and the truncated code is used identically for LLM, human, and no‑comment conditions. This preserves the “all other variables held constant” requirement of Principle VII.  

- All logging files (`dataset_preparation.log`, `generation.log`, `truncation_warnings.log`, `recruitment_validation.log`, etc.) are written explicitly to enable verification of compliance with the corresponding success criteria.  

---  

### Alignment with Constitution  

- Reproducibility is enforced via deterministic seeds, checkpointing, and the early `T012` requirements check.  
- Verified accuracy is maintained by using only the verified CodeSearchNet URLs listed in the plan.  
- Data hygiene is ensured through immutable raw files, checksums, and explicit log artifacts.  
- Single source of truth is upheld by referencing exact rows in `merged_dataset.csv` from figures and summary.  
- Versioning discipline is supported by artifact hash recording in `data/artifact_hashes.yaml`.  
- Automated metric‑human correlation validation is performed in T009.  
- Controlled experimental condition isolation is guaranteed by the Latin‑Square design in T005 and uniform truncation in T002.  
