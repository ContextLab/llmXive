---
action_items:
- id: 1741cc4f692b
  severity: science
  text: The claim of '55x faster' inference (Sec 4.2) relies on a specific deployment
    configuration (CUDA Graphs) for GAM that is not applied to baselines. Table A.5
    shows the gap narrows to ~1.7x (17.5ms vs 29.2ms) without CUDA Graphs. The main
    text must clarify this asymmetry to avoid overstating the speed advantage.
- id: e6dfc5e5336e
  severity: science
  text: Real-world robustness claims (Sec 4.2) are based on only 20 trials per task
    (10 ID, 10 OOD). This sample size is insufficient to robustly claim 'substantial'
    outperformance over baselines given the high variance typical in real-robot manipulation.
    Please report confidence intervals or conduct a statistical significance test
    (e.g., bootstrap) to support the conclusion.
- id: 8283a722d8f6
  severity: science
  text: 'The ablation study in Table 3 suggests removing L_depth and L_feat has ''minimal
    impact'' on robustness (Plus SR 89.0% vs 89.7%). However, the text claims these
    losses ''substantially improve robustness'' when pretraining is absent. The manuscript
    should explicitly reconcile these findings: does the benefit of geometric prediction
    losses depend entirely on the absence of pretraining, or is the effect masked
    by the strong backbone in the main setting?'
artifact_hash: 2b47a226fbf60e77bf3630e010af6d066f9a3ac0ebb39463048a80ab1f66b524
artifact_path: projects/PROJ-718-geometric-action-model-for-robot-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:58:50.640237Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the core claims of the Geometric Action Model (GAM) is generally strong, particularly regarding the architectural novelty and the simulation results on LIBERO-Plus. The ablation studies effectively isolate the contribution of the split layer $L_s$ and the pretraining stage. However, there are specific concerns regarding the statistical rigor of the real-world evaluation and the fairness of the inference speed comparison that require clarification before the claims can be fully accepted.

First, the claim of a "55x" speedup over diffusion-based baselines (Introduction, Sec 4.2) is potentially misleading due to an asymmetry in the evaluation protocol. Table A.5 in the appendix reveals that the 6.9ms latency for GAM is achieved using CUDA Graphs, a deployment optimization not enabled for the baselines (which are measured at 29.2ms–382.4ms without CUDA Graphs). When comparing under matched conditions (Torch Compile only, no CUDA Graphs), the speedup reduces to approximately 1.7x (17.5ms vs 29.2ms for $\pi_{0.5}$). While GAM is still faster, the "55x" figure conflates architectural efficiency with specific deployment optimizations. The main text should either present the matched comparison as the primary metric or explicitly qualify the 55x claim as a "best-case deployment scenario" to avoid overstating the inherent algorithmic advantage.

Second, the real-world robustness claims rely on a sample size that is statistically fragile. The authors report results from "20 trials per task" (10 nominal, 10 perturbed) in Sec 4.2 and Appendix A.3. In real-robot manipulation, success rates can exhibit high variance due to unmodeled dynamics, lighting changes, or minor hardware inconsistencies. With only 10 trials in the out-of-distribution (OOD) condition, a difference of a few successes (e.g., 7/10 vs 5/10) can lead to large percentage swings that may not be statistically significant. The paper currently lacks confidence intervals, standard errors, or a statistical significance test (e.g., a bootstrap test or Fisher's exact test) to validate that the observed improvements over baselines like $\pi_{0.5}$ are not due to random chance. Given the high stakes of "real-world" claims, a larger sample size (e.g., 50+ trials) or rigorous statistical reporting is necessary.

Finally, the interpretation of the ablation study in Table 3 requires nuance. The authors state that removing the future-prediction losses ($\mathcal{L}_{\text{depth}}$, $\mathcal{L}_{\text{feat}}$) has "minimal impact" on robustness when pretraining is present (89.7% vs 89.0% on LIBERO-Plus). However, they simultaneously claim these losses "substantially improve robustness" when pretraining is absent (73.4% vs 50.0%). This suggests the benefit of the geometric world modeling objective is conditional on the lack of a strong pretrained prior. The discussion should explicitly address this interaction: does the GFM backbone already encode sufficient geometric dynamics that the explicit prediction losses become redundant in the pretraining regime? Clarifying this would strengthen the argument for when and why the proposed architecture is necessary.
