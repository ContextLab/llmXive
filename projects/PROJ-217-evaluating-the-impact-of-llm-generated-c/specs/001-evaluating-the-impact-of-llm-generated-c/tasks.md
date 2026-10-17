# Tasks: Evaluating the Impact of LLM‑Generated Code Comments on Code Readability

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001‑evaluating‑the‑impact‑of‑llm‑generated‑c/contracts/`.

The study must deliver a three‑condition experimental dataset, automated readability metrics, a human‑study data merge, and a full statistical analysis (power analysis, one‑way ANOVA, correlation).  
The tasks below are ordered to respect data flow and to produce an early end‑to‑end result on a small sample before scaling to the full dataset.

---

- [ ] T001 [US1] **Download & validate CodeSearchNet Python snippets**   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  *Create* `data/raw_snippets.jsonl` containing `snippet_id`, `code`, and `human_comment`; write malformed records to `data/excluded_records.json`.  
  *Verification*:  
  – SHA‑256 checksums of the three source parquet files match the values recorded in `data/artifact_hashes.yaml`.  
  – At least 50 valid snippets are retained, each with non‑empty `code` and `human_comment`.  
  – `data/excluded_records.json` lists only records with a `reason` field (e.g., “invalid_docstring”).

- [ ] T002 [US1] **Generate LLM‑based comments via HuggingFace Inference API**  
  *Read* `data/raw_snippets.jsonl`, *write* `data/llm_comments.jsonl` with fields `snippet_id`, `code`, `human_comment`, `llm_comment`, `no_comment` (empty string). Implement 3‑attempt exponential back‑off (base = 60 s) and truncate any snippet longer than the model’s 1024‑token window, logging warnings to `logs/truncation_warnings.log`.  
  *Verification*:  
  – Every retained `snippet_id` appears once in `llm_comments.jsonl`.  
  – `llm_comment` is a non‑empty string; `no_comment` is exactly `""`.  
  – The script exits with an error if the API rate limit is exceeded after all retries.

- [ ] T003 [US2] **Compute readability metrics for all comment conditions**  
  *Consume* `data/llm_comments.jsonl` (which already contains the human and no‑comment variants) and produce `data/readability_metrics.csv` with columns `snippet_id`, `condition`, `BLEU`, `ROUGE_L`, `Semantic_Similarity`, `Comment_Length`, `Flesch_Kincaid`. Compute BLEU, ROUGE‑L, and Sentence‑BERT cosine similarity **for every condition** using the human docstring as the reference:  
  – `condition = "llm"`: compare `llm_comment` to `human_comment`.  
  – `condition = "human"`: compare `human_comment` to itself (score = 1.0 for BLEU & ROUGE‑L, similarity = 1.0).  
  – `condition = "none"`: set BLEU, ROUGE‑L, and Semantic_Similarity to 0.0.  
  Use Sentence‑BERT (fallback to `all‑MiniLM‑L6‑v2` if OOM). Normalize BLEU, ROUGE‑L, and similarity to the range [0, 1]. Also compute `Comment_Length` (character count) and `Flesch_Kincaid` readability for every comment variant (empty string yields 0 length and 0 readability).  
  *Verification*:  
  – All `snippet_id`s from `llm_comments.jsonl` appear three times (once per condition).  
  – The CSV includes a `condition` column with values `llm`, `human`, `none`.  
  – Primary scores are floats in [0, 1]; auxiliary metrics are populated for every row.

- [ ] T003a [US3] **Validate data collection environment and recruitment tools**  
  *Verify* the availability and functionality of the user study platform and the participant recruitment pipeline (e.g., checking API connectivity to the survey tool and verifying recruitment quotas) before the user study begins.  
  *Verification*:  
  – A validation log is produced confirming that the environment is ready and recruitment tools are operational.

- [ ] T004 [US3] **Integrate human‑study performance data**  
  *Load* the externally collected `data/human_study_responses.csv` (participants’ `completion_time_sec`, `accuracy`, `subjective_helpfulness`) and *merge* with `data/readability_metrics.csv` on `snippet_id` and `condition` to create `data/analysis_dataset.csv`. No synthetic metric filling is required because `readability_metrics.csv` already contains complete scores for all conditions.  
  *Verification*:  
  – Every row in `analysis_dataset.csv` contains the fields required by `dataset.schema.yaml`.  
  – No `null` values appear in `completion_time_sec`, `accuracy`, or `subjective_helpfulness`.  
  – Metric columns (`BLEU`, `ROUGE_L`, `Semantic_Similarity`) are populated for all rows (no `null`s), satisfying FR‑003.

- [ ] T005 [US3] **Perform power analysis**  
  *Using* `statsmodels.stats.power.FTestAnovaPower`, compute the required sample size per group for a target effect size f = 0.25, α = 0.05, and desired power ≥ 0.80. Compare with the actual recruited N per group and write `results/power_report.txt` summarizing `effect_size`, `alpha`, `required_sample_per_group`, `achieved_power`, and a note if power < 0.80.  
  *Verification*:  
  – The report contains all four numeric fields and a plain‑text statement of whether the achieved power meets the target.

- [ ] T006 [US3] **Run one‑way ANOVA on completion time**  
  *Transform* `completion_time_sec` as needed (e.g., log‑transform if skewed) and execute a one‑way ANOVA across the three conditions. Write results to `results/anova_time.json` with keys `F`, `p_value`, `df_between`, `df_within`.  
  *Verification*:  
  – The JSON file validates against `analysis.schema.yaml` under the `anova_time` object.  
  – `p_value` is a float between 0 and 1.

- [ ] T007 [US3] **Run one‑way ANOVA on accuracy**  
  *Apply* arcsine‑sqrt transformation to the binary `accuracy` column, perform ANOVA, and write `results/anova_accuracy.json` with the same schema fields as `anova_time`.  
  *Verification*:  
  – The file conforms to the `anova_accuracy` schema section.  

- [ ] T008 [US3] **Correlation analysis between LLM metrics and human outcomes**  
  *Compute* Pearson correlation coefficients between each LLM‑only metric (`BLEU`, `ROUGE_L`, `Semantic_Similarity`, `Comment_Length`) and each outcome (`completion_time_sec`, `accuracy`, `subjective_helpfulness`). Apply Bonferroni correction (α/4) and output `results/correlations.csv` with columns `metric`, `outcome`, `pearson_r`, `p_value_raw`, `p_value_corrected`.  
  *Verification*:  
  – Every combination listed in the schema’s `correlation_metrics` array appears exactly once.  
  – All `p_value_corrected` values are ≤ 0.05 *or* the file notes the lack of significance.

- [ ] T009 [P] **Generate figures and summary report**  
  *Create* `figures/fig_time.pdf` (box‑plot of completion time by condition) and `figures/fig_corr.png` (heat‑map of correlation coefficients). Write `results/results_summary.md` that:  
  – References specific rows in `analysis_dataset.csv`.  
  – Summarizes the power analysis, ANOVA outcomes, and correlation findings.  
  – Explicitly notes any limitation (e.g., power < 0.80).  
  *Verification*:  
  – Figures open without error and display the expected axes/labels.  
  – The markdown file contains at least one citation to each result artifact.

- [ ] T010 [P] **Contract validation & reproducible quickstart**  
  *Add* unit tests in `tests/contract/test_contracts.py` that load `analysis_dataset.csv`, `readability_metrics.csv`, and all JSON result files and validate them against the corresponding YAML schemas. Update `quickstart.md` with a single command (`python -m src.cli.run_pipeline --sample 10`) that runs the full pipeline on a 10‑snippet sample. Additionally, execute the full pipeline on the complete dataset and log the total wall‑clock runtime and peak RSS memory usage to `results/feasibility_report.txt`.  
  *Verification*:  
  – `pytest -q` passes with all contract tests.  
  – The quickstart command completes within 5 minutes.  
  – `results/feasibility_report.txt` confirms total runtime ≤ 30 min and peak RAM ≤ 7 GB for the full dataset.

- [ ] T011 [P] **Verify overall computational feasibility**  
  *Measure* peak RAM usage and total wall‑clock time of the full pipeline (using `psutil` or similar) and assert that RAM ≤ 7 GB and runtime ≤ 30 minutes. Record the measurements in `results/feasibility_report.txt` (if not already produced by T010).  
  *Verification*:  
  – The report contains explicit numeric values for RAM (in GB) and runtime (in minutes) and asserts they meet the limits.

---  

**Dependency mapping**

| Requirement | Satisfied by task(s) |
|-------------|----------------------|
| FR‑001 | T001 |
| FR‑002 | T002 |
| FR‑003 | T003, T004 |
| FR‑004 | T004 |
| FR‑005 | T006, T007 |
| FR‑006 | T003a |
| FR‑007 | T005 |
| SC‑001 | T004, T006, T007 |
| SC‑002 | T003 |
| SC‑003 | T008 |
| SC‑004 | T006, T007 |
| SC‑005 | T010, T011 |

All tasks are unchecked; the runner will execute them in the order shown, guaranteeing that each step’s inputs are produced by its predecessors.  