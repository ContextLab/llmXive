---
action_items:
- id: fcdbe789d1a9
  severity: science
  text: Theorem 1 assumes Var(R|D_i) is monotone in BS_i to prove variance reduction.
    This is a critical unverified assumption. Provide empirical evidence (e.g., a
    scatter plot of BS vs. reward variance across datasets) or a sensitivity analysis
    showing robustness if this monotonicity does not strictly hold.
- id: bc7e0f1c78e1
  severity: science
  text: Table 1 and Table 2 report performance gains (e.g., +7.9% on Llama3.1) without
    standard deviations or statistical significance tests (e.g., t-tests, confidence
    intervals). Given the small sample sizes of some benchmarks (e.g., AIME24 has
    30 problems), these gains may not be statistically significant. Report variance
    across multiple seeds or statistical tests.
- id: 40ff86d5c04a
  severity: science
  text: The ablation study in Table 4 (tab:comp) shows component contributions but
    lacks error bars or significance testing. With only average scores reported, it
    is unclear if the observed drops (e.g., 0.9 points for BS->Ent) are robust or
    within noise. Include variance estimates or multiple runs.
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:35:26.906001Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents APPO, a method for fine-grained credit assignment in agentic RL, supported by extensive experiments on 13 benchmarks. The central claim—that branching at high-impact decision points (identified by the Branching Score) outperforms coarse-grained or entropy-only methods—is supported by consistent empirical gains across diverse tasks and model sizes. The pilot study (Figure 1) provides reasonable motivation, showing that token entropy alone is a noisy proxy for decision significance.

However, the scientific evidence has notable gaps regarding statistical rigor and theoretical assumptions. First, the main results in Tables 1 and 2 report only mean accuracy scores. Several benchmarks, particularly AIME24/25 (30 problems) and Bamboogle (125 problems), have small sample sizes where variance is high. Without reporting standard deviations, confidence intervals, or results from multiple random seeds, it is impossible to determine if the reported improvements (e.g., +7.9% on Llama3.1) are statistically significant or due to chance. The authors should report variance across at least 3-5 seeds and perform significance testing (e.g., paired t-tests) against the strongest baselines.

Second, Theorem 1 (Variance Reduction) relies on the assumption that the conditional reward variance is monotone in the Branching Score (BS). This is a strong assumption that is not empirically validated in the text. The proof holds only if high-BS tokens indeed correspond to high-variance decision points. The authors should provide an empirical analysis (e.g., a plot of BS vs. observed reward variance) to justify this assumption or discuss the robustness of the method if the monotonicity is weak.

Finally, the ablation studies (Table 4) and scaling analysis (Table 3) lack error bars. While the trends are clear, the magnitude of the drops (e.g., 0.9 points when removing the future-aware term) is small relative to the potential variance in these benchmarks. Including variance estimates would strengthen the claim that each component is strictly necessary. The current evidence is suggestive but not yet rigorous enough to fully support the magnitude of the claims without statistical validation.
