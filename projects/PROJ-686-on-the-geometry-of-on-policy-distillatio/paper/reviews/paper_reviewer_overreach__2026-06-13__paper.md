---
action_items:
- id: da510cff51d8
  severity: writing
  text: Clarify the Abstract and Introduction to distinguish between static intermediate
    positioning (supported by Table 1) and distinct trajectory dynamics (supported
    by Section 5). Current phrasing 'not merely an intermediate point' risks implying
    static metrics are also distinct.
- id: 784177c596be
  severity: writing
  text: Soften Section 6.2 mechanistic claims. Change 'explaining why objective mixing...
    breaks' to 'suggesting why' to align with the Limitations disclaimer that these
    are not 'complete causal or formal theories'.
- id: 4b53fc4d6865
  severity: writing
  text: Reinforce generalization boundaries in the Discussion. While Limitations note
    variability across families, the Discussion claim that geometry-aware control
    'may make OPD more... transferable' should explicitly reference the reasoning-task
    constraint to prevent overgeneralization.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T00:52:08.458857Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper is generally well-calibrated regarding its empirical claims, with honest limitations stated in `sections/limitation.tex`. However, there are two areas where the phrasing risks overreach or reader misinterpretation.

First, the Abstract and Introduction assert OPD is "not merely an intermediate point between SFT and RLVR" (Abstract, Line 15; `sections/01_introduction.tex`, Line 70). While the trajectory analysis (subspace locking) supports a distinct *dynamic*, the static metrics (sparsity, spectral drift) clearly place OPD *between* SFT and RLVR (Table 1, `sections/04_opd_pnt_framework.tex`, Section 4.2). This phrasing risks implying the static positioning is also distinct, which contradicts the data. Clarifying that OPD is an *intermediate endpoint* with a *distinct trajectory* would prevent overinterpretation of the regime characterization.

Second, Section 6.2 ("Mechanistic view") states that the covariance analysis "explaining why objective mixing... breaks the OPD-like rank trajectory" (`sections/06_low_rank_drivers.tex`, Line 10). This is a strong causal claim based on a theoretical model. While the Limitations section (`sections/limitation.tex`, Line 5) appropriately qualifies this as "consistent with the evidence, rather than complete causal or formal theories," the main text should align with this caution. Changing "explaining why" to "suggesting why" would ensure the main text does not overreach beyond the theoretical model's support.

Additionally, the Discussion suggests geometry-aware control "may make OPD more stable, interpretable, and transferable" (`sections/07_discussion.tex`, Line 12). While framed as a possibility ("may"), this extrapolates from reasoning tasks (Math/Code) to general transferability. The Limitations acknowledge this ("may vary across other model families"), but the Discussion could more explicitly reiterate this boundary to avoid readers assuming broad transferability is proven. These are minor textual adjustments to ensure claims do not exceed the evidentiary support, particularly regarding causal mechanisms and the distinction between static and dynamic properties. The paper's honesty about limitations is a strength, but the main text should reflect this same rigor.
