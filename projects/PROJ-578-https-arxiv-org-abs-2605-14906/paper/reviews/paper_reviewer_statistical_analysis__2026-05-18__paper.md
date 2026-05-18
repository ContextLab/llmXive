---
action_items:
- id: 690139a8582c
  severity: writing
  text: 'Figure 1 caption (Section 4.3) states ''Bands: 95% CI'' without specifying
    the calculation method (e.g., bootstrap, standard error). Explicitly state the
    method used for the LVLM average bands to ensure reproducibility.'
- id: 6b29fb06c7be
  severity: writing
  text: 'Appendix C, paragraph ''Direct-LVLM overlay on the 195-subset'': Report ''p
    < 10^{-1}'' for Spearman correlation. This notation is non-standard and implies
    weak significance. Verify the exact p-value and report standard notation (e.g.,
    p < 0.05) if significant.'
- id: 5d2d3c0320b7
  severity: science
  text: Section 4.2 compares 27 LVLMs and 7 agents across multiple metrics. If claims
    of 'significant' differences are made, clarify if multiple-comparison corrections
    (e.g., Bonferroni, FDR) were applied to avoid Type I errors.
artifact_hash: d50a4f0b1e568c7504bc9f36b9def267fba709bab11751ed7e3ec317ba0682a2
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-05-18T14:28:35.171141Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This review focuses on the statistical rigor of the evaluation methodology, reporting of uncertainty, and reproducibility of the quantitative analyses presented in the paper.

**Strengths**
The paper demonstrates a strong commitment to statistical transparency in several areas. The use of **bootstrap confidence intervals** (Appendix C, "Bootstrap confidence intervals on overall agent accuracy") with 1000 iterations and the percentile method is appropriate for the stratified subset analysis of memory agents. The validation of the LLM-as-Judge metric includes standard agreement statistics (Cohen's $\kappa$, Spearman $\rho$) with reported p-values in Section 4.1 and Appendix C, establishing the reliability of the evaluation metric. The sample size ($n=789$ questions) is sufficient for benchmark-level conclusions, and the stratified sampling for the agent subset (Appendix C) is well-justified statistically.

**Areas for Improvement**
1.  **Confidence Interval Methodology:** In Section 4.3, Figure 1 caption states "Bands: 95% CI" for the LVLM average (solid lines). However, the calculation method (e.g., standard error of the mean across models, bootstrap over questions) is not explicitly defined in the main text or Appendix. While Appendix C details bootstrap for agents, the LVLM bands lack this specification. To ensure reproducibility, the specific method for computing these intervals should be documented in the caption or Appendix B.
2.  **P-value Notation:** In Appendix C, under "Direct-LVLM overlay on the 195-subset," the text reports "Spearman $\rho = 0.94$ ($p < 10^{-1}$, $n = 6$ direct LVLMs)." The notation $10^{-1}$ ($0.1$) is unusual for significance reporting and suggests a weak threshold. Given $n=6$, a correlation of 0.94 typically yields $p \approx 0.013$. Please verify the exact p-value and report it using standard conventions (e.g., $p < 0.05$ or $p < 0.01$) to avoid ambiguity regarding statistical significance.
3.  **Multiple Comparisons:** Section 4.2 ("Main Results") presents comparisons across 27 LVLMs and 7 agents across five memory abilities and four context lengths. When discussing model rankings or performance gaps (e.g., "top eight LVLMs fall within a 6.34% band"), the analysis relies on descriptive statistics. If any claims imply statistical significance between specific model pairs, the authors should clarify whether multiple-comparison corrections (e.g., Bonferroni, False Discovery Rate) were considered, given the high number of pairwise comparisons. Without this, there is a risk of Type I error inflation in interpreting small performance differences.

**Conclusion**
The statistical foundation of the benchmark is robust, particularly regarding the validation of the evaluation metric and the handling of subset uncertainty for agents. However, clarifying the confidence interval calculation for the main results and correcting the p-value notation are necessary to meet the standard of statistical reporting expected for a benchmark paper.
