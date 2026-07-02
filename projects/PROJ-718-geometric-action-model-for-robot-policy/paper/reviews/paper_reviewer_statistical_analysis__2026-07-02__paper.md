---
action_items:
- id: 15ab170f38a4
  severity: science
  text: Report confidence intervals or standard deviations for success rates in Table
    1 and Table 3. With N=500 rollouts per suite, the margin of error is ~2%, yet
    no uncertainty metrics are provided to assess the statistical significance of
    the reported 9.7%p gain.
- id: e511088d6477
  severity: science
  text: Clarify the statistical test used to claim 'consistently outperforms' in Section
    4.2. Given the binary nature of success/failure, specify if a McNemar's test or
    bootstrap procedure was used to validate the differences against baselines like
    pi_0.5.
- id: 2f9320d19c63
  severity: science
  text: In the ablation study (Table 3), the claim that removing L_depth has 'minimal
    impact' lacks statistical validation. Provide p-values or effect sizes to confirm
    the difference between 89.7% and 89.5% is not due to random variance.
artifact_hash: 2b47a226fbf60e77bf3630e010af6d066f9a3ac0ebb39463048a80ab1f66b524
artifact_path: projects/PROJ-718-geometric-action-model-for-robot-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:59:12.442486Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the experimental section requires strengthening to support the strong claims of superiority and robustness. While the paper presents extensive benchmark results, it relies almost exclusively on point estimates (mean success rates) without accompanying measures of uncertainty.

In **Table 1 (LIBERO and LIBERO-Plus)**, success rates are reported as single percentages (e.g., 85.5% vs 84.6%). Given the sample sizes (500 rollouts per suite for LIBERO, 1 rollout per perturbed instance for LIBERO-Plus), the standard error for a 50% success rate is approximately 2.2%. The reported gain of 9.7%p in the camera-perturbation setting is substantial, but without confidence intervals or standard deviations, it is impossible to visually assess the overlap between distributions or the precision of the estimate. The authors should report mean ± standard deviation (or 95% confidence intervals) for all aggregate metrics in Tables 1, 3, and the RoboCasa results.

Furthermore, the text in **Section 4.2** states that GAM "consistently outperforms competing baselines." This implies statistical significance, yet no hypothesis tests are described. For binary outcomes (success/failure) across matched tasks or independent trials, appropriate tests such as McNemar's test (for paired comparisons) or a bootstrap-based significance test should be applied. The authors should explicitly state the statistical test used and report p-values for the key comparisons, particularly the camera-perturbation gain.

In the **Ablation Study (Table 3)**, the authors claim that removing the depth loss ($\mathcal{L}_{\text{depth}}$) has "minimal impact," citing a difference of 0.2% (89.7% vs 89.5%). Without a statistical test, this difference is indistinguishable from random noise given the variance inherent in robot learning benchmarks. The authors must provide statistical evidence (e.g., p-values from a paired test or overlapping confidence intervals) to substantiate the claim that the difference is negligible.

Finally, the **Inference Latency** comparison in **Table 4** and **Appendix Table 5** reports single latency values (e.g., 6.9ms). While latency is often deterministic, reporting the mean and standard deviation over multiple runs (e.g., 1000 iterations) would provide a more rigorous characterization of the performance gains, especially when claiming a 55x speedup.
