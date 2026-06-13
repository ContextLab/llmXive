---
action_items:
- id: 801928f87371
  severity: science
  text: Correlation analysis (Table 3, Sec 5.2) lacks p-values and confidence intervals.
    With n=150 instances but correlations computed across explorers (likely <20),
    report 95% CIs for r and rho values to assess statistical significance of the
    claimed 'highest' correlations.
- id: 22165ae27ef7
  severity: science
  text: Multiple comparisons not addressed. Testing 10+ metrics (Table 4) without
    correction inflates Type I error. Apply Bonferroni or FDR correction when claiming
    any metric 'outperforms' others.
- id: b27954455057
  severity: science
  text: Degradation analysis (Fig 3, Sec 5.4) claims rate 'jumps' between alpha=50
    and alpha=75 but provides no statistical test. Report confidence intervals on
    resolve rates at each alpha level and p-values for pairwise comparisons.
- id: b286769628e9
  severity: science
  text: Aggregation method (Appendix A) states 'per-instance then averaged' but does
    not specify weighted vs. unweighted averaging or report variance across instances.
    Add instance-level variance metrics to support generalization claims.
artifact_hash: 4f74e000b69de2d67ea831b1e89044d5ab493f7912139c51fbf7fc4d4c2ada92
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T21:54:37.768313Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis methodology is generally sound but lacks critical rigor in several areas. I focus on statistical validity, uncertainty quantification, and reproducibility concerns.

**Correlation Analysis (Section 5.2, Table 3):** The claim that "Context Efficiency showed the highest Pearson correlation (r=0.950)" lacks statistical validation. With n=150 instances but correlations computed across explorers (likely <20 agents), the effective sample size for correlation testing is unclear. No p-values or 95% confidence intervals are reported. At n=150, r=0.950 is significant (p<0.001), but the unit of analysis (instances vs. explorers) must be explicitly stated. Similar concerns apply to Spearman rho=0.845 for Rec@100.

**Multiple Comparisons Problem:** Table 4 reports 10 metrics across 10+ explorers. When claiming "highest" or "strongest" metrics without multiple-comparisons correction, Type I error is inflated. For example, testing 10 metrics at alpha=0.05 yields expected 0.5 false positives by chance. Apply Bonferroni (alpha/10=0.005) or Benjamini-Hochberg FDR correction.

**Degradation Analysis (Section 5.4, Figure 3):** Claims "Resolve rate jumps between alpha=50 and alpha=75" without statistical evidence. Report 95% confidence intervals on resolve rates at each alpha level and p-values from chi-square or Fisher's exact tests for pairwise comparisons. The observed dip from alpha=0 to alpha=25 also requires significance testing.

**Variance and Aggregation:** Appendix states metrics are computed "per-instance then averaged" but does not report variance across instances (standard deviation, interquartile range). For generalization claims, instance-level variance is essential. Weighted vs. unweighted averaging should be specified, especially given the imbalanced language distribution (Python 64.5%, C++ 0.8%).

**Effect Size Reporting:** Claims like "Agentic explorers substantially outperform" lack effect size quantification. Report Cohen's d or similar metrics for performance differences between agent classes.

**Reproducibility:** Appendix mentions "artifact contains benchmark records, scripts" but does not specify random seeds, versioning, or exact computational setup for statistical analyses. Full reproducibility requires these details.
