---
action_items:
- id: d98b9ece0226
  severity: science
  text: The standard error for success rates (n=20) is ~0.11, yet the paper treats
    small differences (e.g., 0.15 vs 0.30 at x4 damping) as distinct performance tiers.
    Report confidence intervals or statistical significance tests for the main comparison
    in Table 1 and Figure 2 to support claims of superiority.
- id: 4bf741681fea
  severity: science
  text: The 'Traj. tracking' baseline achieves 1.00 success at x1 and x4 damping (Table
    1), which contradicts the claim that open-loop replay fails under high damping.
    Clarify why this specific baseline is robust to damping changes while learned
    policies fail, or re-evaluate the baseline's physical validity.
- id: 58b9c07a3596
  severity: science
  text: The hardware results in Figure 4 are qualitative only. To support the claim
    of 'physically plausible' interaction, provide quantitative metrics (e.g., contact
    force, slip rate) from the hardware trials or explicitly limit the claim to simulation
    validity.
artifact_hash: aac12eff083d8d7168328cdeef9fdab897d5808d01d31c99a8c36453db9b88d3
artifact_path: projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:31:54.447274Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the central claims of DragMesh-2 is generally robust, particularly regarding the ablation of the PICA mechanism and the demonstration of overfitting in standard PPO baselines. The experimental design effectively isolates the contribution of contact-aware signals and temporal encoding. However, several statistical and interpretative issues require clarification before the evidence fully supports the conclusions.

First, the sample size for the main comparison is 20 episodes per cell (Section 5, "Experiments"). For a binary success metric, the standard error is approximately $\sqrt{p(1-p)/20} \approx 0.11$ at $p=0.5$. The paper frequently highlights small absolute differences in success rates (e.g., 0.15 vs. 0.30 at $\times4$ damping in Table 1) as evidence of methodological superiority. Without confidence intervals or statistical significance testing (e.g., McNemar's test or bootstrap CIs), these differences are statistically indistinguishable from noise. The authors should report error bars in Figure 2 and add a statistical analysis section to validate the claimed performance gaps.

Second, the "Traj. tracking" baseline presents a logical anomaly in the evidence. Table 1 shows this open-loop baseline achieving 1.00 success at $\times1$, $\times2$, and $\times4$ damping for most objects, yet the text claims open-loop replay fails under high damping. If the baseline is truly robust to damping changes, the claim that "open-loop replay alone is not OOD-robust" is unsupported by the provided data. The authors must explain why this specific baseline succeeds where learned policies fail, or re-evaluate the baseline's implementation to ensure it does not inadvertently cheat the physics (e.g., by ignoring damping in the trajectory generation).

Third, the claim of "physically plausible" interaction relies heavily on simulation results. While the hardware visualization in Figure 4 is compelling, it is qualitative. The absence of quantitative hardware metrics (e.g., contact force profiles, slip detection rates) limits the ability to verify the physical plausibility claim outside of simulation. The authors should either provide quantitative hardware data or temper the claim to "simulation-validated physical plausibility."

Finally, the training-length study (Table 3) provides strong evidence of the "nominal success masks saturation collapse" phenomenon, which is a key contribution. However, the transition from 0.55 to 0.10 success between 200 and 300 epochs is abrupt. The authors should discuss the sensitivity of this collapse to random seeds to ensure it is a systematic failure mode rather than a stochastic artifact.
