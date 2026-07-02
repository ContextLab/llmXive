---
action_items:
- id: 31deae9ec66a
  severity: science
  text: The paper claims 'extensive experiments' across Qwen2.5/3 families but provides
    no statistical significance testing (e.g., t-tests, confidence intervals) for
    the reported gains (e.g., +9.4% on ALFWorld). Without variance estimates or multiple
    seeds, these point estimates are insufficient to rule out random fluctuation,
    especially given the small number of reported runs (implied single run per setting).
- id: 4b33ec90d11e
  severity: science
  text: The robustness analysis (Table 2) claims 'graceful degradation' with random
    retrieval, yet the baseline 'w/o OPSD' is a single point. The paper fails to report
    the variance of the baseline or the proposed method across different random seeds
    for the retrieval noise experiment, making the 'robustness' claim statistically
    unsupported.
- id: 5d3ea580f41a
  severity: science
  text: "The ablation study on hyperparameters (Figures 4-6) sweeps $\\lambda$ and\
    \ $\beta$ but does not report the standard deviation of performance across seeds\
    \ for these ablations. Given the sensitivity of RL training, a single run per\
    \ hyperparameter setting is insufficient to validate the claimed 'optimal' values."
- id: 979e877c7155
  severity: science
  text: The claim that 'naive GRPO+OPSD degrades severely' (Section 4.1) is supported
    by a single data point (32.0 vs 46.1). The paper must provide error bars or results
    from multiple independent training runs to confirm this instability is systematic
    and not an artifact of a specific random seed or initialization.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:58:57.075928Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the central claims of SDAR is currently insufficient due to a lack of statistical rigor in the experimental reporting. While the methodology is well-motivated, the empirical validation relies almost exclusively on point estimates from what appears to be single-run experiments.

First, the paper reports specific performance gains (e.g., +9.4% on ALFWorld, +7.0% on Search-QA) without providing standard deviations, confidence intervals, or results from multiple random seeds. In reinforcement learning, particularly with LLMs, performance can vary significantly based on initialization and stochastic sampling. Without variance estimates, it is impossible to determine if these improvements are statistically significant or merely the result of favorable random seeds. The claim of "consistent improvements across all model scales" is particularly vulnerable to this issue.

Second, the robustness analysis regarding retrieval quality (Table 2) is underpowered. The authors claim the method degrades gracefully even with random retrieval, but the comparison is made against a single baseline value ("w/o OPSD"). To substantiate the claim that the gating mechanism filters noise effectively, the authors must demonstrate that the performance distribution of SDAR with random retrieval is significantly better than the baseline distribution, not just that the mean is higher.

Third, the ablation studies on hyperparameters ($\lambda$, $\beta$) and loss functions (Figure 4-6) present smooth curves that suggest deterministic outcomes. However, RL training is inherently noisy. The absence of error bars on these ablation plots makes it difficult to assess the stability of the optimal hyperparameters. If the performance curves overlap within one standard deviation, the claimed "optimal" settings may not be distinguishable from suboptimal ones.

Finally, the claim that "naive GRPO+OPSD degrades severely" (Section 4.1) is supported by a single data point (32.0 vs 46.1 for Qwen3-1.7B). To prove this instability is a systematic failure mode of the baseline rather than a fluke, the authors must report results from multiple independent training runs for the baselines as well.

To meet the standards of scientific evidence, the authors must re-run key experiments (main results, ablations, and robustness checks) with multiple seeds (at least 3-5) and report mean $\pm$ standard deviation. Statistical significance tests (e.g., paired t-tests) should be included to validate the reported improvements.
