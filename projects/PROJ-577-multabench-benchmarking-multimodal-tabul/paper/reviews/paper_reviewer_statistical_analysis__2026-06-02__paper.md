---
action_items:
- id: d72f51263896
  severity: writing
  text: Specify CI calculation method (t-distribution for N=5 seeds) in Section 3.2
    and Figure captions.
- id: 0ffe63639f1d
  severity: science
  text: Add paired statistical tests (e.g., Wilcoxon) for TAR vs Frozen gains across
    datasets in Section 5.
- id: 97f3a6b65dac
  severity: writing
  text: Clarify if regression R^2 is on binned labels or original values in Appendix
    A.1.
- id: b55a3ff889a4
  severity: science
  text: Quantify selection bias impact in Discussion (Section 7) regarding curation
    pipeline.
artifact_hash: 6787a87df841d43fd2785f288cbdae2d1c09b5ec14bf84bfd0cf81559d785c80
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T11:16:09.036842Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis is generally robust but lacks specific details on uncertainty quantification and significance testing, which are critical for benchmarking claims.

1. **Confidence Intervals (CIs):** Figures 5, 6, and Table 3 report 95% CIs derived from 5 seeds. With $N=5$, the Student's t-distribution ($df=4$) is required rather than the normal approximation ($z=1.96$). Please explicitly state the formula used (e.g., `mean +/- t_crit * std/sqrt(N)`). Using $z$ with small $N$ underestimates uncertainty, potentially overstating significance.

2. **Statistical Significance:** While mean performance gains are reported (e.g., +0.022 AUC in Table 3), paired statistical tests across datasets are missing. Given the paired nature of the experiment (same datasets for TAR vs. Frozen), a Wilcoxon signed-rank test should be added to confirm gains are significant ($p < 0.05$) beyond random variance.

3. **Regression Metric Consistency:** Appendix A.1 states regression targets are discretized into 20 bins with a Cross-Entropy objective, yet Table 1 reports $R^2$. Clarify if $R^2$ is calculated on the binned labels or original continuous values. If on binned labels, note that this may underestimate performance on the original continuous task and affects comparability with baselines that use regression.

4. **Selection Bias:** The curation pipeline (Section 3.2) selects datasets specifically where TAR shows gains. This introduces selection bias, potentially inflating the reported average gain on MulTaBench. Acknowledge this limitation more quantitatively in the Discussion (Section 7). Ideally, report gains on a held-out set or rejected datasets to estimate the inflation.

Reproducibility is high due to code/data release, but the statistical methodology needs tightening to support the strong claims about TAR generalization.
