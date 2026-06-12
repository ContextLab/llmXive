---
action_items:
- id: 0834342c070a
  severity: science
  text: Report confidence intervals (95% CI) for all benchmark scores in Tables 1-3.
    Currently no variance measures are provided across runs.
- id: 59aec3d6f464
  severity: science
  text: Add statistical significance tests (paired t-test or bootstrap) comparing
    Audio-Interaction against key baselines. No p-values or significance markers exist.
- id: c5defc2ca6d5
  severity: science
  text: Clarify the number of independent training runs averaged for each reported
    score. Currently unclear if results are single-run or averaged.
- id: d787d8b88e75
  severity: science
  text: Apply multiple-comparison correction (e.g., Bonferroni) when claiming superiority
    across 8 benchmarks. Currently no correction is applied.
- id: c3427942c2a1
  severity: science
  text: Provide power analysis or justification for the 644-item Proactive-Sound-Bench
    sample size. No statistical basis for test set size is given.
- id: d2b911615fee
  severity: science
  text: The 2-hour real-world validation across 4 scenarios lacks variance reporting.
    Add scenario-level statistics with error bars.
artifact_hash: d722b827ffcc42ef33cad3308518a181a01c5d135cbbac51efaf0289e64033d0
artifact_path: projects/PROJ-666-https-arxiv-org-abs-2606-05121/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-12T10:56:13.452173Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

This review focuses exclusively on statistical analysis aspects of the manuscript.

**Critical Statistical Reporting Gaps:**

1. **No Confidence Intervals**: All benchmark results (MMAU, dialogue, ASR, S2TT, Proactive-Sound-Bench) report single-point estimates without confidence intervals or standard deviations. For example, Table 1 reports "58.15" on MMAU audio instruction but provides no measure of uncertainty. This makes it impossible to assess whether differences from baselines (e.g., 57.81 for Qwen2.5-Omni-3B) are statistically meaningful.

2. **No Statistical Significance Tests**: The paper claims superiority ("best", "surpasses") across multiple tables but never reports p-values or performs formal hypothesis testing. When claiming "Audio-Interaction reaches 61.2 on Single and 62.8 on Multi tiers" (Proactive-Sound-Bench), no statistical comparison against baselines is provided.

3. **Multiple-Comparisons Problem**: With 8 benchmarks and numerous baseline comparisons, the paper makes no correction for multiple hypothesis testing. This inflates Type I error rates for claims of superiority.

4. **Unclear Reproducibility**: The appendix states training occurred on 32× H100 GPUs over ~10 days, but does not specify: (a) number of independent runs averaged, (b) random seeds used, or (c) whether results are reproducible. For a 3B model with streaming training, variance across runs can be substantial.

5. **Sample Size Justification**: The Proactive-Sound-Bench contains 644 human-designed events, but no power analysis or statistical justification for this sample size is provided. The real-world validation uses only 2 hours of audio across 4 scenarios—insufficient for strong statistical claims about generalization.

6. **Error Analysis Statistics**: Appendix Section 6 reports error breakdowns (e.g., "60.2% of errors") but without confidence intervals on these proportions or specification of how many total predictions were analyzed per benchmark.

**Required Actions:**
- Add 95% confidence intervals to all quantitative tables
- Perform and report statistical significance tests for key comparisons
- Clarify the number of independent runs per reported score
- Apply multiple-comparison correction when making cross-benchmark claims
- Provide power analysis for benchmark sample sizes
- Report scenario-level variance for real-world validation results

Without these statistical rigor improvements, the quantitative claims cannot be properly evaluated for reliability.
