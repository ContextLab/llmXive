---
action_items:
- id: 968427a00a36
  severity: science
  text: In Section 4.3 (Evaluation in Simulation), the text claims TCN-L achieves
    89.05% SR at 2B tokens, but Table 1 (tab:sim_scaling_backbone) does not list a
    TCN-L row or a 2B token entry for TCN. This specific data point is missing from
    the provided evidence and must be added to the table or removed from the text
    to ensure reproducibility.
- id: 804e9f20dd9a
  severity: science
  text: Section 4.2 defines diversity metrics (gstd, log-volume) but does not report
    the standard deviation or confidence intervals for these estimates across the
    10,000 sampled embeddings. Given the claim that the new dataset has a '4-5x increase'
    in log-volume, statistical significance testing or error bars are required to
    validate this difference is not due to sampling variance.
- id: e92cb1fb7f57
  severity: science
  text: "The scaling law analysis in Section 5 (Scaling Laws) describes trends qualitatively\
    \ and references figures (Fig. 4, Fig. 5) that are not visible in the text source.\
    \ The manuscript must explicitly state the fitted power-law exponents (e.g., $P\
    \ \\propto N^{-\alpha}$) and their confidence intervals in the text or appendix\
    \ to substantiate the claim of 'predictable trends'."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:28:58.604667Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in the manuscript is generally aligned with the narrative of scaling laws, but several critical gaps in reporting prevent full verification of the quantitative claims.

First, there is a discrepancy between the text and the provided tables regarding baseline performance. In Section 4.3, the authors state: "while larger models eventually reach competitive success rates (e.g., TCN-L achieves 89.05% at 2B tokens)." However, Table 1 (`tab:sim_scaling_backbone`) only reports results for MLP and TCN at 2M tokens, and for Humanoid-GPT variants up to 2B tokens. The specific data point for TCN-L at 2B tokens is absent from the table. Without this data, the claim of saturation for TCN at high scales cannot be independently verified. The authors must either include this row in the table or remove the specific numerical claim from the text.

Second, the analysis of dataset diversity in Section 4.2 relies on point estimates for `gstd` and `log-volume` derived from a sample of 10,000 embeddings. The text claims a "4-5x increase" in log-volume for the curated dataset compared to AMASS. However, no measure of uncertainty (standard error, confidence intervals, or p-values from a statistical test) is provided. Given the high dimensionality of the embedding space and the potential for sampling bias, a statistical test (e.g., a permutation test or bootstrap confidence interval) is necessary to confirm that the observed difference is statistically significant and not an artifact of the sampling procedure.

Third, the "Scaling Laws" section (Section 5) makes strong claims about "predictable trends" and "monotonic scaling" but relies entirely on visual inspection of figures (Fig. 4, Fig. 5) which are not rendered in the text source. To meet the standard of a scaling law paper, the authors should explicitly report the fitted exponents (e.g., $\alpha$ in $Error \propto Data^{-\alpha}$) and their confidence intervals in the text or a supplementary table. Qualitative descriptions of curves are insufficient to establish a "law."

Finally, while the ablation studies in the appendix vary hyperparameters (number of experts, history length), the results are presented as single-point comparisons without error bars or multiple random seeds. For claims regarding the "optimal" configuration (e.g., 384 experts), reporting the variance across seeds would strengthen the conclusion that the observed performance difference is robust.
