---
action_items:
- id: aa9febb46db4
  severity: science
  text: "Multiple comparisons across 10 models \xD7 multiple blocking conditions lack\
    \ correction (e.g., Bonferroni, FDR). Report adjusted p-values or confidence intervals\
    \ to control Type I error inflation."
- id: 2ee103f27d40
  severity: science
  text: Seed variability shows 20 pp accuracy swings (Figure seed_acc, Appendix E002).
    This exceeds reported CI widths (~2.94 pp). Re-run with more seeds or report seed-dependent
    variance explicitly.
- id: 365f2dab97e0
  severity: science
  text: No explicit hypothesis tests reported for model comparisons. Confidence intervals
    alone are insufficient; add paired tests (e.g., McNemar, bootstrap t-tests) with
    effect sizes.
- id: 860620e06d17
  severity: science
  text: Sample size (327 tasks) lacks power analysis justification. Explain why this
    size detects meaningful differences given observed variance.
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T21:33:42.507954Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

**Statistical Analysis Review**

The paper presents a benchmark with reasonable statistical practices in some areas but has notable gaps that affect claim validity.

**Strengths:**
- Appendix E002 reports 95% confidence intervals via non-parametric bootstrap (10,000 resamples), which is appropriate for accuracy metrics.
- Seed variability is acknowledged (Figure seed_acc), showing awareness of stochasticity.

**Critical Concerns:**

1. **Multiple Comparisons (Section 3, Appendix E002):** The paper evaluates 10 LLMs across default, blocked, and fine-grained blocking conditions. With ~30+ pairwise comparisons, uncorrected p-values inflate Type I error. No Bonferroni, Holm, or FDR correction is mentioned. This undermines claims about model ranking differences.

2. **Seed Variability vs. CI Width (Figure seed_acc, Appendix E002):** Reported seed variation reaches 20 percentage points for DeepSeek and Llama, yet bootstrap CIs average only 2.94 pp. This discrepancy suggests either (a) the 10,000 bootstrap resamples don't capture seed-level variance, or (b) the CI calculation assumes i.i.d. tasks when seed effects dominate. The 20 pp variation should be reported as part of uncertainty, not just mean accuracy.

3. **Missing Hypothesis Tests (Section 3, Error Analysis):** Error category distributions (Irrecoverable Drift, Weak Recovery, etc.) are compared descriptively across models without statistical testing. Are the 72.4% vs. 71.3% Irrecoverable Drift rates for GPT-5.4 vs. Gemini significantly different? Add chi-square or Fisher's exact tests with effect sizes.

4. **Sample Size Justification (Appendix E002):** The 327-task benchmark lacks power analysis. Given observed variance, what minimum effect size can be detected with 80% power? This is essential for interpreting null results (e.g., enforced exploration improving <5 pp).

5. **Reproducibility (Appendix E002):** Bootstrap code and seed lists should be released alongside the benchmark. The current description ("10,000 times") is insufficient for exact replication.

**Recommendations:**
- Add multiple-comparison correction for all model comparisons.
- Report seed-level variance separately from bootstrap CI.
- Include hypothesis tests with effect sizes for key claims.
- Provide power analysis or justify 327-task sample size.
- Release statistical analysis code for full reproducibility.
