---
action_items:
- id: 95f7b0e72f05
  severity: science
  text: The real-world Franka experiments (Sec 6) report success rates over 50 trials
    but lack statistical significance testing (e.g., confidence intervals or p-values)
    when comparing PhysBrain 1.0 against the $\pi_{0.5}$ baseline. Given the claim
    of a 16.2% average gain, provide 95% CIs or a binomial test to confirm the improvement
    is not due to random variance.
- id: d842d143514d
  severity: science
  text: In the VLM results (Sec 5.1.2), the 'Avg. relative' metric normalizes scores
    by the best model per benchmark before averaging. This aggregation method obscures
    the magnitude of absolute gains and may introduce bias if benchmarks have different
    score distributions. Justify this normalization or report absolute mean differences
    with standard deviations.
- id: ac9821a381d9
  severity: science
  text: The VLA simulation results (Tables 1-4) show single-point success rates without
    error bars or standard deviations across seeds. For claims of SOTA performance
    (e.g., 80.2% on SimplerEnv-WidowX), report results averaged over multiple random
    seeds (e.g., 3-5) with standard deviation to ensure reproducibility and robustness.
artifact_hash: bf25ed8c32843a89226c47ca4dcbfcdb0c63d6720d9c7d52a55697f1d16cf9dc
artifact_path: projects/PROJ-600-https-arxiv-org-abs-2605-15298/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:28:22.169026Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the experimental sections requires strengthening to fully support the claims of superior performance and robustness.

In Section 5.1.2 (VLM Experiment Results), the authors introduce an "Avg. relative" metric where scores are normalized by the best model on each benchmark before averaging. While this allows for a unified view across benchmarks with different scales, it obscures the absolute magnitude of improvements and the variance within each benchmark. For instance, a 2-point gain on a benchmark where the best score is 50 is statistically distinct from a 2-point gain where the best is 90. The manuscript should report the absolute mean scores and standard deviations for each benchmark, or at least provide the standard error of the mean for the aggregated metric, to allow for a more rigorous assessment of the gains.

More critically, the real-world experiments in Section 6 (Real-World Experiments) lack essential statistical validation. The authors report success rates based on 50 independent trials per task (450 total trials for single-object grasping). While the reported improvement of 16.2 percentage points (from 47.1% to 63.3%) is substantial, the manuscript does not provide confidence intervals (CIs) or results of statistical significance tests (e.g., a two-proportion z-test or Fisher's exact test) to determine if this difference is statistically significant or could be attributed to random chance. Given the high stakes of real-world deployment claims, providing 95% confidence intervals for the success rates of both PhysBrain 1.0 and the $\pi_{0.5}$ baseline is necessary.

Similarly, the simulation results in Tables 1 through 4 (SimplerEnv, RoboCasa, LIBERO) present single-point success rates. In deep learning research, performance can vary significantly based on random initialization, data shuffling, or evaluation stochasticity. The absence of standard deviations or error bars (typically derived from running experiments over multiple random seeds, e.g., 3-5) makes it difficult to assess the stability and reproducibility of the reported SOTA results. For example, the 1.0% margin over the second-best method on SimplerEnv-WidowX (80.2% vs 79.2%) is within the typical noise floor of a single run. The authors should report mean and standard deviation across multiple seeds to substantiate the claim of consistent superiority.

Finally, the data engine section (Sec 2) describes a multi-model annotation pipeline but does not quantify the inter-annotator agreement or the variance introduced by different generator models (GPT-5, Gemini, Qwen, etc.). While the text mentions using multiple models to reduce bias, a statistical measure of the consistency of the generated QA pairs (e.g., agreement on physical attributes) would strengthen the argument for the quality of the supervision signal.
