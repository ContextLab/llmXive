---
action_items:
- id: f0c4fde4a601
  severity: science
  text: "The statistical reporting in Table 1 (Section 5.2) is inconsistent. While\
    \ the LLM-Judge (J) scores include standard deviations (e.g., 75.17 \xB1 0.33),\
    \ the F1 scores are reported as single point estimates without any measure of\
    \ variance or confidence intervals. Given that the experiments are run three times\
    \ (Appendix A.4), F1 standard deviations must be reported to allow for statistical\
    \ significance testing between MRAgent and baselines."
- id: 946f0586fffc
  severity: science
  text: The claim of 'significant improvements' (Abstract, Section 5.2) lacks statistical
    validation. No hypothesis tests (e.g., paired t-tests, Wilcoxon signed-rank tests)
    or confidence intervals are provided to demonstrate that the observed performance
    gaps (e.g., 23% relative gain) are statistically significant rather than due to
    random variance in the LLM judge or sampling.
- id: a3dfa645219a
  severity: science
  text: The ablation study (Figure 3, Section 5.4) and multi-turn analysis (Figure
    4, Section 5.5) present performance trends but omit error bars or confidence intervals.
    Without these, it is impossible to determine if the observed differences between
    structural variants (CE vs. CTE vs. CTC) or across reasoning turns are statistically
    distinguishable.
- id: 8132aaac2d50
  severity: science
  text: The cost analysis in Table 2 (Section 5.3) reports single values for token
    consumption and runtime. Given the iterative nature of the active reconstruction
    process, these metrics likely have high variance depending on the specific query
    complexity and the number of turns taken. Reporting mean and standard deviation
    (or at least min/max) is necessary to validate the claim of 'substantially reducing'
    cost.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:27:29.787446Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis in the experimental section is insufficient to support the paper's claims of "significant improvements" and "substantially reducing" costs.

First, the reporting of results in **Table 1 (Section 5.2)** is inconsistent. While the LLM-Judge scores include standard deviations (e.g., $75.17 \pm 0.33$), the F1 scores are presented as single point estimates. Since the authors state in **Appendix A.4** that "Each method is evaluated three independent times," the F1 scores must also include standard deviations or confidence intervals. Without variance estimates for F1, it is impossible to assess the stability of the model or perform statistical significance tests against baselines.

Second, the paper repeatedly claims "significant improvements" (Abstract, Section 5.2) but provides no statistical evidence. There are no hypothesis tests (e.g., paired t-tests or Wilcoxon signed-rank tests) reported to determine if the observed gains (e.g., the 23% relative gain in J score) are statistically significant. Given the stochastic nature of LLMs and the small sample size (N=3 runs), the observed differences could easily be due to random variance. The authors must perform and report statistical significance tests for all primary comparisons.

Third, the **ablation study (Figure 3, Section 5.4)** and the **multi-turn reasoning analysis (Figure 4, Section 5.5)** lack error bars or confidence intervals. The visual trends suggest that adding tags or increasing reasoning turns improves performance, but without error bars, it is unclear if the differences between the "CE" and "CTC" variants, or between 1-turn and 3-turn reasoning, are statistically distinguishable.

Finally, the **cost analysis (Table 2, Section 5.3)** reports single values for token consumption and runtime. Since the active reconstruction process is adaptive, the number of turns and tokens consumed will vary significantly across queries. Reporting only the mean (or a single value) without variance (standard deviation or range) makes the claim of "substantially reducing" cost difficult to verify statistically. The authors should report the distribution of costs (mean ± std) to validate the efficiency claims.
