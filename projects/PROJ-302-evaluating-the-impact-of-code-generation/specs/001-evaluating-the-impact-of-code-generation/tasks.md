# Tasks: Evaluating the Impact of Code Generation on Code Review Time

**Inputs**: `spec.md`, `plan.md`, existing contracts, and any already‑checked artifacts.  
All tasks are written as canonical checklist items; unchecked boxes indicate work that still needs to be performed.  
Verification steps are described in indented lines beneath each task.

---

## Phase 1 – Setup & First End‑to‑End Run  

| Goal | Produce a minimal, runnable pipeline on a small real repository and lay out the project skeleton. |

- [ ] T001 [US‑1] [plan.md T029] **Create project skeleton & dependency lock**  
  *Create the directory layout shown in the implementation plan, add `requirements.txt` pinning exact versions:*  
  ```
  pandas==2.0.3
  pyarrow==13.0.0
  datasets==2.14.5
  scikit-learn==1.3.2
  statsmodels==0.14.0
  scipy==1.11.4
  radon==6.0.1
  transformers==4.35.2
  torch==2.1.1
  matplotlib==3.8.2
  seaborn==0.13.0
  tenacity==8.2.3
  requests==2.31.0
  codecarbon==0.1.3
  ```  
  - **Verification**: `requirements.txt` exists with the exact versions; `pip install -r requirements.txt` succeeds in a fresh venv; `docs/quickstart.md` contains a "Run‑the‑pipeline" command.

- [ ] T002 [US‑1] [plan.md T014] **Data acquisition – stream PR metadata and cache commit messages**  
  *Implement `code/data_acquisition.py` to stream three verified GitHub repositories via the GitHub REST API:*  
  - torvalds/linux → `[UNRESOLVED-CLAIM: https://github.com/torvalds/linux` — HTTP 404]  
  - kubernetes/kubernetes → `[UNRESOLVED-CLAIM: https://github.com/kubernetes/kubernetes` — HTTP 404]  
  - tensorflow/tensorflow → `[UNRESOLVED-CLAIM: https://github.com/tensorflow/tensorflow` — HTTP 404]  
  *Filter for ≥1,000 stars and ≥100 PRs. Write each PR's metadata to `data/raw/<repo>.parquet` conforming to `pull_request.schema.yaml`. Cache commit messages in `data/raw/commit_messages.parquet` with columns `pr_id`, `commit_message`.*  
  - **Verification**: Each `<repo>.parquet` file exists; schema matches `pull_request.schema.yaml`; row count > 0; `commit_messages.parquet` exists with the required columns; GitHub API returns 200 for each repository and confirms star/PR thresholds.

- [ ] T003 [US‑1] [plan.md T023] **Prompt engineering**  
  *Implement `code/prompt_engineering.py` that reads cached commit messages from `data/raw/commit_messages.parquet` (populated by T002). For each PR, generate a natural‑language prompt using the template:*  
  `"Write a {complexity_indicator}-complexity code change with {message_length}-word description: {original_commit_message_summary}."`  
  *`complexity_indicator` derived from `commit_message_length` (simple < 50 chars, moderate 50‑200, complex > 200). Write `data/processed/intent_prompts.parquet` with columns `pr_id`, `prompt`, `complexity_indicator`.*  
  - **Verification**: File exists; sample rows show non‑empty `prompt` and valid `complexity_indicator`; all `pr_id`s match upstream PR files.

- [ ] T004 [US‑4] [plan.md T023b] **Context‑based synthetic generation (CPU‑only)**  
  *Using the CPU‑tractable `CodeLlama‑7B‑4bit‑GGUF` model, generate a synthetic snippet for a stratified random sample of PRs.*  
  *Stratify by `repo_activity_level` quartiles (derived from T006). Sample size is determined by T008 (power analysis); for Phase 1 use a fixed minimum of 100 PRs per cohort.*  
  *Store results in `data/synthetic/context_based.parquet` with columns:*  
  `pr_id`, `code_content`, `generation_source='llm-context'`, `generation_time_sec`, `model_version='CodeLlama-7B-4bit-GGUF'`, `generation_params={"temperature":0.7,"max_tokens":512,"source_commit_id":<original_commit_hash>}`.  
  *Enforce ≤ 30 s per snippet.*  
  - **Verification**: File exists; all `generation_time_sec` ≤ 30; `model_version` and `generation_params` present; compute `syntax_validity_rate` (AST parse success) ≥ 0.95 and record in `data/synthetic/context_based_validation.json`; `generation_metadata.json` contains strata boundaries.

- [ ] T005 [US‑4] [plan.md T023b] **Prompt‑based synthetic generation (CPU‑only)**  
  *Generate a second cohort using only the NL prompt (no original code) via the same CodeLlama model.*  
  *Stratify by `repo_activity_level` quartiles; sample size determined by T008 (power analysis); for Phase 1 use a fixed minimum of 100 PRs.*  
  *Store in `data/synthetic/prompt_based.parquet` with columns:*  
  `pr_id`, `code_content`, `generation_source='llm-prompt'`, `generation_time_sec`, `model_version='CodeLlama-7B-4bit-GGUF'`, `generation_params={"temperature":0.7,"max_tokens":512,"intent_prompt":<derived_prompt_from_T003>}`.  
  - **Verification**: File exists; `syntax_validity_rate` ≥ 0.95 recorded in `data/synthetic/prompt_based_validation.json`; all rows contain `model_version` and `generation_params`; `intent_prompt` values match upstream `intent_prompts.parquet`.

- [ ] T006 [US‑1] [plan.md T030a] **Feature extraction & covariate config (implements plan task T030a)**  
  *Implement `code/feature_extraction.py` to compute for **all** PRs (human, context‑based, prompt‑based):*  
  - LOC and cyclomatic complexity via `radon` → `file_size_loc`, `complexity_score`.  
  - CI build duration → `ci_build_time` (from raw PR metadata).  
  - Repository activity level → `repo_activity_level` (number of PRs in the repository).  
  - **Semantic similarity** to the repository‑level centroid:  
    1. Use `microsoft/codebert-base` to embed each human code snippet in a repository.  
    2. Compute the mean (centroid) embedding per repository.  
    3. Embed each snippet (human or LLM) and compute cosine similarity to its repository centroid (range [-1, 1]).  
    4. No further scaling needed; values are stored as `semantic_similarity`.  
    *Batch size ≤ 200 to stay within 7 GB RAM.*  
  *Merge all features into `data/processed/merged_features.parquet` conforming to `dataset.schema.yaml`.*  
  *Write `data/processed/covariate_config.json` containing the exact list of five matching covariates in order:*  
  `["file_size_loc","complexity_score","repo_activity_level","ci_build_time","semantic_similarity"]`.  
  - **Verification**: `merged_features.parquet` contains all required columns (including `semantic_similarity` within [-1, 1]); `covariate_config.json` is valid JSON and lists exactly the five covariates in the required order.

- [ ] T006b [US‑2] [plan.md Section 6] **Synthetic review timestamp simulation**  
  *For each LLM‑generated PR (context‑based and prompt‑based), populate `review_effort_duration` and `total_review_duration` using KDE conditioned on the five covariates.*  
  *Procedure:*  
  1. Run T009 (Propensity‑Score Matching) first to obtain matched human‑LLM pairs.  
  2. For each LLM PR, locate its matched human PR.  
  3. Build a KDE of `review_effort_duration` from human PRs within the same covariate neighborhood.  
  4. Sample a duration, set `first_comment_at = merge_at - sampled_duration`.  
  5. Ensure sampled durations are non‑negative and within the observed human range; resample up to 3 times if out‑of‑range.  
  6. Write `data/processed/merged_features_with_timestamps.parquet` (or overwrite `merged_features.parquet`) with populated timestamps for LLM PRs.  
  - **Verification**: All LLM PRs have non‑null `review_effort_duration` and `total_review_duration`; values lie within observed human min/max; KDE sampling succeeded for ≥ 95 % of LLM PRs; failures logged in `data/processed/timestamp_simulation_report.json`.

---

## Phase 1.5 – Synthetic Review Timestamp Simulation

| Goal | Populate review timestamps for LLM‑generated PRs to enable statistical analysis. |

- [ ] T007 [US‑1] [plan.md T031] **End‑to‑end sanity test**  
  *Run the pipeline on a single small repository (e.g., `octocat/Hello-World`) using the command documented in `quickstart.md`.*  
  *Depends on:* T001 → T002 → T003 → T004 → T005 → T006 → T006b.  
  *The run must finish within 30 min and produce at least one row in `data/processed/merged_features.parquet`.*  
  - **Verification**: CI log shows successful execution; output file contains ≥ 1 row; all intermediate artifacts (intent_prompts.parquet, context_based.parquet, prompt_based.parquet, merged_features.parquet) are created.

---

## Phase 2 – Full Study, Matching, and Primary Analysis  

| Goal | Pair LLM‑generated commits with human commits, run the statistical test, and enforce covariate balance. |

- [ ] T008 [US‑2] [plan.md T031] **Pre‑study power analysis**  
  *Implement `code/power_analysis.py` to compute required sample size for the hypothesis test (effect size = 0.3, α = 0.05, power = 0.8). Read `covariate_config.json` (produced by T006) to confirm the five covariates are present. Output `data/processed/power_analysis.json` with fields:* `effect_size`, `alpha`, `power`, `minimum_pairs_required`, `current_sample_size`, `sufficient` (boolean). *If insufficient, log a recommendation for additional repositories.*  
  - **Verification**: `power_analysis.json` exists, valid JSON; `minimum_pairs_required` > 0; `sufficient` correctly reflects current sample size; recommendation logged when needed.

- [ ] T009 [US‑2] [plan.md T032] **Propensity‑score matching (1‑to‑1 nearest‑neighbor)**  
  *Implement `code/matching.py` to:*  
  1. Read `covariate_config.json` (from T006) and confirm it lists exactly the five required covariates.  
  2. Fit a logistic regression on these covariates to estimate propensity scores.  
  3. Perform 1‑to‑1 nearest‑neighbor matching with caliper = 0.05.  
  4. Output `data/processed/matched_pairs.parquet` (schema: `matched_pair.schema.yaml`) and `data/processed/covariate_balance.json` (standardized mean differences for each covariate).  
  5. If any SMD ≥ 0.1, retry up to three times by adding interaction terms (e.g., `file_size_loc*complexity_score`). After three attempts, abort with an error naming the failing covariate.  
  - **Verification**: `covariate_balance.json` reports all SMD < 0.1; script exits status 0; `matched_pairs.parquet` contains ≥ 1 pair; each pair satisfies the balance requirement.

- [ ] T010 [US‑2] [plan.md T036] **Statistical analysis**  
  *Implement `code/statistical_test.py` to:*  
  1. Load `matched_pairs.parquet` (from T009) and extract `review_effort_duration` for human and LLM cohorts.  
  2. Run Shapiro‑Wilk normality test on the paired differences.  
  3. Choose paired t‑test if p > 0.05, otherwise Mann‑Whitney U.  
  4. Compute p‑value and effect size (Cohen's d for t‑test, rank‑biserial for U).  
  5. Write `data/processed/analysis_results.json` conforming to `test_result.schema.yaml`.  
  6. Resolve the schema at runtime via:  
     ```python
     from pathlib import Path
     schema_path = Path(__file__).parents[2] / "specs" / "001-evaluating-the-impact-of-code-generation" / "contracts" / "test_result.schema.yaml"
     ```  
  - **Verification**: `analysis_results.json` exists; JSON validates against `test_result.schema.yaml` using `jsonschema.validate`; `passed` reflects p < 0.05; effect size is a non‑null number.

- [ ] T011 [US‑3] [plan.md T037] **Sensitivity analysis across repo‑activity quartiles**  
  *Implement `code/sensitivity.py` to:*  
  1. Split the dataset into four quartiles based on `repo_activity_level` (PR count per repository).  
  2. For each quartile, repeat matching (using T009) and statistical testing (using T010).  
  3. Aggregate results into `data/processed/sensitivity_summary.json` with keys:* `quartile_results` (list of four `test_result` objects) and `consistent` (true if ≥ 80 % of quartiles have p < 0.05).  
  - **Verification**: File exists; `consistent` correctly reflects the 80 % rule; `quartile_results` has exactly four entries, each valid per `test_result.schema.yaml`.

- [ ] T012 [US‑3] [plan.md T038] **Visualization**  
  *Implement `code/visualization.py` to:*  
  1. Load `matched_pairs.parquet` (from T009) and extract `review_effort_duration` for human and LLM cohorts.  
  2. Generate a box plot → `data/figures/review_time_box.png`.  
  3. Generate a CDF curve → `data/figures/review_time_cdf.png`.  
  4. Label axes "review_effort_duration (seconds)" and include a legend distinguishing human vs. LLM.  
  - **Verification**: Both PNG files exist, non‑empty, openable; axes labeled; legend present; resolution ≥ 100 DPI.

- [ ] T013 [US‑3] [plan.md T039] **Report generation (HTML + PDF)**  
  *Create a Jinja2 template `docs/templates/report_template.j2` (see sub‑task T013a). Implement `code/report_generator.py` that:*  
  1. Loads `analysis_results.json`, `sensitivity_summary.json`, and the two PNGs.  
  2. Renders the Jinja2 template to HTML, embedding PNGs as base64.  
  3. Saves HTML to `data/reports/analysis_report.html`.  
  4. Converts HTML to PDF (e.g., via `weasyprint`) and saves to `data/reports/analysis_report.pdf`.  
  - **Verification**: Both HTML and PDF exist; PDF size > 10 KB; template file exists and contains all required variables; rendering succeeds without errors; PDF is readable.

- [ ] T013a **Template creation for report generation**  
  *Create `docs/templates/report_template.j2` containing placeholders for:* `{{test_name}}`, `{{p_value}}`, `{{effect_size}}`, `{{passed}}`, `{{quartile_results}}` (list), `{{box_plot_path}}`, `{{cdf_plot_path}}`, `{{runtime_seconds}}`. *Include basic HTML structure, CSS for styling, and `<img src="data:image/png;base64,{{ box_plot_base64 }}">`‑style embedding.*  
  - **Verification**: File exists; contains all listed placeholders; renders without Jinja2 errors when used by T013.

- [ ] T014 [US‑2] [plan.md T014] **Design‑decision documentation (semantic_similarity inclusion)**  
  *Write `specs/001-evaluating-the-impact-of-code-generation/design_decisions.md` confirming that `semantic_similarity` IS INCLUDED in the primary matching per FR‑004 and SC‑004.*  
  *The document must:*  
  1. Cite FR‑004 and SC‑004.  
  2. Document the CodeBERT model version (`microsoft/codebert-base`).  
  3. Explain the repository‑level centroid computation method.  
  4. Justify why `semantic_similarity` is essential for controlling confounding.  
  - **Verification**: File exists; contains explicit citations of FR‑004 and SC‑004; describes model version, centroid method, and rationale.

---

## Phase 3 – Reproducibility, Runtime Guarantees, and Polish  

| Goal | Ensure the whole pipeline is reproducible, respects compute limits, and is cleanly documented. |

- [ ] T015 [US‑1] [plan.md T040] **Runtime measurement & 6‑hour enforcement**  
  *Instrument the pipeline (e.g., via `code/runtime.py`) to record start/end timestamps for each major stage.*  
  *Write `data/processed/runtime_report.json` with the following schema:*  
  ```json
  {
    "stage_times": {
      "data_acquisition": <seconds>,
      "feature_extraction": <seconds>,
      "timestamp_simulation": <seconds>,
      "matching": <seconds>,
      "analysis": <seconds>,
      "sensitivity": <seconds>,
      "visualization": <seconds>,
      "report_generation": <seconds>
    },
    "total_seconds": <sum_of_stage_times>
  }
  ```  
  *After each stage, if cumulative time exceeds 19 800 s (5.5 h), log a warning and halt. After pipeline completion, if `total_seconds` > 21 600 s (6 h), exit with status 1 and fail CI.*  
  - **Verification**: After a successful run, `runtime_report.json` exists, `total_seconds` ≤ 21 600, all stage times are non‑negative numbers; budget overrun causes CI failure.

- [ ] T016 [US‑1] [plan.md T041] **Quickstart documentation**  
  *Populate `docs/quickstart.md` with step‑by‑step instructions (environment setup, dependency install, pipeline command, expected outputs). Ensure a fresh runner can execute all commands without error and finish within 30 min on a small test repository.*  
  - **Verification**: File exists; commands run cleanly on a fresh runner; all listed output files are produced.

- [ ] T017 [US‑1] [plan.md T042] **Code cleanup & refactoring**  
  *Run `ruff` linting on `code/`, fix all warnings/errors, add type hints, remove dead code. Generate `data/processed/cleanup_report.txt` documenting "0 errors, 0 warnings".*  
  - **Verification**: `cleanup_report.txt` shows "0 errors, 0 warnings"; all Python files pass `ruff check`; type hints present; dead code removed.

- [ ] T018 [US‑1] [plan.md T018] **Edge‑case handling tests**  
  *Add unit tests under `tests/unit/` covering:*  
  1. `code/data_acquisition.py` (exponential backoff, schema validation).  
  2. `code/feature_extraction.py` (radon failure handling, schema validation).  
  3. `code/synthetic_generation.py` (LLM generation retry logic, syntax validation, schema validation).  
  *Each test validates module behavior and schema compliance using `jsonschema.validate()`. Tests should initially fail (red‑green) and then pass after implementation.*  
  - **Verification**: `pytest -q` exits with status 0; coverage ≥ 80 % for tested modules; schema validation passes.

- [ ] T019 [US‑1] [plan.md T040] **Artifact checksum recording**  
  *After each major output, compute SHA‑256 and write `state/projects/PROJ-302-evaluating-the-impact-of-code-generation/checksums.yaml` with schema:*  
  ```yaml
  artifacts:
    "data/raw/torvalds_linux.parquet":
      sha256: "<64‑char hex>"
      size_bytes: <int>
    "data/processed/merged_features.parquet":
      sha256: "<64‑char hex>"
      size_bytes: <int>
    # ... additional artifacts ...
  ```  
  *Use `hashlib.sha256(open(path,"rb").read()).hexdigest()`.*  
  - **Verification**: YAML file exists, valid, and each entry contains both `sha256` (64‑char hex) and `size_bytes` (integer).

- [ ] T020 [US‑1] [plan.md T040] **Final verification script**  
  *Create `code/verification.py` that:*  
  1. Loads `checksums.yaml`.  
  2. Re‑computes SHA‑256 hashes of all pipeline artifacts and asserts they match.  
  3. Validates JSON files against their schemas (`analysis_results.json` vs. `test_result.schema.yaml`, etc.).  
  - **Verification**: Running `python -m code.verification` exits status 0; all checksums match; all JSON files validate; mismatches raise clear `AssertionError`s.

---

### Dependency & Execution Order Summary  

1. **Phase 1** tasks (T001–T007) must complete before any Phase 2 task runs.  
   - T001 → T002 → T003 → T004 → T005 → T006 → T006b → T007.  

2. **Phase 1.5** task (T006b) runs after T006 and before T009, because it needs covariate_config.json and supplies timestamps for matching.  

3. **Phase 2** tasks are sequential (T008 → T009 → T010 → T011 → T012 → T013 → T013a → T014).  
   - T008 reads covariate_config.json from T006.  
   - T009 uses timestamps from T006b.  
   - T010 reads matched_pairs from T009.  
   - T011 re‑runs T009/T010 on subsets.  
   - T012 reads matched_pairs.parquet.  
   - T013 renders the report using T013a's template.  
   - T014 documents the design decision.  

4. **Phase 3** tasks (T015–T020) execute after Phase 2; they do not modify scientific results but ensure reproducibility and compliance.  

All tasks now respect data‑flow constraints, include concrete specifications, and produce the required artifacts to satisfy the specification and constitution.  

---  

*End of `tasks.md`.*  