---
action_items:
- id: 7e3bc8ba22f6
  severity: writing
  text: "Table 2 reports single-point benchmark scores (e.g., '85.2' on MMLU Pro)\
    \ without any measure of uncertainty (SD, SE, or CI) or the number of seeds/runs\
    \ used. In ML, single-run reporting is insufficient to distinguish signal from\
    \ noise. Report mean \xB1 SD over \u22653 seeds or explicitly state the result\
    \ is from a single run and drop the implied precision."
- id: f64c418a9427
  severity: writing
  text: "Table 1 (Arena Elo) reports 95% CIs (e.g., '\xB1 8') for Gemma 4 models but\
    \ provides no methodology for their calculation (e.g., bootstrap, Bayesian inference)\
    \ or the number of pairwise comparisons used to derive them. Without this, the\
    \ intervals cannot be verified or interpreted correctly."
- id: 58f3bc87d41c
  severity: writing
  text: Section 5.2 claims Gemma 4 is 'significantly better' than Gemma 3 across benchmarks
    based on Table 2 point estimates. No statistical test (e.g., paired t-test, bootstrap)
    or p-values are reported to support this claim. Replace 'significantly better'
    with 'higher' or report the actual test statistics and p-values.
artifact_hash: 55958703b13d89f6f09bca63229fc87b11f6b4b47923a438bff5af617f4f5f53
artifact_path: projects/PROJ-1018-gemma-4-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T04:27:48.045078Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this technical report is largely descriptive, presenting point estimates for model performance without the necessary inferential machinery to support claims of superiority or stability.

**Missing Uncertainty Reporting:**
The most pervasive issue is the reporting of single-point estimates for benchmark results in **Table 2** (Static benchmarks) and **Table 3** (Vision benchmarks). For instance, the 31B model is reported as achieving "85.2" on MMLU Pro and "89.2" on AIME 2026. There is no indication of the number of random seeds used, nor is there any measure of variance (standard deviation, standard error, or confidence intervals). In the context of large language models, where performance can fluctuate based on initialization, sampling temperature, or data shuffling, a single number is statistically insufficient to claim a "leap in performance." The authors must either report mean ± SD over multiple seeds (standard practice) or explicitly state that these are single-run results, which would necessitate softening claims of statistical significance.

**Unsubstantiated Claims of Significance:**
In **Section 5.2**, the text states: "Gemma 4 31B is closest in size and significantly better across the board." The term "significantly" implies a statistical hypothesis test was performed. However, **Table 2** only provides raw scores. No p-values, test statistics, or effect sizes are reported to validate this claim. Without a formal test (e.g., a paired t-test across seeds or a bootstrap test), the word "significantly" is misleading. The authors should either run the appropriate tests and report the results or rephrase the claim to "higher performance" based on the observed point estimates.

**Ambiguous Confidence Intervals:**
**Table 1** (Arena Elo leaderboard) reports 95% confidence intervals (e.g., "± 8" for Gemma 4 31B). While this is a positive step, the methodology for deriving these intervals is absent. Elo ratings are typically derived from a Bradley-Terry model or similar pairwise comparison framework. The width of the CI depends heavily on the number of battles and the specific statistical model used. Without specifying the method (e.g., "95% CI derived from 10,000 bootstrap samples of the pairwise comparison matrix"), these intervals are not reproducible or verifiable.

**Recommendation:**
The paper requires a revision to the statistical reporting section. Specifically:
1.  Add standard deviations or confidence intervals to all benchmark tables (Tables 2, 3, 4, 5) based on multiple seeds.
2.  Remove the word "significantly" from claims unless accompanied by a reported p-value and test name.
3.  Add a brief methodological note in the caption of Table 1 explaining how the Elo confidence intervals were calculated.

These are reporting fixes (writing) that can be implemented if the raw per-seed data exists, or require re-running experiments (science) if the data was not collected. Given the scale of the models, it is highly likely the data exists but was omitted for brevity.
