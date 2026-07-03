---
action_items:
- id: af78220d2aba
  severity: science
  text: The claim that MPI is 'equivalent to a steepest ascent optimization' (Sec
    3.3) is unsupported. Eq. 10 shows structural similarity, not equivalence. The
    adaptive step-size is not proven to match the optimal step-size for steepest ascent
    on the manifold, weakening the theoretical claim.
- id: 0cf0dd9eec5a
  severity: science
  text: The argument that 'aggressive alignment disrupts stability' (Sec 4.1) with
    10 iterations contradicts standard power iteration convergence. The paper lacks
    a mechanism (e.g., gradient variance analysis) to explain why tighter alignment
    to the principal direction would destabilize the optimizer.
- id: 41dee747d40f
  severity: science
  text: The load balancing improvement is attributed to 'retraction design' (Sec 4.1),
    yet the ablation (Fig 4) shows the 'Retraction-only' baseline achieves similar
    balance. This suggests normalization, not the power iteration interaction, drives
    the benefit, weakening the causal claim for the full method.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:59:08.218032Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper is generally sound in its high-level narrative: the motivation (router-expert misalignment) leads to a proposed solution (aligning with principal singular directions via power iteration), which is then empirically validated. However, specific causal claims and theoretical equivalences lack rigorous support, creating gaps between premises and conclusions.

First, in Section 3.3 ("From Maximum Projection Constraints to Manifold Power-Iteration"), the authors claim their update rule is "equivalent to a steepest ascent optimization." The derivation in Equation 10 shows that the update direction $\Delta \vr_M$ shares a structural form with the projected gradient $\Delta \vr_g$. However, the paper treats this structural similarity as mathematical equivalence. The adaptive step-size in $\Delta \vr_M$ (the denominator term) is derived from the power iteration process, not from an optimization line-search or manifold geometry argument. Asserting equivalence without proving that this specific step-size yields the same trajectory or convergence rate as true steepest ascent is a logical leap. The conclusion that the method is "tailored for maximum projection constraints" is plausible, but the claim of equivalence is unsupported.

Second, the explanation for the failure of 10 power iterations (Section 4.1) is logically weak. The authors state that "aggressive alignment disrupt the stability of router optimization." Standard power iteration theory suggests that more iterations lead to a more accurate estimate of the principal singular vector, which should theoretically improve the alignment objective. The observed performance drop (loss increase, downstream drop) is attributed to "stability," but no mechanism is provided. Why would a more accurate alignment with the expert's dominant direction destabilize the training? Is it due to overfitting the current batch's expert weights? Is it a gradient variance issue? Without a theoretical or empirical analysis of the gradient dynamics or spectral properties under multiple iterations, the causal link between "tighter alignment" and "instability" remains an assertion rather than a derived conclusion.

Third, the attribution of load balancing improvements to the "retraction design" (Section 4.1) is contradicted by the ablation results. The authors claim the improved balance is an "unexpected bonus" of the retraction. However, Figure 4 and the accompanying text note that the "Retraction-only" baseline (which performs normalization without the power iteration step) exhibits a "similar balance loss distribution" to the full MPI method. If the retraction alone achieves the balance, the causal claim that the *combination* of power iteration and retraction (the core novelty) is responsible for the load balancing benefit is weakened. The data suggests the normalization constraint is the primary driver, yet the paper frames the entire "Power-then-Retract" paradigm as the cause.

These issues do not invalidate the empirical results but require clarification to ensure the theoretical claims and causal attributions are logically supported by the presented evidence.
