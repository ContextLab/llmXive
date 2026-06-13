---
action_items:
- id: 8f12e175148a
  severity: writing
  text: 'Clarify the ''KL loss: Disabled'' setting in Table 3 (Appendix) relative
    to the KL-based objective in Appendix A. The Three-Gate theory relies on a ''distributional
    anchor'' (Gate I), but the table implies no KL regularization. Explicitly state
    that the distillation KL is the anchor and the disabled loss refers to reference-policy
    regularization to avoid confusion about the mechanistic explanation.'
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T00:48:57.257216Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a logically consistent argument regarding the parameter-space geometry of On-Policy Distillation (OPD). The core claims—that OPD occupies a "relaxed off-principal regime" and exhibits "subspace locking"—are well-supported by the defined diagnostics (update sparsity, stable rank, subspace similarity) and ablation studies. The causal chain linking objective composition to rank dynamics is established through controlled perturbations (token sparsification, off-policy rollouts, objective mixing) where only the objective mixing alters the trajectory, supporting the conclusion that the lock is objective-sensitive.

However, there is a minor logical clarity issue regarding the "distributional anchor" in the Three-Gate theory extension (Section 4, Appendix A). The text argues OPD remains anchored via a "local quadratic budget" (Gate I), consistent with RLVR's KL-regularized anchor. Yet, Table 3 (Appendix) explicitly lists "KL loss: Disabled" for the OPD setup. While this likely refers to the reference-policy regularization term distinct from the distillation objective, the terminology creates a potential ambiguity for readers attempting to reconcile the "KL-based anchor" mechanism with the "KL loss: Disabled" configuration. This does not invalidate the empirical results but slightly obscures the logical connection between the theoretical mechanism and the experimental setup.

Additionally, the distinction between "constrained" (Section 3, referring to sparsity/geometry preservation) and "low-dimensional" (Section 5, referring to stable rank) is well-maintained, but the transition between these concepts could be explicitly reinforced to ensure readers do not conflate "off-principal" with "low-rank."

Overall, the logical structure is sound, but clarifying the KL terminology will strengthen the mechanistic argument.
