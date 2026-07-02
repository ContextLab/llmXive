---
action_items:
- id: c913dbddbbb9
  severity: science
  text: The paper significantly over-claims the magnitude and universality of its
    findings, particularly regarding the "3x" acceleration and the "foresight" mechanism.
    First, the Abstract and Introduction repeatedly assert an "average training acceleration
    of 3x." However, the experimental results in Figure 5 and Section 4.2 present
    a more nuanced picture. While some models show significant speedups, others show
    more modest gains (e.g., ~2x), and the convergence steps vary (10 vs 30-40). Furthermore,
    th
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:07:46.893383Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper significantly over-claims the magnitude and universality of its findings, particularly regarding the "3x" acceleration and the "foresight" mechanism.

First, the Abstract and Introduction repeatedly assert an "average training acceleration of 3x." However, the experimental results in Figure 5 and Section 4.2 present a more nuanced picture. While some models show significant speedups, others show more modest gains (e.g., ~2x), and the convergence steps vary (10 vs 30-40). Furthermore, the EffOPD method introduces a validation step (sampling 50 examples) to select the extrapolation magnitude. The paper fails to rigorously subtract this validation overhead from the total training time to justify the "3x" net speedup claim. This is a classic case of extrapolating a best-case or partial metric to a general average without sufficient evidence.

Second, the central metaphor of "foresight" (Abstract, Intro, Section 1) is an over-interpretation of the data. The paper demonstrates that OPD update directions align with the final solution early (Figure 4). While this indicates "early stabilization," labeling it "foresight" anthropomorphizes the optimization process and implies a predictive capability that the data does not support. The paper should stick to the more precise, descriptive term "Early Low-Rank Lock-in" used in Section 3, rather than the speculative "foresight" narrative.

Third, the theoretical analysis in Appendix A.5 ("A Linearized View of OPD Dynamics") relies on a local quadratic approximation of the loss landscape around the base model. The authors over-extend this local theory to explain the global, non-convex training dynamics and the observed 3x speedup. The limitations section acknowledges the local nature of the theory but does not sufficiently temper the main text's claims that this theory *explains* the efficiency. The connection between the local linearization and the global acceleration is asserted rather than proven.

Finally, the claim that EffOPD requires "no complex hyperparameter tuning" (Abstract) is misleading. The method requires defining an extrapolation schedule (exponential checkpoints) and a validation set size, and the choice of the extrapolation magnitude (k) is critical. The paper presents the validation set as a simple heuristic but does not analyze the sensitivity of the results to the size of this set or the specific extrapolation steps, which are effectively hyperparameters.

To address these over-reaches, the authors must: (1) recalculate and report the net speedup including validation overhead, tempering the "3x" claim to a range; (2) replace the "foresight" metaphor with "early directional stabilization"; (3) explicitly limit the scope of the theoretical claims to the local regime; and (4) clarify the hyperparameter dependencies of EffOPD.
