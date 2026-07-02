---
action_items:
- id: 02ef5eb63124
  severity: writing
  text: 'Ambiguity in Step-Level Divergence (Section 3.2): The definition of the subset
    $\mathcal{K}_t$ (Eq 11) is logically opaque. The text describes selecting the
    "top-$k$ most confident tokens," but the equation $\sum |\mathcal{K}_t| = L$ suggests
    a partitioning of the sequence length. It is unclear if $k$ is a fixed hyperparameter
    per step or if the set size varies. Furthermore, Eq 12 averages the KL divergence
    over $\mathcal{K}_t$. If $\mathcal{K}_t$ is selected based on confidence, the
    supervision'
- id: 0e092c32a3db
  severity: writing
  text: 'Causal Link in "New Knowledge" Claim (Section 4.3): The paper argues that
    the AR-style baseline fails because the "Overlap Top-$K_t$" is near 1, implying
    no new knowledge transfer. This is a correlation presented as a causal mechanism.
    High overlap could simply indicate that both the student and teacher (even with
    different conditioning) agree on the most probable tokens for a given task. The
    paper fails to provide a logical argument for *why* suffix conditioning (self-future)
    structurally neces'
- id: 1684de9f3dbe
  severity: writing
  text: 'The "Self-Future" Paradox (Section 3.3 & 4.4.4): The method relies on the
    student generating a trajectory, and the teacher being conditioned on the *final*
    answer of that trajectory (Eq 9). In the early stages of training, the student''s
    final answer is likely incorrect. Logically, conditioning the teacher on an incorrect
    "future" should guide the student toward that incorrect answer, reinforcing errors.
    The paper mentions a "Fix teacher" strategy (App 5.1) and a "Compute only on Correct
    Generati'
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T04:39:06.739358Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper is generally strong in its high-level motivation: adapting On-Policy Self-Distillation (OPSD) to Diffusion LLMs (dLLMs) requires changing both the conditioning mechanism (prefix to suffix) and the supervision granularity (token to step). The argument that AR-style prefix conditioning is incompatible with dLLMs' arbitrary-order generation is well-founded.

However, there are specific logical gaps in the mathematical formulation and the causal explanation of the results:

1.  **Ambiguity in Step-Level Divergence (Section 3.2):** The definition of the subset $\mathcal{K}_t$ (Eq 11) is logically opaque. The text describes selecting the "top-$k$ most confident tokens," but the equation $\sum |\mathcal{K}_t| = L$ suggests a partitioning of the sequence length. It is unclear if $k$ is a fixed hyperparameter per step or if the set size varies. Furthermore, Eq 12 averages the KL divergence over $\mathcal{K}_t$. If $\mathcal{K}_t$ is selected based on confidence, the supervision is biased toward high-confidence tokens. The paper does not logically justify why this specific bias is beneficial for dLLMs compared to a uniform step-level average, nor does it clearly define the selection algorithm.

2.  **Causal Link in "New Knowledge" Claim (Section 4.3):** The paper argues that the AR-style baseline fails because the "Overlap Top-$K_t$" is near 1, implying no new knowledge transfer. This is a correlation presented as a causal mechanism. High overlap could simply indicate that both the student and teacher (even with different conditioning) agree on the most probable tokens for a given task. The paper fails to provide a logical argument for *why* suffix conditioning (self-future) structurally necessitates a lower overlap or higher information gain compared to prefix conditioning in the specific context of diffusion denoising. Without this mechanism, the claim that the performance gap is *due* to "new knowledge" rather than just better alignment with the diffusion process is weak.

3.  **The "Self-Future" Paradox (Section 3.3 & 4.4.4):** The method relies on the student generating a trajectory, and the teacher being conditioned on the *final* answer of that trajectory (Eq 9). In the early stages of training, the student's final answer is likely incorrect. Logically, conditioning the teacher on an incorrect "future" should guide the student toward that incorrect answer, reinforcing errors. The paper mentions a "Fix teacher" strategy (App 5.1) and a "Compute only on Correct Generations" strategy (App 5.2), but the core method description in Section 3.3 does not explicitly state that the teacher construction *requires* a correct final answer to be valid. If the method is applied to incorrect trajectories, the logical consistency of "learning from self-future" breaks down. The paper needs to clarify if the "on-policy" loop is strictly gated by correctness, which would make it a form of filtered on-policy learning rather than pure on-policy.
