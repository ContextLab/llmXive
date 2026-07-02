---
action_items:
- id: d281b2247e36
  severity: science
  text: The benchmark size (N=200) is insufficient for robust statistical inference
    across 9 sub-domains and 3 modalities. With ~22 samples per sub-domain, the standard
    error for mean utility is high. Report confidence intervals (e.g., 95% CI via
    bootstrapping) for all main results in Table 1 and Figure 1 to quantify uncertainty.
- id: ebf6d41efca9
  severity: science
  text: The paper claims 'statistically significant' improvements (e.g., 6.6% utility
    gain) but provides no hypothesis testing results (p-values, effect sizes, or power
    analysis). Explicitly state the statistical test used (e.g., paired t-test, Wilcoxon
    signed-rank) and report p-values for all key comparisons against baselines.
- id: 90b42e9eb681
  severity: science
  text: The utility metric combines exact match, numeric error, and lexical similarity
    (Appendix Eq 1-3). The aggregation weights (alpha=0.6, beta=0.4) and the cap (tau=0.8)
    are arbitrary. Provide a sensitivity analysis showing how results change if these
    hyperparameters are varied, or justify them with a validation study.
- id: 6aeac0a5cdb6
  severity: science
  text: The benchmark composition (Table 1 in Appendix) shows uneven sample counts
    per sub-domain (15-28). The reported 'mean utility' is an unweighted average.
    Clarify if this is appropriate given the imbalance, or provide a weighted average
    based on domain prevalence to avoid bias.
artifact_hash: 6f6f16bf33fe17a682df44afbf900ee0d80c1586f03954b67f158a9d54f94900
artifact_path: projects/PROJ-573-https-arxiv-org-abs-2604-27351/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:39:48.142978Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is currently insufficient to support the strong claims of performance improvement and efficiency gains. While the experimental setup is well-described, the lack of uncertainty quantification and formal hypothesis testing is a critical gap.

First, the benchmark size (N=200 total, ~22 per sub-domain) is small for drawing robust statistical conclusions, especially when stratifying by domain and modality. The reported mean utilities (e.g., 0.6558 for EywaAgent) are point estimates without any measure of dispersion. The authors must report confidence intervals (e.g., 95% CI via bootstrapping over the 200 samples) for all primary metrics in Table 1 and Figure 1. Without this, it is impossible to determine if the observed differences (e.g., the 6.6% gain over the baseline) are statistically significant or merely due to random variation in the small sample.

Second, the paper makes claims of "improvement" and "outperforming" baselines but does not perform any statistical hypothesis testing. For every comparison in Table 1 (e.g., EywaAgent vs. Single-LLM-Agent), the authors should report the results of an appropriate statistical test (e.g., paired t-test or Wilcoxon signed-rank test, depending on the distribution of the utility scores) along with p-values and effect sizes (e.g., Cohen's d). The current text implies significance without evidence.

Third, the construction of the unified utility score involves several arbitrary choices (Appendix, Section "Metrics"). The weights $\alpha=0.6$ and $\beta=0.4$ for the lexical fallback, and the cap $\tau=0.8$, are not justified. A sensitivity analysis is required to demonstrate that the main conclusions (e.g., Eywa's superiority) are robust to reasonable variations in these hyperparameters. If the ranking of methods changes significantly with different weights, the claims are not robust.

Finally, the unweighted mean utility across sub-domains with unequal sample sizes (15 to 28 samples per sub-domain, see Appendix Table 1) may introduce bias. The authors should clarify if a weighted average (weighted by the number of samples in each sub-domain) was considered or if the unweighted mean is justified by the experimental design. If the latter, a justification is needed.

In summary, the paper needs to move from reporting point estimates to reporting statistical estimates with uncertainty bounds and formal significance testing to validate its claims.
