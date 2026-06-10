---
action_items:
- id: 20de54d19d77
  severity: science
  text: "Main results table (tables/main-table.tex) reports accuracy gains as point\
    \ estimates without confidence intervals or standard errors. Provide 95% CIs for\
    \ all \u0394Acc values to enable assessment of statistical significance."
- id: 234c999640d6
  severity: science
  text: Multiple-comparisons issue across 12+ model-retriever combinations on BrowseComp-Plus
    plus 3 additional benchmarks. No correction (e.g., Bonferroni, FDR) is reported
    for the regime boundary claims. Add statistical testing framework.
- id: a9cd3f089c12
  severity: science
  text: Attention percentages (e.g., 53.7% reasoning vs 25.6% observations in Section
    5.3.1) lack uncertainty quantification. Report standard errors or confidence intervals
    from bootstrap across trajectories.
- id: f0e69ca58d2a
  severity: science
  text: Regression probe AUC values (Figure 5, Section 5.2) are reported without confidence
    intervals or statistical tests comparing AUCs across conditions. This weakens
    the separability claims.
artifact_hash: 0662f086c971957827b984215e812ef5eb19c982637f2c1511efa72d77075eda
artifact_path: projects/PROJ-652-https-arxiv-org-abs-2606-00408/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T07:43:05.360919Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

**Statistical Analysis Review**

This paper presents an empirical study of observation masking in search agents, but the statistical analysis lacks essential rigor for publication-quality claims.

**Main Results (Table 1, Section 5):** The accuracy gains (e.g., +11.7 pts for Qwen3.5-35B-A3B+AgentIR) are reported as point estimates without confidence intervals or standard errors. With 830 samples on BrowseComp-Plus, the margin of error should be quantifiable. The regime boundary claims (retriever bottleneck vs. CM optimum vs. model-saturated) depend on these differences being statistically distinguishable, but no hypothesis testing is reported.

**Multiple Comparisons:** The paper tests 12+ model-retriever combinations on BrowseComp-Plus alone, plus 3 additional benchmarks (GAIA, xBench-DeepSearch, BrowseComp-ZH). No multiple-comparisons correction (Bonferroni, FDR, or hierarchical testing) is applied. The "three regimes" narrative may reflect random variation across the tested conditions without proper statistical control.

**Attention Analysis (Section 5.3.1):** Claims like "Reasoning captures 53.7% of attention vs. 25.6% for observations" lack uncertainty quantification. These percentages should be reported with standard errors or confidence intervals derived from bootstrap sampling across the 150 trajectories mentioned in Appendix H.1.

**Regression Probe (Section 5.2, Figure 5):** The AUC values for CM-rescue separability (e.g., 0.74 for GPT-OSS-120B+AgentIR) are reported without confidence intervals. AUC comparisons across conditions require statistical testing (e.g., DeLong's test) to support claims about separability differences.

**Ablation Studies (Table 3):** The scaffold design ablations show percentage differences (e.g., 18.60% vs. 22.61%) but no statistical significance testing or confidence intervals.

**Reproducibility:** While code is released, the statistical analysis pipeline (exact regression specifications, random seeds for trajectory sampling, bootstrap procedures) is not fully documented in the appendices.

**Recommendations:** Add confidence intervals to all reported metrics, apply multiple-comparisons correction for regime claims, provide statistical tests for attention and AUC differences, and document the statistical analysis pipeline in detail.
