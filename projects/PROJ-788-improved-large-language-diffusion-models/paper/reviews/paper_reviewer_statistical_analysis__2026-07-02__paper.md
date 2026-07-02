---
action_items:
- id: 2bbd8bd1e0ed
  severity: science
  text: The paper reports specific benchmark scores (e.g., 74.8 on MMLU, 71.3 on BBH)
    without providing standard errors, confidence intervals, or the number of random
    seeds used for evaluation. Given the stochastic nature of diffusion sampling and
    benchmark evaluation, single-point estimates are insufficient to claim statistical
    significance of the reported improvements over baselines.
- id: 735912db07f5
  severity: science
  text: In the ablation study (Sec. 4.2, Tab. 3), the authors claim confidence-based
    scoring 'consistently improves' over likelihood scoring. However, no statistical
    test (e.g., paired t-test or bootstrap) is reported to verify if the observed
    differences (e.g., +1.3 on PIQA) are statistically significant rather than due
    to random variance in the evaluation process.
- id: 07186905ec8b
  severity: science
  text: The SFT epoch ablation (Fig. 2) shows performance trends across epochs, but
    the error bars or variance metrics are not described in the caption or text. Without
    uncertainty quantification, it is difficult to determine if the performance plateau
    or slight dips at higher epochs are meaningful or within the noise margin of the
    evaluation.
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T10:46:23.762390Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling empirical study of iLLaDA, but the statistical rigor of the evaluation and ablation sections requires strengthening to support the claims of "substantial improvement" and "competitiveness."

Currently, the results in Tables 1 and 2 (Sec. 4.1) are presented as deterministic point estimates. In large-scale language model evaluation, results can vary based on random seeds, sampling temperature, and the specific subset of test questions used (especially for benchmarks like MATH or HumanEval). The absence of standard deviations, confidence intervals, or a statement regarding the number of evaluation seeds (e.g., "results averaged over 3 seeds") makes it impossible to assess the statistical significance of the reported gains. For instance, the 1.4-point gain on MMLU over LLaDA (74.8 vs 73.4 implied, though LLaDA is 65.9 in the table, the comparison to Qwen2.5 is 74.8 vs 71.9) needs context on variance to claim it is a robust improvement rather than a fluctuation.

Similarly, the ablation study in Section 4.2 (Table 3) compares scoring rules. While the authors state the improvements are consistent, they do not provide statistical evidence. A simple paired t-test or a bootstrap analysis over the benchmark items would be appropriate to confirm that the observed differences (e.g., +2.3 on HellaSwag) are not due to chance.

Finally, Figure 2 (SFT epoch ablation) illustrates performance trends but lacks uncertainty visualization. If the curves for different epochs overlap within their error margins, the claim that performance "generally improves" might be overstated. The authors should either include error bars in the figure or explicitly state the variance across seeds in the text. Without these statistical safeguards, the reproducibility and robustness of the conclusions remain partially unverified.
