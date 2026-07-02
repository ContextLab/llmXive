---
action_items:
- id: 4eb74023f6f6
  severity: science
  text: The paper reports specific quantitative values for stable rank, Frobenius
    norms, and principal angles (e.g., '10 degrees', '10^-3 level') in Section 5 and
    Figure 5 captions. However, no standard deviations, confidence intervals, or p-values
    are provided to assess the statistical significance of the differences between
    SFT, OPD, and RLVR trajectories. Given the claim of distinct regimes, variance
    estimates across seeds or layers are required to rule out noise.
- id: c12f245cbf48
  severity: science
  text: The 'bf16-aware update sparsity' metric relies on a fixed threshold eta=10^-3
    (Section 4.1). The sensitivity of the reported sparsity percentages (e.g., 51.6%
    vs 77.2%) to this specific threshold choice is not analyzed. A sensitivity analysis
    varying eta is needed to ensure the 'relaxed off-principal' conclusion is not
    an artifact of the precision cutoff.
- id: 81ec88d164d6
  severity: science
  text: In the rank-16 projection experiment (Section 5.2), the performance difference
    between OPD and SFT is presented as a definitive finding. However, the text does
    not mention whether the evaluation was repeated across multiple random seeds or
    if statistical tests (e.g., t-tests) were performed to confirm the degradation
    in SFT is significant compared to the variance in OPD.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:33:19.539213Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis of parameter-space geometry is conceptually sound, utilizing established diagnostics like stable rank, principal angles, and spectral drift. However, the presentation of results lacks necessary statistical rigor to fully support the strong claims of distinct regimes.

First, the paper reports point estimates for key metrics (e.g., "principal angles rise above 10°" for SFT vs "around 1°" for OPD in Section 4.2) without providing measures of uncertainty. Given that these metrics are averaged across layers and potentially across seeds, the absence of standard deviations, confidence intervals, or error bars in the text (and implied in the figures) makes it difficult to assess the statistical significance of the observed differences. The claim that OPD occupies a "distinct" regime relies on these differences being robust, not just point-estimate separations.

Second, the definition of "bf16-aware update sparsity" depends critically on the threshold $\eta=10^{-3}$ (Section 4.1). The paper does not include a sensitivity analysis to show how the reported sparsity values (e.g., 51.6% for OPD) change if $\eta$ is varied slightly. Without this, the conclusion that OPD is "intermediate" could be sensitive to the arbitrary choice of precision cutoff.

Finally, the functional sufficiency experiment (Section 5.2) claims that rank-16 projection "degrades SFT" while leaving OPD "essentially unchanged." While the performance drop is described, the statistical significance of this difference is not quantified. Were the evaluations run with multiple seeds? Is the difference in final accuracy statistically significant? Adding error bars or reporting p-values for these comparative experiments would strengthen the evidence for the "subspace locking" hypothesis.
