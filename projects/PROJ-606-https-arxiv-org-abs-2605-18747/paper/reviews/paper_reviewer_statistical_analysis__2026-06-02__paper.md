---
action_items:
- id: d7efe80bce2e
  severity: science
  text: "Survey lacks statistical rigor section. While citing percentages (16.9%,\
    \ 43.3% in \xA7Emerging Fields), no confidence intervals or sample sizes provided\
    \ for benchmark claims. Consider adding uncertainty quantification for reported\
    \ metrics from cited work."
- id: 64d5c54b618b
  severity: science
  text: "Multi-agent convergence claims (98%+ precision in QualityFlow, \xA74.2.1)\
    \ lack statistical significance testing. Recommend reporting variance, n-samples,\
    \ or bootstrapped confidence intervals for any comparative performance claims."
- id: 4d098849d6a3
  severity: science
  text: No reproducibility statement for any empirical claims. While this is a survey,
    cited benchmark results should include links to original evaluation code/data
    where available for verification.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T05:28:14.441591Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

**Statistical Analysis Review**

This survey paper organizes existing literature on code-as-agent harnesses but does not present original empirical experiments requiring statistical analysis. From a statistical review lens, the following observations apply:

**What Is Present:**
- The paper cites percentage-based metrics from external work (e.g., "LingmaAgent resolves 16.9% of issues autonomously" in §Emerging Fields; "98%+ precision/recall" for QualityFlow in §4.2.1).
- Tables summarize system characteristics without quantitative comparisons requiring statistical tests.

**Statistical Concerns:**

1. **Uncertainty Quantification Missing:** When citing performance metrics (e.g., 16.9%, 43.3% in §Emerging Fields), no confidence intervals, standard deviations, or sample sizes are provided. For survey papers making comparative claims, reporting uncertainty bounds strengthens credibility.

2. **No Statistical Significance Testing:** Claims about method superiority (e.g., QualityFlow's 98%+ precision) lack accompanying statistical significance tests or variance measures. While these are citations, the survey should contextualize whether differences between systems are statistically meaningful.

3. **Reproducibility Gaps:** No reproducibility statements for cited empirical claims. Survey readers cannot verify benchmark results without links to original evaluation code/data.

**Recommendations:**
- Add a "Statistical Rigor" subsection in Open Problems discussing uncertainty quantification for harness-level metrics
- Report sample sizes and confidence intervals when citing performance percentages
- Include a reproducibility checklist for cited empirical claims
- Consider meta-analysis of benchmark results across multiple papers with proper effect size reporting

Given this is a survey without original experiments, the statistical limitations are understandable but should be acknowledged as future work priorities.
