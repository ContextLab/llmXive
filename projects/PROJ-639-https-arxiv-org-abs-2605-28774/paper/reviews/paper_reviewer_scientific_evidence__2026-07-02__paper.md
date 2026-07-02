---
action_items:
- id: 932f64d71765
  severity: science
  text: The claim that AXPO 'provably dominates' raw sampling (Proposition 1, text/2_method.tex)
    relies on the assumption p(prefix) >= q * p^tool. The paper asserts this holds
    empirically but lacks a statistical test or confidence interval on the distribution
    of p(prefix) across the training set to confirm the threshold is met with high
    probability, not just on average.
- id: 6802764ce8ab
  severity: science
  text: The 'all-wrong' rate diagnostic (Fig 3b, text/2_method.tex) is central to
    the motivation. The paper reports ~40% but does not provide the standard error
    or the number of questions (N) used to calculate this rate. Given the binary nature
    of the metric, the sample size is critical to assess the stability of this claim.
- id: 4f03b20250c9
  severity: science
  text: The comparison to 'rollout 2x' (Table 2, tables/tab_comparison.tex) claims
    AXPO is more efficient. However, the '2x' baseline doubles the *total* rollout
    budget, while AXPO adds a 25% *extra* budget (r=0.25). The paper does not explicitly
    normalize the comparison to a '25% extra budget' GRPO baseline to isolate the
    algorithmic gain from the compute difference.
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T05:16:59.381756Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the "Thinking-Acting Gap" and the efficacy of AXPO is generally robust, with clear diagnostic plots (Fig 3) and consistent performance gains across multiple benchmarks and model scales (Tables 1, 4). The ablation study (Table 1) effectively isolates the contribution of the resampling mechanism. However, several statistical and experimental design details require clarification to fully validate the central claims.

First, the theoretical justification in Proposition 1 (text/2_method.tex) claims that prefix-fixed resampling "provably dominates" raw sampling. This proof strictly holds only if the selected prefix satisfies $p(\text{prefix}) \geq q \cdot p^{\text{tool}}$. While the authors argue this is true empirically, the manuscript lacks a statistical analysis of the distribution of $p(\text{prefix})$ across the training data. Without a confidence interval or a histogram showing that the majority of selected prefixes exceed this threshold, the "provably" claim is slightly overstated. A brief statistical summary of the prefix success rates would strengthen this argument.

Second, the diagnostic metrics driving the method's design, specifically the "all-wrong" rate of ~40% for tool-using subgroups (Fig 3b, text/2_method.tex), are presented as point estimates. The paper does not report the standard error, confidence intervals, or the total number of questions ($N$) sampled to derive these percentages. Given that these metrics are binary (all-wrong vs. not), the sample size is crucial for assessing the stability of the observation. If $N$ is small, the 40% figure could be noisy, potentially undermining the motivation for the specific resampling trigger.

Finally, the efficiency claim in Section 3.4 (text/3_experiments.tex) and Table 2 (tables/tab_comparison.tex) compares AXPO (with a 25% extra budget) against a "rollout 2x" baseline (100% extra budget). While the result shows AXPO is superior, the comparison is confounded by the compute difference. To rigorously prove that the gain comes from the *algorithm* (resampling) rather than just *more compute*, the authors should include a baseline where GRPO is run with a 25% extra rollout budget (or equivalent compute) to show that AXPO still outperforms it. Without this controlled comparison, the claim that "the gain comes from where compute is spent" is not fully isolated from the effect of having *any* extra compute.
