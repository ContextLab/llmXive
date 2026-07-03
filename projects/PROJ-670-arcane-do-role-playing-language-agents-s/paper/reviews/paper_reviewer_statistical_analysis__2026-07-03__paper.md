---
action_items:
- id: 561ace4dc22e
  severity: science
  text: Report confidence intervals or standard errors for all mean scores in Tables
    1 and 2. The current presentation of single-point estimates (e.g., 62.4 vs 57.7)
    lacks a measure of uncertainty, making it impossible to assess the statistical
    significance of the reported gains without raw data.
- id: 411db5c0277c
  severity: science
  text: Clarify the statistical test used to validate the 'PTF sensitivity' claims
    in Section 5.2 and Appendix B. The text reports specific point drops (e.g., -23.0)
    for perturbed conditions but does not state if these differences were tested against
    a null hypothesis or if the variance across the 75 probes was sufficient to support
    the conclusion.
- id: 3936c092f2d1
  severity: science
  text: Address the multiple comparisons problem. The study evaluates 6 models across
    6 context modes and 4 metrics (APF, RPF, RAE, PTF) across 3 scenario types. The
    paper highlights 'best' results without mentioning any correction (e.g., Bonferroni,
    Holm-Bonferroni) for the large number of pairwise comparisons performed.
- id: dbfba06f697e
  severity: science
  text: Provide the sample size (N) and degrees of freedom for the Pearson correlation
    analyses in Appendix B (Judge Validation). While r=0.96 is reported, the statistical
    power and significance (p-value) of these correlations are missing, which is critical
    for validating the LLM judge.
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:15:25.892955Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this paper is largely descriptive, relying on mean scores and point-difference comparisons without sufficient inferential statistics to support the strength of the claims.

First, the primary results in Table 1 and Table 2 present only point estimates (e.g., DeepSeek-V4-Pro Arc score of 62.4 vs. Vanilla 52.4). There are no confidence intervals, standard errors, or standard deviations reported for these means. Given the variability inherent in LLM generation and the relatively small number of probes per condition (e.g., 75 probes for the PTF perturbation study in Appendix B), the absence of uncertainty measures makes it difficult to determine if the observed gaps are statistically significant or potentially due to random variance. The claim that "Arc-grounded context achieves the highest Overall score on every model" requires statistical testing (e.g., paired t-tests or Wilcoxon signed-rank tests) to be robust.

Second, the paper performs a large number of pairwise comparisons (6 models × 6 modes × 4 metrics × 3 scenario types) but does not address the multiple comparisons problem. Highlighting the "best" result in each column without correcting for the family-wise error rate (e.g., via Bonferroni or False Discovery Rate) inflates the risk of Type I errors. The authors should clarify if the reported "lifts" (e.g., +7.7 points) remain significant after such corrections.

Third, the validation of the PTF metric (Appendix B) relies on reporting mean drops in scores after perturbation (e.g., -23.0 for reverse_response). While the magnitude of the drop is impressive, the text does not specify the statistical test used to confirm that these drops are significantly different from zero or from the baseline variance. Similarly, the judge validation section reports high Pearson correlations (r ≥ 0.92) between the LLM judge and human scores but omits the p-values and confidence intervals for these correlations, which are essential for establishing the judge's reliability.

Finally, the sample sizes for the ablation studies (e.g., N=75 for PTF perturbation, N=210 for human plausibility) are stated, but the power of these tests is not discussed. For the human plausibility check (87.1% pass rate), a binomial test or confidence interval around the proportion would strengthen the claim of validity. The authors should supplement their descriptive statistics with inferential tests and uncertainty estimates to fully support their conclusions.
