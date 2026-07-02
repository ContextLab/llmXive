---
action_items:
- id: 6da69de8f1e1
  severity: science
  text: The paper reports p-values (e.g., p < 0.0001 for variance decomposition) but
    does not specify the statistical test used (e.g., Levene's, F-test) or the distributional
    assumptions. Given the non-normal nature of pass/fail metrics, clarify the test
    statistic and validity of the p-values.
- id: 2cba64856012
  severity: science
  text: Multiple comparisons are performed across 12 systems and 6+ metrics without
    correction (e.g., Bonferroni, Holm). With ~72+ pairwise tests implied, the risk
    of Type I error is high. Report adjusted p-values or justify the lack of correction.
- id: 4707ab51bea2
  severity: science
  text: "Confidence intervals are reported as '\xB1' standard deviations (e.g., 0.207\
    \ \xB1 0.041) in Table 1, but the text and figure captions refer to '95% percentile\
    \ bootstrap intervals'. Standard deviation is not a confidence interval. Explicitly\
    \ label these as SD or recompute as 95% CIs for consistency."
- id: 13148fc7b6e5
  severity: science
  text: The correlation claim (Pearson r = 0.93, p = 0.002) between transcription
    accuracy and task completion is based on n=7 systems (cascade only). This sample
    size is insufficient for robust correlation inference. Report the exact test used
    and consider non-parametric alternatives (Spearman) given the small N.
artifact_hash: 9779db764c5e6d634d1311a56a0ec38a708da09d28018889a272cb266ef418fe
artifact_path: projects/PROJ-574-eva-bench-a-new-end-to-end-framework-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:40:26.031552Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in EVA-Bench is ambitious but lacks necessary rigor in reporting and inference. While the sample size of trials (~12,780) is large, the unit of analysis for many claims is the system (n=12) or architecture class (n=3), which severely limits statistical power for comparative claims.

First, the reporting of uncertainty is inconsistent. Table 1 presents metrics as "Mean ± SD" (e.g., 0.207 ± 0.041), yet the text and Figure captions describe these as "95% percentile bootstrap intervals." Standard deviation and confidence intervals are distinct statistical concepts; conflating them misrepresents the precision of the estimates. The authors must either relabel the table columns as "Mean (SD)" or recompute the values as 95% CIs and update the table accordingly.

Second, the paper performs extensive hypothesis testing without addressing the multiple comparisons problem. With 12 systems evaluated across multiple metrics (EVA-A, EVA-X, and sub-metrics), the number of pairwise comparisons is substantial. The claim that "81% [of turn-taking metrics] show significant degradation" (Section 4.3) implies a large number of t-tests or ANOVAs were run. Without correction (e.g., Bonferroni, Benjamini-Hochberg), the reported p-values (e.g., p < 0.0001 in Section 4.2) are likely inflated. The authors should apply a correction method and report adjusted p-values, or explicitly state that the analysis is exploratory.

Third, the correlation analysis in Section 4.4 (Pearson r = 0.93, p = 0.002) is based on only 7 data points (the cascade systems). With n=7, the degrees of freedom are too low to robustly support a parametric correlation claim, especially given the potential for outliers. The authors should report the exact test used, consider a non-parametric alternative like Spearman’s rank correlation, and acknowledge the limited power of this specific analysis.

Finally, the variance decomposition claim ("Trial stochasticity is the dominant variance source... p < 0.0001") lacks methodological detail. The specific statistical test (e.g., F-test for variances, Levene's test) and the model used to partition variance (e.g., mixed-effects model) are not described. Given the binary nature of "pass" metrics, standard ANOVA assumptions may be violated. A brief description of the statistical model and assumptions is required to validate this claim.
