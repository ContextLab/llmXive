---
action_items:
- id: c794bfe01ebf
  severity: science
  text: Report confidence intervals or standard errors for all mean scores in Tables
    1 and 2. With 289 cases, point estimates alone are insufficient to assess statistical
    significance of model differences (e.g., Wan 2.7 vs. Kling 3.0).
- id: 5187de01f60e
  severity: science
  text: Clarify the multiple-comparisons correction method used for the 22 sub-metrics.
    Without adjustment (e.g., Bonferroni or FDR), the risk of Type I errors in identifying
    'leading' models is high.
- id: 4ecb3901f425
  severity: writing
  text: Specify the sample size (N) and degrees of freedom for the Pearson/Spearman
    correlations reported in Figure 3. Correlation strength depends heavily on N,
    which is currently ambiguous for the '20 models' subset.
- id: 3ffd5fb2c7de
  severity: science
  text: Provide the distribution (e.g., boxplots or histograms) of the human-annotation
    scores used to validate the automated metrics. A single Spearman rho value does
    not reveal if the alignment holds across the full score range or only at extremes.
artifact_hash: 583182a56bc8cd93d801cd098b02d980b9a48cb375dac6cc8130da68f508615f
artifact_path: projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:04:38.079212Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in WBench is extensive but lacks necessary rigor in uncertainty quantification and error control. While the paper reports 22 sub-metrics across 289 test cases, it presents only point estimates (means) in Tables 1 and 2 (e.g., "Wan 2.7: 91.5", "Kling 3.0: 91.0"). Without confidence intervals (CIs) or standard errors, it is impossible to determine if these differences are statistically significant or within the noise of the evaluation protocol. Given the multi-turn nature of the data (1,058 turns), the effective sample size for independence assumptions also requires clarification.

Furthermore, the paper performs numerous pairwise comparisons across models and dimensions without mentioning any correction for multiple testing (e.g., Bonferroni, Holm-Bonferroni, or False Discovery Rate). With 22 metrics and 20 models, the probability of false positives is substantial. The claim that "no single model excels on all dimensions" relies on these uncorrected comparisons.

Regarding the human alignment study (Section 5.3, Figure 4), the authors report high Spearman correlations ($\rho \ge 0.94$). However, the statistical power of this claim depends on the number of pairwise comparisons and the distribution of human scores. The text mentions "400 annotators" and "13.5K tasks," but the specific N used for the correlation calculation is not explicitly stated in the text or figure caption. Additionally, the validation relies on a single aggregate correlation coefficient; a more robust analysis would include Bland-Altman plots or per-dimension error analysis to ensure the automated metrics do not systematically bias high or low scores.

Finally, the Z-score analysis for difficulty factors (Figure 3c) is presented without the underlying variance or standard deviation of the scores used to compute these Z-scores. To ensure reproducibility and statistical validity, the authors should provide the standard deviation of the scores for each dimension and model, and explicitly state the statistical tests used to derive the Z-scores.
