---
action_items:
- id: 217234ab4a00
  severity: science
  text: The sample size for the primary quantitative evaluation is insufficient to
    support claims of robustness across categories. With only 7 objects and 20 episodes
    per cell, the standard error for success rates is ~10% (Appendix Sec. 2.1). The
    paper reports small differences (e.g., 0.15 vs 0.30 at x4 damping) as evidence
    of superiority without reporting confidence intervals or statistical significance
    tests (e.g., t-tests or bootstrapping).
- id: 8457325b2346
  severity: science
  text: The 'Traj. tracking' baseline achieves 1.00 success at x1 damping on all objects
    (Table 1), yet the text claims it fails under higher damping due to contact loss.
    However, the table shows it maintains 1.00 success on 5/7 objects even at x4 damping.
    This contradicts the narrative that open-loop replay is inherently non-robust
    and requires clarification or correction of the baseline's performance data.
- id: 6a3ce5458cae
  severity: science
  text: The hardware results in Figure 4 and Appendix Fig. 3 are presented as 'qualitative
    illustrations' with no quantitative metrics (success rate, episodes). The claim
    that the method is 'physically plausible' relies heavily on these single-rollout
    visualizations. To support the central claim of physical plausibility, a small-scale
    real-world quantitative benchmark (even n=5-10) is required to rule out simulation
    artifacts.
- id: d95a1fb38e15
  severity: science
  text: The ablation study (Table 2) shows that 'w/o GLA' (PICA only) achieves 0.43
    success at x4, while 'w/o PICA' (GLA only) achieves 0.36. The paper claims these
    components are 'complementary' and the full model (0.56) is significantly better.
    However, the difference between 0.36 and 0.43 is within the noise margin of the
    sample size (n=140 total for that cell). The statistical significance of the ablation
    gains is not established.
artifact_hash: aac12eff083d8d7168328cdeef9fdab897d5808d01d31c99a8c36453db9b88d3
artifact_path: projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T13:50:45.836552Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the central claims of robustness and physical plausibility is currently insufficient due to limited sample sizes and a lack of statistical rigor.

First, the evaluation protocol relies on a very small test set: 7 GAPartNet objects with 20 episodes each (Section 4, Table 1). As noted in the Appendix (Sec. 2.1), the standard error for a success rate estimate with n=20 is approximately 10%. The paper frequently draws strong conclusions from differences that fall within this margin of error. For instance, the comparison between the full PICA model (0.56 success at x4) and the 'w/o GLA' ablation (0.43) or 'w/o PICA' ablation (0.36) lacks statistical significance testing. Without confidence intervals or hypothesis testing (e.g., paired t-tests or bootstrapping), it is impossible to determine if the observed improvements are real or artifacts of random variation in the 20-episode rollouts.

Second, there is a discrepancy between the narrative and the data regarding the 'Traj. tracking' baseline. The text argues that open-loop replay fails under high damping because it cannot maintain contact. However, Table 1 shows that the trajectory tracking baseline maintains 1.00 success on 5 out of 7 objects even at x4 damping (e.g., objects 12583, 45261, 45661, 46440, 48513). It only fails on objects 45936 and 7310. This suggests the baseline is more robust than claimed, and the failure of other methods might be specific to certain object geometries rather than a general failure of contact-driven learning. The paper needs to reconcile this data with its claims about the necessity of PICA.

Third, the claim of "physical plausibility" is supported almost entirely by qualitative visualizations (Figure 4, Appendix Fig. 3) and simulation metrics. While the simulation results are internally consistent, the lack of any quantitative real-world validation (even a small n=5-10 study) leaves the "physical" aspect of the claim unverified. Simulation physics engines can sometimes mask contact instabilities that would occur in reality. The hardware images are labeled as "qualitative," which is insufficient to substantiate a claim of physical plausibility for a dexterous hand system.

Finally, the training-length study (Table 3) shows a collapse in robustness (x4 success dropping from 0.55 to 0.10) as training extends, which is a strong finding. However, this is based on a single object (45936) and a single run. To generalize this "overfitting to nominal dynamics" claim, the authors should demonstrate this trend across multiple objects or provide error bars on the training curves.

To proceed, the authors must: (1) Report confidence intervals or p-values for all comparative results in Tables 1 and 2; (2) Clarify the performance of the trajectory tracking baseline in the text to match the data in Table 1; (3) Provide at least a small-scale quantitative real-world evaluation or explicitly limit the scope of "physical plausibility" claims to simulation; and (4) Replicate the training-length collapse finding on at least one additional object to ensure it is not an anomaly.
