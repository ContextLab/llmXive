# Research: Evaluating the Impact of Code Generation on Code Review Burden

## Dataset Strategy

| Dataset | Source URL (verified) | Loader | Key Variables Needed |
|---------|-----------------------|--------|----------------------|
| PR‑v2‑sample | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | `datasets.load_dataset(..., data_files=..., split="train")` (streaming optional) | `pr_id`, `repo_name`, `created_at`, `merged_at`, `additions`, `deletions`, `comment_count`, `commit_message`, `diff_text`, `file_headers`, `labels`, `first_comment_timestamp` |
| Authors‑merged‑model‑prs | https://huggingface.co/datasets/davanstrien/authors_merged_model_prs/resolve/main/data/train-00000-of-00001-d32a63c5798549f1.parquet | same as above | same as above |
| Authors‑merged‑dataset‑prs | https://huggingface.co/datasets/davanstrien/authors_merged_dataset_prs/resolve/main/data/train-00000-of-00001-d5c709e857d2ca0b.parquet | same as above | same as above |

All three files are concatenated into a single DataFrame (`data/raw/combined_prs.parquet`). Checksums are verified on download (SHA‑256 stored in `data/checksums.txt`). No other data sources are used.

## Methodological Rationale

| Decision | Rationale | CPU/GPU |
|----------|-----------|---------|
| Use open HuggingFace parquet files instead of live GitHub API calls | Guarantees reproducible, rate‑limit‑free access; dataset contains the required provenance fields. | CPU |
| Classification precedence (file‑header > diff pattern > commit keyword) | Mirrors FR‑002 and the constitution’s Provenance Rigor principle. | CPU |
| Mixed‑effects model with `repo_name` random intercept **and fixed effects** for PR size, author experience, repo popularity | Addresses confounding (methodology‑d576283a) and improves estimate validity. | CPU (statsmodels) |
| Bonferroni correction across 5 primary metrics | Satisfies the multiplicity control described in the assumptions. | CPU |
| Power analysis after data collection (using `statsmodels.stats.power.TTestIndPower`) | Required by the assumptions; if power < 0.8, the report will flag the limitation. | CPU |
| Sensitivity analysis on IQR thresholds and comment‑filter relaxation | Directly implements FR‑006, FR‑014, and SC‑003. | CPU |
| Cohen’s κ on a representative sample of manual labels per group | Meets FR‑007 and SC‑001. | CPU |
| **Observational framing**: All findings are reported as **associational differences**, not causal effects. | Aligns with methodology‑0489c1c8 and the study’s observational nature. | CPU |
| Issue severity treated as **secondary exploratory** metric rather than primary burden indicator | Addresses methodology‑81094217; primary burden is captured by review_active_seconds and comment_density. | CPU |
| No GPU‑required components are present; all statistical and data‑processing steps run comfortably on the free‑tier runner. | – | CPU |

## Statistical Validation Discipline

1. **Normality** – Shapiro‑Wilk (α = 0.05). If any primary metric fails, default to Mann‑Whitney U.  
2. **Primary Tests** –  
   - `review_active_seconds` → t‑test or Mann‑Whitney U (effect size: Cohen’s d or rank‑biserial).  
   - `comment_density` → same.  
   - `issue_severity` → chi‑square test (Cramér’s V reported; secondary).  
3. **Effect Size Benchmarks** – Small = 0.2, Medium = 0.5, Large = 0.8 (SC‑004).  
4. **Multiple Comparison** – Bonferroni‑adjusted α = 0.05 / 5 = 0.01.  
5. **Null‑Result Statement** – Automatically inserted when `p ≥ α_corrected`. (FR‑011)  
6. **Robustness Flag** – If any metric’s significance flips across IQR = {1.0, 1.5, 2.0} or comment‑filter relaxation, the “Low Robustness” flag is set (SC‑003).  

## Validation & Sensitivity

- **Inter‑rater agreement** – Cohen’s κ computed with `sklearn.metrics.cohen_kappa_score`. κ ≥ 0.6 required (SC‑001).  
- **Outlier thresholds** – IQR multipliers 1.0, 1.5, 2.0 applied separately; results stored in `data/results/sensitivity_*.csv`.  
- **Comment‑filter sensitivity** – Re‑run the full pipeline with `comment_count ≥ 0`; compare effect sizes and p‑values.  

## Resource Monitoring

During each script run, `psutil` records peak RAM and CPU time. If RAM > 6 GB or CPU time > 5 h, the pipeline aborts with a clear log entry, satisfying SC‑005.

---


## Power Analysis Detail (added for completeness)

Assuming a medium effect size (Cohen’s d = 0.5), α = 0.05, and desired power = 0.80, `statsmodels.stats.power.TTestIndPower().solve_power(effect_size=0.5, alpha=0.05, power=0.8)` yields a required sample size of **≈64 per group**. The pipeline will check that both LLM‑generated and Human‑written groups meet this threshold before proceeding; otherwise a power‑limitation warning is emitted in the final report.
