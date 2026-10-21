# Tasks: Evaluating the Impact of LLM-Generated Code Comments on Code Readability

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001-evaluating-the-impact-of-llm-generated-c/contracts/`.

The study must deliver a three‑condition experimental dataset (LLM / Human / None), automated readability metrics computed against both source code and human docstring, a fully within‑subject human‑study data merge, and a complete statistical analysis (power analysis, one‑way ANOVA, correlation). Tasks are ordered to respect data flow and to produce an early end‑to‑end result on a small sample before scaling to the full dataset. T001 now also validates and logs dataset preparation; T010 conducts the user study; T006 performs standard ANOVA; T007 limits correlation to human‑reference metrics; additional tasks ensure reproducibility and environment validation.

---

- [X] T001 [US1] **Download & validate CodeSearchNet Python snippets (including validation pass)**
  *Implement* `src/data/download.py` that:
  - Downloads the verified CodeSearchNet Python parquet files via `hf_hub_download(repo_id="code_search_net", repo_type="dataset", filename="python/train-00000-of-00001.parquet")` with a 3‑attempt retry loop that **RAISES** on final failure (no synthetic fallback).
  - Parses using pandas/pyarrow with column‑tolerant mapping: accepts either `code`/`docstring` or `func_name`/`func_code_string`/`func_documentation_string`. If neither set matches, abort with an explicit error listing actual columns.
  - Takes a deterministic seeded subset (`PROJECT_SEED=42`) of **N = 500** snippets.
  - Validates JSON structure and docstring relevance (non‑empty, not a bare type signature, not boilerplate like `"""TODO"""`).
  - Writes **valid** records to `data/raw_snippets.jsonl` **and** to `data/validated_snippets.jsonl` (the latter is the filtered, validated output).
  - Writes excluded records with a `reason` field to `data/excluded_records.json`.
  - Records SHA‑256 checksums of the downloaded parquet files in `data/artifact_hashes.yaml`.
  - Emits a log file `data/dataset_preparation.log` summarising total records, valid count, excluded count, and compliance with SC‑006.
  *Verification*:
  – Script exits 0; checksum recorded.
  – `data/validated_snippets.jsonl` contains ≥ 150 valid snippets (target 500, ≥ 90 % processed).
  – `data/dataset_preparation.log` exists and reports the counts.
  – Pytest `src/tests/test_download.py` asserts correct column‑mapping for both possible schemas.

- [ ] T002 [US1] **Generate deterministic LLM comments via HuggingFace Inference API** <!-- FAILED-IN-EXECUTION: src/data/generate_comments.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/generate_comments.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/generate_comments.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/generate_comments.py exit=1 -->
  *Implement* `src/data/generate_comments.py` that:
  - Reads `data/validated_snippets.jsonl`.
  - Truncates each code snippet to ≤ 2048 tokens using `tiktoken` at the nearest newline; logs each truncation to `data/truncation_warnings.log`.
  - Calls **CodeLlama‑7B‑Instruct** (`codellama/CodeLlama-7b-Instruct-hf`) via the HF Inference API with **deterministic decoding** (`temperature=0.0`, `top_p=1.0`, fixed `seed=42`).
  - Implements ≤ 3 retries with exponential backoff (base 60 s).
  - Writes `data/llm_comments.jsonl` with fields `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (exactly `""`).
  *Verification*:
  – Every `snippet_id` in `validated_snippets.jsonl` appears exactly once in `llm_comments.jsonl`.
  – `llm_comment` is non‑empty; `no_comment` is `""`.
  – No snippet exceeds the token limit; truncation events are logged.

- [ ] T003 [US2] **Compute dual‑reference readability metrics for all comment conditions**
  *Implement* `src/data/metrics.py` that:
  - Consumes `data/llm_comments.jsonl`.
  - For each `snippet_id` creates three rows (conditions `llm`, `human`, `none`) in `data/readability_metrics.csv`.
  - Computes BLEU (nltk), ROUGE‑L (rouge_score), and Sentence‑BERT cosine similarity (`sentence-transformers/multi-qa-mpnet-base-dot-v1`, fallback to `all-MiniLM-L6-v2` on OOM) **against the source code** and **against the human docstring** for `llm` and `human` conditions.
  - Normalises all scores to [0, 1]; for `none` rows sets metric fields to `null`, `Comment_Length = 0`, `Flesch_Kincaid = 0`.
  - Records additional length metrics (`Comment_Length`, `Flesch_Kincaid`).
  - Processes in batches to stay ≤ 7 GB RAM and ≤ 30 min CPU (SC‑005).
  *Verification*:
  – Each `snippet_id` appears three times with correct `condition` values.
  – Metric fields are floats in [0, 1] or `null` for `none`.
  – `src/tests/test_metrics.py` validates metric values on fixed fixtures (tolerance 0.001) and that identical strings yield 1.0.

- [ ] T003a [US3] **Validate environment and recruitment tools**
  *Implement* `src/utils/validate_environment.py` that:
  - Verifies required packages import.
  - Checks RAM/disk headroom (≤ 7 GB usage) using `psutil`.
  - Validates HF token presence and ability to query the HF API.
  - Confirms Prolific API reachability (real authenticated GET).
  - Checks that the pre‑existing `data/consent_form.pdf` loads without error.
  - Emits a boolean `success` flag and writes `data/recruitment_validation.log` detailing each check.
  *Verification*:
  – Returns `success=True` with no errors when environment is ready; `success=False` aborts the study (SC‑007).
  – Log records each check outcome.

- [ ] T010 [US3] **Conduct the within‑subject user study**
  *Implement* `src/data/conduct_user_study.py` that:
  - Uses the Prolific API to create a study where **each participant evaluates every selected snippet under all three comment conditions** (fully within‑subject design, satisfying FR‑008).
  - Presents snippets in a counter‑balanced order to eliminate order effects.
  - Records task completion time, binary accuracy, and a 1‑5 Likert helpfulness rating.
  - Stores results in `data/human_study_responses.csv` with columns `participant_id`, `snippet_id`, `condition`, `completion_time_sec`, `accuracy`, `subjective_helpfulness`.
  - Fails loudly if the study cannot be launched or if required assets are missing.
  *Verification*:
  – CSV contains three rows per participant‑snippet (one per condition).
  – All fields are non‑null and conform to `contracts/dataset.schema.yaml`.
  – A pytest `test_user_study.py` (not shown) checks CSV schema compliance.

- [ ] T004 [US3] **Merge human‑study data with comments and metrics (within‑subject)**
  *Implement* `src/data/prepare.py` that:
  - Loads `data/human_study_responses.csv`, `data/llm_comments.jsonl`, and `data/readability_metrics.csv`.
  - Verifies the **within‑subject design**: each participant has exactly three rows per snippet, covering all conditions, and across participants each snippet appears equally in all conditions.
  - Merges on `snippet_id` + `condition` to produce `data/merged_dataset.csv` conforming to `contracts/dataset.schema.yaml`.
  - aborts if the design check fails or if any required file is missing.
  *Verification*:
  – Every row contains all required fields; no `null` in human‑evaluation columns.
  – Metric columns are `null` only for `condition = "none"`.
  – Design balance check passes.

- [ ] T005 [US3] **Power analysis (ANOVA)**
  *Implement* in `src/data/analysis.py` a power analysis using `statsmodels.stats.power.FTestAnovaPower` with effect size f = 0.25, α = 0.05. Compare required per‑group N with actual recruited N and write `results/power_report.txt` containing `effect_size`, `alpha`, `required_sample_per_group`, `achieved_power`, and a plain‑text statement of whether the target power (≥ 0.80) is met (FR‑007, SC‑009).
  *Verification*:
  – Report includes all four numeric fields and the target statement.
  – If `achieved_power < 0.80`, a limitation note is present.

- [ ] T006 [US3] **One‑way ANOVA on completion time and accuracy**
  *Implement* in `src/data/analysis.py`:
  - For **completion time**: ordinary least‑squares ANOVA (`statsmodels.formula.api.ols`) with factor `condition`; compute F, p‑value, df_between, df_within; set `reject_null` based on α = 0.05.
  - For **accuracy**: apply arcsine‑sqrt transformation to the binary accuracy values, then run the same OLS ANOVA pipeline.
  - Output `results/analysis_results.json` containing `anova_time` and `anova_accuracy` objects matching `contracts/analysis.schema.yaml`.
  *Verification*:
  – JSON validates against the schema.
  – `p_value` fields are floats in [0, 1]; `reject_null` correctly reflects p < 0.05.
  – Synthetic test fixture asserts both p < 0.05 **and** achieved power ≥ 0.80 (see executability‑33a6aaa4).

- [ ] T007 [US3] **Correlation analysis (human‑reference metrics only)**
  *Implement* in `src/data/analysis.py` that:
  - Aggregates `data/merged_dataset.csv` per `snippet_id` (mean completion time, mean accuracy, mean subjective helpfulness) **only for the LLM condition**.
  - Computes Pearson correlations between each of the four metrics (`BLEU`, `ROUGE_L`, `Semantic_Similarity`, `Comment_Length`) **using the human‑reference scores** and each outcome (`completion_time_sec`, `accuracy`, `subjective_helpfulness`).
  - Applies Bonferroni correction for 12 tests (α = 0.05/12).
  - Appends a `correlation_metrics` array to `results/analysis_results.json` with fields `metric`, `outcome`, `pearson_r`, `p_value_raw`, `p_value_corrected` (exactly one entry per metric‑outcome pair, matching the schema).
  *Verification*:
  – All 12 combinations appear once.
  – Corrected p‑values are reported; non‑significant results are included honestly.

- [ ] T008 **Generate figures and results summary**
  *Create*:
  - `figures/fig_time_by_condition.pdf` (box‑plot of completion time by condition).
  - `figures/fig_corr_heatmap.png` (heat‑map of the correlation matrix).
  - `results/results_summary.md` that cites exact rows in `merged_dataset.csv`, summarizes power, ANOVA, and correlation findings, and explicitly notes any limitations (e.g., power shortfall, truncation events, metric proxy status).
  *Verification*:
  – Figures open without error and have labeled axes.
  – Summary references each result artifact and reports negative findings honestly.

- [ ] T009 **Contract validation, feasibility measurement, and reproducible quickstart**
  *Add*:
  - `src/tests/test_contracts.py` that validates `data/merged_dataset.csv` and `results/analysis_results.json` against their respective schemas.
  - Runtime measurement (peak RSS, wall‑clock) using `psutil`; write `results/feasibility_report.txt` asserting RAM ≤ 7 GB and metric stage ≤ 30 min (SC‑010).
  - Verify the presence of a pinned `requirements.txt` at the project root; fail if missing (addresses reproducibility requirement).
  - Update `quickstart.md` with commands for the early 10‑snippet checkpoint and the full pipeline, and include a handoff note for the paper stage.
  *Verification*:
  – `pytest -q` passes all tests.
  – Feasibility report meets limits.
  – `quickstart.md` reproduces the full run from scratch.

- [ ] T012 **Verify pinned requirements file for reproducibility**
  *Implement* `src/utils/verify_requirements.py` that:
  - Checks that `requirements.txt` exists at the repository root and that it is non‑empty.
  - Optionally verifies that the file matches a known hash stored in `data/artifact_hashes.yaml`.
  - Emits a boolean flag and logs to `data/requirements_check.log`.
  *Verification*:
  – Pipeline aborts if the requirements file is missing or empty, ensuring compliance with Constitution Principle I.
