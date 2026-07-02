---
action_items:
- id: 603ec6f628c0
  severity: science
  text: Report confidence intervals or standard errors for the success rates in Table
    1 and Table 2. With N=20 episodes per cell, the standard error is ~0.11; without
    error bars or CIs, small differences (e.g., 0.56 vs 0.50) are statistically indistinguishable.
    Appendix Limitations (Sec 5.1) acknowledges this but the main results tables lack
    the necessary statistical context.
- id: dbaf48da14a5
  severity: science
  text: Clarify the statistical independence of the 20 episodes per cell. If the same
    random seed or initialization is used across damping conditions for a single object,
    the samples are not independent, invalidating standard error calculations. Explicitly
    state the randomization protocol for episode initialization and damping sampling
    in Appendix Sec 5.1.
- id: e7aa39678d08
  severity: science
  text: The ablation study (Table 2) compares multiple methods without correcting
    for multiple comparisons. With 7 objects and 3 damping levels, the number of pairwise
    tests is high. Report adjusted p-values or use a non-parametric test (e.g., Friedman
    test) to validate that PICA's superiority over baselines is statistically significant
    rather than due to chance.
artifact_hash: aac12eff083d8d7168328cdeef9fdab897d5808d01d31c99a8c36453db9b88d3
artifact_path: projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:32:15.942560Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in DragMesh-2 is generally sound in its design, particularly the use of out-of-distribution (OOD) damping conditions to test robustness and the inclusion of diagnostic metrics like action saturation (`clip099`) alongside success rates. The authors correctly identify that nominal success can mask failure modes, and the experimental protocol (20 episodes per cell) provides a reasonable sample size for a simulation-based RL benchmark.

However, the presentation of results lacks necessary statistical rigor for a quantitative comparison. In **Table 1** (Main Comparison) and **Table 2** (Ablation), success rates are reported as point estimates (e.g., 0.56 vs 0.50) without confidence intervals (CIs) or standard errors. As noted in the Appendix (Section 5.1, "Limitations"), the standard error for a proportion with $N=20$ is approximately $\sqrt{p(1-p)/20} \approx 0.11$. Consequently, differences of 0.05–0.10 between methods (e.g., PICA vs. Reconfig at $\times4$ damping) are not statistically distinguishable. The text claims PICA "attains the best mean in every damping/mode column," but without error bars or significance testing, these claims are not statistically supported.

Furthermore, the ablation study involves multiple pairwise comparisons across objects and damping levels. The authors do not mention any correction for multiple comparisons (e.g., Bonferroni or False Discovery Rate), increasing the risk of Type I errors when claiming the superiority of the full PICA model over its ablated variants. While the Appendix acknowledges the limitation of small sample sizes, the main text and tables should reflect this uncertainty visually (error bars) or numerically (CIs).

Finally, the independence of the 20 episodes per cell is not explicitly defined. If the same random seed or initial state is used across different damping conditions for the same object, the samples are correlated, which would invalidate standard error calculations. The authors should clarify the randomization protocol for episode initialization and damping sampling in the Appendix to ensure the statistical validity of the reported metrics.
