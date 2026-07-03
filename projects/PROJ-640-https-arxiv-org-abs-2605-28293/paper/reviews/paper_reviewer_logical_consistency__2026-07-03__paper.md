---
action_items:
- id: 1b2f2d94a209
  severity: writing
  text: 'Theoretical Derivation (Theorem 1): Theorem 1 in Section 2.2 asserts that
    the stopping probability $p(s)$ converges to 0 at a rate of $O(1/s)$ under positive
    mean rewards. The proof sketch in Appendix A.1 states that $\frac{dJ}{dp} < 0$
    and integrates $\frac{dp}{ds} \leq -c p^2$ to yield $p(s) \leq K/s$. The logical
    gap lies in the derivation of the differential inequality $\frac{dp}{ds} \leq
    -c p^2$ from the gradient flow of the policy parameters. The paper does not explicitly
    show how the grad'
- id: 79a252c5deb2
  severity: writing
  text: 'Bias in Advantage Estimation: In Section 3.2, the Position-Specific Advantage
    Estimation (Eq. 5) calculates a baseline $\bar{G}_{i,t}$ conditioned on the subset
    of trajectories that actually reach step $t$ ($L^{(i,j)} \geq t$). While this
    reduces variance by using relevant data, the paper does not logically address
    the potential bias introduced by this conditioning. Trajectories that reach step
    $t$ are inherently a non-random subset (likely those with higher cumulative rewards
    or better feasibil'
- id: ee72fb0e0b2f
  severity: writing
  text: 'Causal Interpretation of Ablation: The ablation study (Table 3) demonstrates
    that removing Stepwise Reward Centering (w/o SRC) results in high CTR but significantly
    lower IoI and IoR. The authors conclude this confirms SRC prevents the "length
    shortcut." However, the logical link is slightly tenuous without explicit data
    on path lengths in the "w/o SRC" condition. The high CTR suggests the model is
    generating feasible paths, but it does not explicitly prove these paths are *longer*
    than the opti'
artifact_hash: 59e5ed22cd4a5270f33af7ca1a0149493d75bf5066fd8fe56191e1e437bc5c6a
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T10:59:35.666435Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent narrative regarding the "length shortcut" in proactive recommendation, where standard policy gradients favor overlong paths due to positive mean step rewards. The proposed rectification mechanisms (Stepwise Reward Centering and Position-Specific Advantage Estimation) logically follow from the identified problem statement. The experimental results generally support the claim that ProRL outperforms baselines and that the specific components address the identified deficiencies.

However, there are gaps in the logical derivation of the theoretical claims and the causal interpretation of the ablation results:

1.  **Theoretical Derivation (Theorem 1):** Theorem 1 in Section 2.2 asserts that the stopping probability $p(s)$ converges to 0 at a rate of $O(1/s)$ under positive mean rewards. The proof sketch in Appendix A.1 states that $\frac{dJ}{dp} < 0$ and integrates $\frac{dp}{ds} \leq -c p^2$ to yield $p(s) \leq K/s$. The logical gap lies in the derivation of the differential inequality $\frac{dp}{ds} \leq -c p^2$ from the gradient flow of the policy parameters. The paper does not explicitly show how the gradient of the objective function with respect to the stopping probability leads to this specific quadratic decay rate. Without this derivation, the specific $O(1/s)$ claim is an assertion rather than a proven consequence of the premises.

2.  **Bias in Advantage Estimation:** In Section 3.2, the Position-Specific Advantage Estimation (Eq. 5) calculates a baseline $\bar{G}_{i,t}$ conditioned on the subset of trajectories that actually reach step $t$ ($L^{(i,j)} \geq t$). While this reduces variance by using relevant data, the paper does not logically address the potential bias introduced by this conditioning. Trajectories that reach step $t$ are inherently a non-random subset (likely those with higher cumulative rewards or better feasibility). Using their average return as a baseline for *all* actions at step $t$ (including those in trajectories that might have stopped earlier if not for the policy) could introduce a systematic bias. The claim that this estimator is "unbiased" or simply "reduces variance" requires a more rigorous argument regarding the independence of the baseline from the action taken at step $t$ within the conditioned set.

3.  **Causal Interpretation of Ablation:** The ablation study (Table 3) demonstrates that removing Stepwise Reward Centering (w/o SRC) results in high CTR but significantly lower IoI and IoR. The authors conclude this confirms SRC prevents the "length shortcut." However, the logical link is slightly tenuous without explicit data on path lengths in the "w/o SRC" condition. The high CTR suggests the model is generating feasible paths, but it does not explicitly prove these paths are *longer* than the optimal length. If the "w/o SRC" model generates paths of similar length to ProRL but simply fails to optimize the target interest (IoI/IoR) due to high variance, the "length shortcut" hypothesis is not fully supported by this specific ablation. The paper needs to explicitly show that the "w/o SRC" model converges to $L_{max}$ (or significantly longer paths) to logically validate that the performance drop is caused by the length bias rather than just general optimization instability.
