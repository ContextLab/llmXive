# Tasks: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001-evaluating-the-impact-of-llm-generated-c/contracts/`.

The study must deliver a three‑condition experimental dataset (LLM / Human / None), automated readability metrics computed against both source code and human docstring, a fully within‑subject human‑study data merge, and a complete statistical analysis (power analysis, one‑way ANOVA per FR‑005, plus a repeated‑measures/mixed‑effects analysis that respects the within‑subject design per the reviewer's objection, and correlation). Tasks are ordered to respect data flow and to produce an early end‑to‑end result on a small sample before scaling to the full dataset.

---

### Phase 1: Setup and first end‑to‑end analysis

- [X] **T012** **Verify pinned requirements file for reproducibility**
  *Implement* `src/utils/verify_requirements.py` that:
  - Checks that `code/requirements.txt` exists (as required by the constitution) and is non‑empty.
  - Optionally verifies that its SHA‑256 hash matches the entry in `data/artifact_hashes.yaml`.
  - Emits a boolean flag and logs to `data/requirements_check.log`.
  *Verification*:
  – Pipeline aborts if the requirements file is missing or empty, ensuring compliance with Constitution Principle I.

- [X] **T001** [US-1] **Download & validate CodeSearchNet Python snippets (REDO: previous execution failed with exit=1)**
  *Implement/repair* `src/data/download.py` that:
  - Downloads the verified CodeSearchNet Python **train** parquet via `hf_hub_download` (repo `kejian/codesearchnet-python-raw`, file `data/train-00000-of-00002-022fcdc5658ecd68.parquet`) with a 3‑attempt retry loop that **raises** on final failure — no synthetic or bundled fallback data.
  - Parses columns tolerant to naming (`code`/`docstring` or `func_code_string`/`func_documentation_string`). Abort with a clear error if neither schema is present.
  - Takes a deterministic seeded subset (`PROJECT_SEED=42`) of **N = 200** snippets (≥ 150 required by SC‑006).
  - Validates docstring relevance (non‑empty, ≥ 5 tokens, not boiler‑plate) and that the code parses with `ast`.
  - Writes valid records to `data/raw_snippets.jsonl` and `data/validated_snippets.jsonl`.
  - Writes excluded records with a `reason` field to `data/excluded_records.json`.
  - Records SHA‑256 checksums of the downloaded parquet files in `data/artifact_hashes.yaml`.
  - **Writes** `data/dataset_preparation.log` summarising total records, valid count, excluded count, and compliance with SC‑006.
  *Verification*:
  – Script exits with status 0.
  – `data/dataset_preparation.log` exists and contains the three counts.
  – `data/validated_snippets.jsonl` contains ≥ 150 valid snippets.
  – Pytest `src/tests/test_download.py` asserts correct column mapping and log creation.

- [X] **T001b** **Download & validate CodeSearchNet Python test split (for validation fixtures)**
  *Implement* `src/data/download_test_split.py` that:
  - Downloads the verified **test** parquet (`kejian/codesearchnet-python-rebalanced`, file `data/test-00000-of-00001-3967e86c21fe91c3.parquet`) with the same retry logic.
  - Writes the raw records to `data/raw_test_snippets.jsonl` and logs checksum in `data/artifact_hashes.yaml`.
  - No further validation is needed; this split is used only for metric‑calculation fixtures in tests.

- [X] **T004** **Validate environment and recruitment tools (REDO: previous executions failed with exit=1)**
  *Implement/repair* `src/utils/validate_environment.py` that:
  - Checks that all required packages import successfully.
  - Verifies available RAM and disk headroom (≤ 7 GB usage) using `psutil`.
  - Confirms presence of a valid HuggingFace token and successful ping to the HF Inference API.
  - Performs a real authenticated GET to the Prolific API to ensure reachability; if credentials are absent, report `success=False` with the specific missing credential in `data/recruitment_validation.log` rather than crashing.
  - Loads `data/consent_form.pdf` to guarantee it is readable.
  - Emits a boolean `success` flag and writes `data/recruitment_validation.log` detailing each check.
  *Verification*:
  – `success=True` and the log contains no error entries when the environment is ready.
  – If any check fails, the script exits with a non‑zero status and a specific reason in the log, halting downstream tasks (SC‑007).

- [ ] **T002** [US-1] **Generate deterministic LLM comments via HuggingFace Inference API** <!-- FAILED-IN-EXECUTION: src/data/generate_comments.py exit=1 -->
  *Implement* `src/data/generate_comments.py` that:
  - Reads `data/validated_snippets.jsonl`.
  - **Uniformly truncates** each snippet to ≤ 2048 tokens using `tiktoken` at the nearest newline; logs each truncation to `data/truncation_warnings.log`. The truncation is applied *before* any variant generation, ensuring the same truncated code is used for LLM, human, and no‑comment conditions (preserving experimental control per Principle VII).
  - Calls **CodeLlama‑7B‑Instruct** (`codellama/CodeLlama-7b-Instruct-hf`) via the HF Inference API with deterministic decoding (`temperature=0.0`, `top_p=1.0`, `seed=42`).
  - Implements ≤ 3 retries per request with exponential backoff (base 60 s). If generation permanently fails for a snippet after all retries, **exclude** that snippet from the LLM dataset and log its `snippet_id` to `data/excluded_llm_generation.json`; do **not** insert a placeholder comment.
  - Writes `data/llm_comments.jsonl` containing `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty string) for all successfully generated snippets.
  - Includes batch checkpointing: after each successful batch, appends to `data/generation_checkpoint.json` so a failed run can resume without re‑processing completed snippets.
  - **Writes** `data/generation.log` capturing start/end timestamps, batch statuses, and any unrecoverable errors; exits non‑zero only on unrecoverable failures after logging.
  *Verification*:
  – Every `snippet_id` from `validated_snippets.jsonl` that succeeded appears exactly once in `llm_comments.jsonl`; failed ones are listed in `excluded_llm_generation.json`.
  – `llm_comment` is non‑empty; `no_comment` is `""`.
  – No snippet exceeds the token limit; any truncation is recorded.
  – The script can be re‑run after interruption and resumes from the last checkpoint.

- [ ] **T003** [US-2] **Compute dual‑reference readability metrics for all comment conditions**
  *Implement* `src/data/metrics.py` that:
  - Consumes `data/llm_comments.jsonl`.
  - For each `snippet_id` creates three rows (conditions `llm`, `human`, `none`) in `data/readability_metrics.csv`.
  - Computes BLEU (nltk), ROUGE‑L (rouge_score), and Sentence‑BERT cosine similarity (`sentence-transformers/multi-qa-mpnet-base-dot-v1`; fallback to `all-MiniLM-L6-v2` on OOM, logging the switch) **against both the source code and the human docstring** for the `llm` and `human` conditions, populating the `*_vs_source` and `*_vs_human` columns as required by `contracts/dataset.schema.yaml`.
  - Normalises all scores to the range [0, 1]; for `none` rows sets metric fields to `null`, `Comment_Length = 0`, `Flesch_Kincaid_Grade = 0`.
  - Adds `Comment_Length` (character count) and `Flesch_Kincaid_Grade` (via `textstat`).
  - Processes data in streaming batches to stay ≤ 7 GB RAM and ≤ 30 min CPU time (SC‑005).
  *Verification*:
  – Each `snippet_id` appears three times with correct `condition` values.
  – Metric columns are floats in [0, 1] or `null` for `none`.
  – `src/tests/test_metrics.py` validates metric values on fixed fixtures (tolerance 0.001) and that identical strings yield a score of 1.0.

- [ ] **T005** [US-3] **Run a miniature end‑to‑end pipeline on 10 snippets**
  *Implement* a `--smoke` mode (or `scripts/run_smoke.sh`) that executes T001–T003 stages on the first 10 validated snippets **and** runs a minimal analysis stub producing `data/results/smoke_analysis.json` with the required `anova_time` fields (F, p_value, df_between, df_within, reject_null). This validates the data flow download → generation → metrics → analysis before the full run.
  *Verification*:
  – The documented smoke command in `quickstart.md` executes with exit 0 and produces non‑empty, real (non‑placeholder) outputs, including `smoke_analysis.json`.

### Phase 2: Complete the study and validate its evidence

- [ ] **T006** [US-3] **Conduct the within‑subject user study**
  *Implement* `src/data/conduct_user_study.py` that:
  - Generates a per‑snippet comprehension task (e.g., “Modify the function to add error handling”) and an answer key stored in `data/task_answer_keys.json`.
  - Uses the Prolific API to create a study where **each participant** evaluates every selected snippet under all three comment conditions, with presentation order randomized per participant via a Latin‑Square scheme.
  - Records for each trial: `completion_time_sec`, binary `accuracy` (checked against the answer key), and a 1–5 Likert `subjective_helpfulness` in `data/human_study_responses.csv` (columns `participant_id`, `snippet_id`, `condition`, `completion_time_sec`, `accuracy`, `subjective_helpfulness`).
  - Fails loudly (non‑zero exit) if the study cannot be launched or required assets are missing.
  *Verification*:
  – CSV contains rows for every participant‑snippet‑condition triple; all fields non‑null.

- [ ] **T014** **Merge and validate the experimental dataset**
  *Implement* `src/data/prepare.py` that:
  - Loads `data/human_study_responses.csv`, `data/llm_comments.jsonl`, and `data/readability_metrics.csv`.
  - Verifies the within‑subject design (each participant has exactly three rows per snippet covering all conditions; each snippet appears equally in all conditions across participants).
  - Merges on `snippet_id` + `condition` to produce `data/merged_dataset.csv`.
  - Validates the merged file against `contracts/dataset.schema.yaml`; aborts with a clear error on any design‑check failure or missing file.
  *Verification*:
  – `merged_dataset.csv` conforms to the schema and contains the required fields; `null` appears only in metric columns for the `none` condition.

- [ ] **T007** [US-3] **Power analysis and sample‑size justification** <!-- FAILED-IN-EXECUTION: src/data/analysis.py exit=1 -->
  *Implement* in `src/data/analysis.py` a power analysis using `statsmodels.stats.power.FTestAnovaPower` with:
  - Effect size f = 0.25, α = 0.05, within‑subject correlation ρ = 0.5.
  - Required per‑group sample size compared with the actual number of participants recruited.
  - Write `results/power_report.txt` containing `effect_size`, `alpha`, `required_sample_per_group`, `achieved_power`, and a plain‑text statement of whether target power (≥ 0.80) is met (FR‑007, SC‑009).
  *Verification*:
  – Report includes all four numeric fields and the target statement.
  – If `achieved_power < 0.80`, a limitation note is present.
  – `src/tests/test_analysis_power.py` validates the report structure.

- [ ] **T015** **Design revision on power shortfall**
  *Implement* a lightweight script `src/data/revise_design.py` that, when `achieved_power < 0.80`, automatically updates the recruitment target in `src/data/conduct_user_study.py` (e.g., increase `TARGET_PARTICIPANTS`) and writes a limitation note to `results/power_limitation.txt`. This satisfies SC‑009’s requirement to revise the study design when power is insufficient.
  *Verification*:
  – If power is low, the script updates the target and produces the limitation note; CI logs the action.

- [ ] **T008** [US-3] **Statistical analysis: one‑way ANOVA plus repeated‑measures mixed‑effects analysis**
  *Implement* in `src/data/analysis.py`:
  - **One‑way ANOVA** (FR‑005) on participant‑averaged completion times and arcsine‑sqrt‑transformed accuracy, outputting `anova_time` and `anova_accuracy` fields (schema‑conformant).
  - **Repeated‑measures mixed‑effects ANOVA** (reviewer concern) using `statsmodels.MixedLM` with fixed effects `condition` and `trial_number`, random intercepts for `participant_id` and `snippet_id`, and a random slope for `trial_number` per participant; also a mixed‑effects logistic regression for accuracy.
  - **Assumption checks** (Shapiro‑Wilk, Levene) reported.
  - Write `results/analysis_results.json` containing `anova_time`, `anova_accuracy`, plus a `mixed_effects` section with the repeated‑measures results and a note explaining which analysis is design‑appropriate.
  *Verification*:
  – JSON validates against `contracts/analysis.schema.yaml`.
  – `p_value` fields are floats in [0, 1]; `reject_null` correctly reflects `p < 0.05`.

- [ ] **T009** [US-2] **Correlation analysis (human‑reference metrics only)**
  *Implement* in `src/data/analysis.py`:
  - Aggregates `data/merged_dataset.csv` per `snippet_id` (mean `completion_time_sec`, mean `accuracy`, mean `subjective_helpfulness`) **only for the `llm` condition**.
  - Computes Pearson correlations between each of the five metrics (`BLEU`, `ROUGE_L`, `Semantic_Similarity`, `Comment_Length`, `Flesch_Kincaid_Grade`) and each outcome (`completion_time_sec`, `accuracy`, `subjective_helpfulness`).
  - Applies Bonferroni correction across all metric‑outcome tests (α = 0.05 / number of tests).
  - Appends a `correlation_metrics` array to `results/analysis_results.json` with fields `metric`, `outcome`, `pearson_r`, `p_value_raw`, `p_value_corrected` (exactly one entry per metric‑outcome pair, matching the schema).
  *Verification*:
  – All metric‑outcome combinations appear once.
  – Corrected p‑values reported; non‑significant results included honestly.
  – `src/tests/test_correlation.py` validates the array length and schema conformity.

- [ ] **T010** [US-3] **Generate figures and results summary**
  *Create*:
  - `figures/fig_time_by_condition.pdf` – plot of completion time by condition (means ± 95 % CI) via `plot_time_by_condition()` in `src/data/analysis.py`.
  - `figures/fig_corr_heatmap.png` – heat‑map of the Pearson correlation matrix (metrics vs. outcomes) via `plot_correlation_heatmap()`.
  - `results/results_summary.md` that: cites exact rows in `merged_dataset.csv` for each reported statistic; summarises power analysis, both ANOVA analyses (one‑way and mixed‑effects) and correlation findings; explicitly notes any limitations (power shortfall, truncation events, excluded‑generation snippets, metric proxy status, and the one‑way‑ANOVA/within‑subject design mismatch resolved in T008); and provides a reproducibility checklist.
  *Verification*:
  – Figures open without error and have labeled axes and legends.
  – Summary references each result artifact and reports negative findings honestly.
  – `src/tests/test_figures.py` checks that the figure files exist and are non‑empty.

### Phase 3: Reproducible results and paper handoff

- [ ] **T011** [US-3] **Contract validation, feasibility measurement, and quickstart documentation**
  *Add*:
  - `src/tests/test_contracts.py` that validates `data/merged_dataset.csv` and `results/analysis_results.json` against their respective schemas.
  - Runtime measurement (peak RSS, wall‑clock) using `psutil`; write `results/feasibility_report.txt` asserting RAM ≤ 7 GB and metric‑stage wall‑clock ≤ 30 min (SC‑005, SC‑010).
  - Update `quickstart.md` with commands for: (1) the smoke run on 10 snippets (T005), (2) the full pipeline. Include a handoff note for the paper stage (layout, PDF compilation, and publication belong to the paper pipeline).
  *Verification*:
  – `pytest -q` passes all tests.
  – `feasibility_report.txt` meets limits.
  – `quickstart.md` reproduces the full run from scratch.

---

### Dependencies and requirement coverage

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR-001 | T001 |
| FR-002 | T002 |
| FR-003 | T003 |
| FR-004 | T006, T014 |
| FR-005 | T008 |
| FR-006 | T004 |
| FR-007 | T007 |
| FR-008 | T006 |
| FR-009 | T011 |
| SC-001 | T001, T002, T003, T006, T008, T009 |
| SC-002 | T002, T003, T006 |
| SC-003 | T003, T009 |
| SC-004 | T008 |
| SC-005 | T003, T011 |
| SC-006 | T001 |
| SC-007 | T004 |
| SC-008 | T002 |
| SC-009 | T007, T015 |
| SC-010 | T011 |

All tasks respect the data‑flow ordering: download → validation → generation → metrics → smoke run → user study launch → dataset merge → power analysis → statistical analysis → correlation → figures → validation & documentation.

### Alignment with Constitution

- Reproducibility is enforced via deterministic seeds, checkpointing, and the early `T012` requirements check.
- Verified accuracy is maintained by using only the verified CodeSearchNet sources listed in the plan.
- Data hygiene is ensured through immutable raw files, checksums, and explicit log artifacts.
- Single source of truth is upheld by referencing exact rows in `merged_dataset.csv` from figures and summary.
- Versioning discipline is supported by artifact hash recording in `data/artifact_hashes.yaml`.
- Automated metric‑human correlation validation is performed in T009.
- Controlled experimental condition isolation is guaranteed by the Latin‑Square design in T006 and uniform truncation in T002.
