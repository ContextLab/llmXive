---
action_items:
- id: abe4a14f54c9
  severity: science
  text: No confidence intervals or standard errors reported for any quantitative claims
    (e.g., 58.3% vs 56.3% OLoRA-tail gain, majority voting accuracy). Add 95% CI for
    all reported means.
- id: 27228a8cb49d
  severity: science
  text: No statistical significance tests performed for key comparisons (OLoRA-tail
    vs LoRA, rank regimes, memory capacity thresholds). Add t-tests or bootstrap CIs
    with p-values.
- id: dbdb527ca334
  severity: science
  text: "Multiple comparisons across 9 ranks \xD7 4 batch sizes \xD7 6 seeds (216\
    \ runs) without correction. Report FDR-adjusted p-values or use Bonferroni correction\
    \ for all pairwise tests."
- id: d9038535967c
  severity: science
  text: "Majority voting regression (accuracy \u2248 0.386 + 0.0172 ln(k), R\xB2 \u2248\
    \ 0.888) lacks residual analysis, standard errors on coefficients, or model diagnostics.\
    \ Add regression diagnostics."
- id: 77b147377eda
  severity: science
  text: "Memory capacity ceiling claim (10\u207B\xB3 to 10\u207B\xB2 tokens/parameter)\
    \ has no uncertainty quantification. Provide confidence intervals on the capacity\
    \ threshold estimate."
- id: eb342bea2a83
  severity: science
  text: "Seed-level results (6 seeds) insufficient for reliable mean estimates; recommend\
    \ \u226530 seeds for low-rank regime or report bootstrapped CIs."
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T21:58:10.578475Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

This review focuses exclusively on statistical analysis quality. The paper contains extensive empirical data but lacks rigorous statistical treatment throughout.

**Critical Issues:**

1. **No Confidence Intervals**: All quantitative claims (OLoRA-tail 58.3% vs 56.3%, majority voting 0.3644→0.4867, memory capacity thresholds) report point estimates without 95% CIs or standard errors. This makes it impossible to assess whether observed differences exceed random variation.

2. **Missing Significance Tests**: The OLoRA-tail vs LoRA comparison (11.5 pp gain, Figure 4) shows error bars but no t-tests, permutation tests, or bootstrap p-values. Similarly, rank regime comparisons (ranks 16-32 vs ranks 1-4) lack formal hypothesis testing.

3. **Multiple Comparisons Problem**: With 216 runs across ranks, batch sizes, and seeds, plus additional experiments on OLoRA-tail, memory benchmarks, and majority voting, the paper performs dozens of comparisons without FDR/Bonferroni correction. This inflates Type I error rates.

4. **Regression Diagnostics Missing**: The majority voting fit (accuracy ≈ 0.386 + 0.0172 ln(k), R² ≈ 0.888) lacks residual analysis, standard errors on coefficients, or tests for linearity assumption violations.

5. **Insufficient Power for Low-Rank Claims**: Claims about rank-1 reliability are based on 6 seeds. For detecting seed-to-seed variance differences, ≥30 seeds are typically required for stable variance estimates.

6. **Memory Capacity Threshold Uncertainty**: The 10⁻³ to 10⁻² capacity boundary is stated as fact without confidence intervals around this transition region estimate.

**Recommendations:**
- Add 95% CIs (via bootstrapping or analytical methods) for all reported means
- Perform t-tests/ANOVA for pairwise comparisons with multiple-comparison correction
- Report regression diagnostics for the ln(k) fit
- Increase seed count for low-rank experiments or use Bayesian hierarchical models to borrow strength across configurations
- Quantify uncertainty on the memory capacity threshold estimate

These changes are necessary to support the paper's central claims about PEFT scaling regimes and adapter reliability.
