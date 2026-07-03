---
action_items:
- id: aa996a043f51
  severity: science
  text: Section 3.2 claims JSD ascent caps the advantage on the deliberation side
    to handle heavy tails. However, Lemma 4.3 shows phi(u) is bounded below, meaning
    -phi(u) is bounded above. The text conflates the bound on phi with the bound on
    the advantage, creating a logical gap in justifying why this shape stabilizes
    the negative u regime.
- id: 480143b6c029
  severity: science
  text: 'Section 3.2 asserts the entropy gate is needed because JSD ascent is ''not
    self-terminating.'' This causal claim lacks a premise: the paper does not derive
    why ascent on JSD specifically fails to self-terminate compared to other directions,
    nor why standard descent is self-terminating. The link between ascent and the
    gate requirement is asserted but not derived.'
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T07:22:24.628445Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical flow from the diagnosis of the "shortcut bias" to the proposed "Anti-Self-Distillation" mechanism is generally coherent, but there are specific points where the mathematical justification for the proposed solution does not fully align with the stated claims.

First, in Section 3.2 ("Ascent on Jensen-Shannon divergence"), the authors argue that ascending JSD is chosen because its f-divergence-derived advantage is "asymmetrically bounded," specifically to handle the heavy-tailed distribution of deliberation tokens (where $u_t \ll 0$). The text claims this shape "caps the AntiSD advantage on the deliberation side." However, the mathematical derivation in Appendix Lemma 4.3(iii) shows that $\varphi(u) \ge -0.5 \log 2$. Since the advantage is defined as $A_t = -\varphi(u_t)$, this implies the advantage is bounded *above* by $0.5 \log 2$ when $u_t$ is negative. The text appears to conflate the bound on the function $\varphi$ with the bound on the advantage term, or fails to explicitly map the inequality direction. If the advantage is bounded above, it limits the *positive* reward given to deliberation tokens, which is the correct stabilization mechanism for the heavy-tailed negative $u$ regime. However, the phrasing "caps the AntiSD advantage on the deliberation side" is ambiguous and risks misrepresenting the mathematical constraint derived in the appendix. This requires clarification to ensure the causal link between the JSD shape and the stabilization of heavy-tailed gradients is logically sound.

Second, the necessity of the entropy-triggered gate is justified by the claim that "the JSD ascent direction is not self-terminating." While the paper demonstrates empirically (Figure 4) that removing the gate leads to collapse, the logical premise that JSD ascent *inherently* lacks a self-terminating property compared to the baseline is not derived. The paper does not explain why the ascent on JSD specifically fails to self-terminate (e.g., does the gradient not vanish as distributions diverge?), nor does it contrast this with the self-terminating nature of the standard descent on KL. The argument relies on an unproven assertion about the dynamics of the ascent direction, leaving a gap between the proposed mechanism (ascent) and the required stabilizer (gate).

Finally, the claim in Section 3.1 that the per-token signal $\delta_t = +u_t$ has the "wrong polarity" is well-supported by the PMI analysis. However, the transition to the solution assumes that simply inverting the sign ($-\varphi(u)$) is sufficient to recover the "deliberation" behavior. The paper does not explicitly rule out the possibility that inverting the sign might over-correct, leading to a new bias against "shortcut" tokens that are actually necessary for valid reasoning steps (e.g., confirming a known intermediate result). While the ablation studies show performance gains, the logical argument that the inverted signal perfectly targets "deliberation" without suppressing valid "shortcut" confirmation steps relies on the empirical observation of Figure 2 rather than a theoretical guarantee.
