---
action_items:
- id: 6abb5daaf6de
  severity: science
  text: Table 1 (Video Eval) and Table 2 (Code Eval) report single-point accuracy
    scores without confidence intervals or standard deviations. Given the stochastic
    nature of LLM inference and benchmark sampling, report 95% CIs or results over
    multiple seeds to establish statistical significance of the claimed margins (e.g.,
    74.1 vs 70.5 on LongVideoBench).
- id: 7e66cac087a1
  severity: science
  text: The claim of '1% improvement' from Video RL (Section 4.2.4) lacks statistical
    context. Specify the baseline score, the sample size (N=31K), and the variance
    of the metric to determine if this gain is statistically significant or within
    the noise floor of the evaluation protocol.
- id: f5e5f3e84fe8
  severity: writing
  text: The 'Non-Lin' metric in Table 1 (Video-MME-v2) shows a performance drop for
    Keye-VL-2.0 compared to InternVL3.5. The text does not discuss the statistical
    significance of this degradation or potential confounding factors (e.g., specific
    video length distributions) that might explain the variance.
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:26:38.678201Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive technical report on Kwai Keye-VL-2.0, detailing architectural innovations (DSA, MoE) and extensive benchmarking. However, from a statistical analysis perspective, the evaluation section relies heavily on point estimates without measures of uncertainty.

In **Table 1 (Video Understanding Evaluation)** and **Table 2 (Code Agent Evaluation)**, the authors report single scalar scores (e.g., 74.1 on LongVideoBench, 64.2 on LiveCodeBench). For large language models, inference results can vary significantly based on sampling temperature, random seeds, and the specific subset of the benchmark used. Without reporting confidence intervals (CIs), standard deviations, or results averaged over multiple independent runs, it is impossible to determine if the reported margins (e.g., the 3.6 point lead over InternVL3.5 on LongVideoBench) are statistically significant or merely artifacts of random variance. Standard practice in the field requires reporting $mean \pm std$ or 95% CIs for such claims.

Furthermore, in **Section 4.2.4 (Video RL)**, the authors state that training on 31K video samples "improves benchmarks by 1%." This claim is statistically ambiguous. A 1% absolute improvement on a benchmark with a score of ~80 is a small effect size. The manuscript does not provide the baseline variance, the specific benchmark subset used for this claim, or a statistical test (e.g., t-test or bootstrap) to validate that this improvement is distinguishable from noise.

Finally, **Table 1** includes a "Non-Lin" metric where Keye-VL-2.0 underperforms InternVL3.5 (18.5 vs 26.3). The text focuses almost exclusively on the "ACC" metric where the model leads, potentially engaging in "cherry-picking" of favorable statistics. A rigorous review would require an analysis of whether this degradation is statistically significant and an explanation of the trade-offs involved in the model's design choices that lead to this specific variance.

To strengthen the scientific validity of the claims, the authors should re-run evaluations with multiple seeds to generate variance estimates and report these alongside the means.
