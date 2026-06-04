---
action_items:
- id: cff402a6241b
  severity: science
  text: Report variance across multiple random seeds for all main benchmark results.
    Table 1 shows single-point estimates without error bars or standard deviations,
    making it impossible to assess whether TRB's 0.4-0.9 point advantages are statistically
    significant.
- id: 271e449b84f7
  severity: science
  text: Add statistical significance testing (e.g., t-tests, confidence intervals)
    for the claimed "strongest average" in Table 1. The marginal improvements (33.2
    vs 32.3, 44.4 vs 44.0) lack uncertainty bounds necessary to substantiate superiority
    claims.
- id: c94f435d68a1
  severity: science
  text: "Address checkpoint selection bias. Section 5.2 states methods are compared\
    \ using \"the checkpoint with the highest mean score over the setup-specific benchmark\
    \ suite.\" This introduces selection bias when comparing methods\u2014each method's\
    \ best checkpoint is selected independently rather than comparing at matched training\
    \ steps."
- id: ba9466558394
  severity: science
  text: Provide multiple seed training curves with error bands in Figures 2-4. Figure
    2 shows single trajectories for SKD, TRB, and OPD without variance information,
    limiting interpretability of the "faster early rise" claim.
artifact_hash: a0fcc4014c0149719a56a0fd8c9438fb07408db2050a8ea923c6bb42f703660e
artifact_path: projects/PROJ-649-trust-region-behavior-blending-for-on-po/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T21:38:48.788917Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

## Scientific Evidence Review

### Sample Sizes and Replication

The paper uses two model-pair settings (Qwen3-1.7B←8B and Qwen3-0.6B←4B) with 25,600 training prompts from OpenThoughts3-1.2M. However, **no multiple random seeds are reported** for any main results. All benchmark scores in Table 1 are single-point estimates without variance. This is a critical gap: without seed-to-seed variance, the 0.4-0.9 point improvements claimed for TRB over Vanilla OPD cannot be distinguished from random fluctuation.

### Controls and Baselines

The baseline set is reasonable (Vanilla OPD, Veto, SKD, Temperature warmup, SFT warmup, Fixed-ε blending), and training hyperparameters are held constant (Appendix Table 1). However, the **checkpoint selection protocol introduces systematic bias**: each method's reported score comes from its individually best checkpoint (Section 5.2). This means TRB benefits from selecting its optimal point while other methods are also given their optimal points—but there is no common evaluation timepoint. A fairer comparison would report scores at matched training steps or use a fixed checkpoint selection rule across all methods.

### Effect Sizes and Statistical Rigor

The reported effect sizes are marginal:
- 1.7B←8B: TRB 33.2 vs Vanilla OPD 32.3 (0.9 point difference)
- 0.6B←4B: TRB 44.4 vs Vanilla OPD 44.0 (0.4 point difference)

**No statistical tests are performed** (no p-values, confidence intervals, or effect size measures like Cohen's d). Temperature warmup achieves 32.8 in the first setting—nearly matching TRB's 33.2—yet TRB is claimed as "strongest average" without acknowledging that simpler interventions show comparable performance.

### P-Hacking Risks

The sweep-level analysis in Appendix Figures 1-2 shows many hyperparameter configurations, but **only the best configuration per method is reported in Table 1**. This is a classic multiple-comparisons problem: with 5 ε₀ values × 3 K values = 15 TRB configurations tested, the "best" configuration is likely overfit to the test benchmarks. The paper does not report whether the winning configuration was pre-specified or selected post-hoc.

### Alternative Explanations

The warmup duration itself (not the TRB mechanism) could explain the gains. Fixed-ε blending performs comparably in some columns (10.3 on AIME24 vs TRB's 10.2), and temperature warmup achieves 32.8 vs TRB's 33.2. The paper does not adequately isolate whether the benefit comes from: (1) the trust-region formulation specifically, (2) the annealing schedule, or (3) simply having any warmup intervention. Figure 3 (continuation gain) provides some mechanistic evidence but lacks statistical validation.

### Conclusion

The central claim that TRB "attains the strongest average" cannot be substantiated with the current evidence. Without variance reporting, statistical testing, and proper controls for checkpoint selection bias, the 0.4-0.9 point advantages are scientifically unverifiable.
