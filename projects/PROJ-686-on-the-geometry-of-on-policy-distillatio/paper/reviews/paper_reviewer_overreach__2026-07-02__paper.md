---
action_items:
- id: c17742ff6737
  severity: writing
  text: The claim that OPD is 'not merely an intermediate point' (Abstract, Intro)
    overstates the evidence. The data shows OPD occupies a position *between* SFT
    and RLVR on all metrics (sparsity, rotation, drift). The distinction is one of
    degree (a 'relaxed' regime), not a fundamentally different categorical state.
    The text should be tempered to reflect that OPD is a distinct *point* on the continuum,
    not a separate regime.
- id: 373f95f02940
  severity: writing
  text: The assertion that the locked subspace is 'functionally sufficient' (Abstract,
    Sec 5) extrapolates beyond the provided data. The experiment shows performance
    is *preserved* under a rank-16 constraint, but this does not prove the subspace
    is the *only* sufficient path or that the full-rank trajectory adds no value.
    The claim should be qualified to state that the early subspace is 'sufficient
    to maintain performance' rather than 'functionally sufficient' in a general sense.
- id: 502ebb50d443
  severity: writing
  text: The mechanistic explanation in Section 4.3 ('A Relaxed Three-Gate Account')
    presents a theoretical derivation as a definitive explanation for the observed
    geometry. The paper admits in the Limitations that these are 'mechanistic explanations
    consistent with the evidence, rather than complete causal... theories.' The main
    text should avoid definitive causal language (e.g., 'This yields...', 'This explains...')
    and instead frame these as plausible hypotheses consistent with the data.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:32:11.218391Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the distinctiveness of On-Policy Distillation (OPD) that slightly overreach the empirical evidence provided.

First, the abstract and introduction repeatedly characterize OPD as "not merely an intermediate point" but as inducing its "own update geometry" and occupying a "distinct parameter-space regime" (Abstract; Introduction). However, the data in Section 4 (Table 1, Figure 1) consistently places OPD *between* SFT and RLVR on every metric: update sparsity (51.6% vs 8.1% and 77.2%), principal-angle rotation (~1° vs >10° and <0.5°), and spectral drift. The authors define this as a "relaxed off-principal regime," which is effectively a description of an intermediate position with specific properties. Claiming it is a "distinct regime" rather than a specific point on the SFT-RLVR continuum risks over-interpreting a gradient difference as a categorical one. The language should be adjusted to emphasize that OPD occupies a *specific, stable region* within the spectrum, rather than implying it exists outside the interpolation logic.

Second, the claim of "functional sufficiency" for the locked subspace (Abstract; Section 5) is slightly too strong. The experiment in Figure 5 demonstrates that constraining training to the early rank-16 subspace *preserves* performance compared to unconstrained training. While this shows the subspace is *sufficient* to achieve the result, it does not prove that the full-rank trajectory is unnecessary or that the subspace is the *unique* functional manifold. The phrasing "functionally sufficient" implies a completeness that the ablation does not strictly prove (i.e., it doesn't rule out that the full trajectory might offer better convergence speed or robustness to distribution shift, even if final accuracy is similar). The text should clarify that the early subspace is sufficient to *maintain* the observed performance, rather than being the sole functional driver.

Finally, the "Relaxed Three-Gate Account" in Section 4.3 presents a theoretical derivation (Eqs. 10-14) as a definitive explanation for the observed geometry. While the authors correctly note in the Limitations that these are "mechanistic explanations consistent with the evidence, rather than complete causal... theories," the main text uses definitive causal language (e.g., "This yields larger effective updates," "This explains why..."). Given that the derivation relies on assumptions (e.g., local quadratic budget, specific covariance structures) that are not empirically verified in the paper, the claims should be softened to reflect that this is a *plausible* mechanistic hypothesis consistent with the data, rather than a proven causal account.
