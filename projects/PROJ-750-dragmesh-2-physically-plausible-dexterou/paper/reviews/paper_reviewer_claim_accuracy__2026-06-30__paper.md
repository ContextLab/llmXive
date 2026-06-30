---
action_items:
- id: a305b86e7a21
  severity: writing
  text: The claim that the trajectory-tracking baseline proves 'open-loop replay alone
    is not OOD-robust' (Sec 4) is misleading. Table 1 shows it achieves 1.00 success
    at x1, implying it relies on nominal physics, not just geometry. The drop at x2/x4
    confirms OOD failure, but the text ignores its nominal robustness.
- id: ee32d17f1056
  severity: writing
  text: "The Figure 1 caption claims PICA has the 'highest mean success in all six\
    \ mode\xD7damping settings.' This is false; Table 1 shows 'Traj. tracking' achieves\
    \ 1.00 at x1, exceeding PICA's 0.89. The claim must exclude non-learned baselines\
    \ or be corrected."
- id: 1d42e4cf28e3
  severity: writing
  text: The claim 'no single policy dominates every instance' (Sec 4) is contradicted
    by Table 1 for object 45261. PICA scores 1.00/1.00 (x1), 0.90/0.90 (x2), and 1.00/0.95
    (x4), strictly beating all other methods in every cell for this object.
artifact_hash: aac12eff083d8d7168328cdeef9fdab897d5808d01d31c99a8c36453db9b88d3
artifact_path: projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T13:49:25.418998Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with the provided data in Tables 1 and 2, and the text in Section 4.

First, the claim in the "Main comparison" paragraph (Section 4) that the trajectory-tracking reference "confirms the reference trajectory genuinely drives the target part through contact rather than replaying object states" is logically inconsistent with the data. The text argues that the baseline's drop to 0.71 at x2/x4 proves it is not OOD-robust. However, the baseline achieves 1.00 success at x1 (nominal). If the trajectory were purely geometric and ignored contact dynamics (as implied by "open-loop replay"), it should fail at x1 if the physics were not perfectly matched. The fact that it succeeds at x1 but fails at x2/x4 suggests it *does* rely on nominal physics, making the claim that it proves "open-loop replay alone is not OOD-robust" slightly misleading without acknowledging its nominal robustness. The text implies the baseline is a "geometric" replay, but the data shows it is a "physics-aware" replay that fails under load.

Second, the caption of Figure 1 states: "PICA attains the highest mean success in all six mode×damping settings." This is factually incorrect based on Table 1. At x1 damping, the "Traj. tracking" baseline has a mean success of 1.00, while PICA has 0.89. Therefore, PICA does not have the highest success in the x1 deterministic setting. The claim should be qualified to exclude the non-learned trajectory-tracking baseline or specify "among learned policies."

Third, the text claims "no single method dominates every instance" (Section 4, Para 1). While true for the aggregate, looking at Table 1, for object 45261 (StorageFurn. drawer), PICA achieves 1.00/1.00 at x1, 0.90/0.90 at x2, and 1.00/0.95 at x4. In every single cell for this object, PICA's deterministic and stochastic scores are equal to or higher than any other method (e.g., State-only PPO is 0.10/0.20 at x1, 0.10/0.10 at x2, 0.10/0.10 at x4). The claim of heterogeneity is an overgeneralization for this specific object where PICA strictly dominates.

Finally, the claim in the "Ablation" paragraph that "the full model exceeds either component by at least 0.13 at x4" is accurate (0.56 vs 0.36 and 0.43), but the text later states "the components help along different axes... so they are complementary rather than redundant." The data supports this, but the claim that "the win is therefore the combination... not the temporal encoder by itself" is slightly imprecise. The "w/o GLA" (PICA only) variant has 0.43 at x4, which is significantly better than "w/o PICA" (GLA only) at 0.36. The text implies the temporal encoder alone is weak, but the data shows it provides a baseline of 0.36, which is not negligible. The phrasing could be tightened to reflect that the *combination* yields the largest gain, rather than implying the encoder alone is ineffective.
