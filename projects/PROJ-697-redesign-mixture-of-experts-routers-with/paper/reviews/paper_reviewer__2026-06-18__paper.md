---
action_items:
- id: 4b60d74b1fcc
  severity: writing
  text: "Clarify the exact experimental setup for the power\u2011iteration step (e.g.,\
    \ number of iterations, choice of expert weight matrix) and provide a brief algorithm\
    \ box summarizing the MPI update."
- id: 6061942822bc
  severity: writing
  text: Add a more detailed discussion of training stability, including quantitative
    analysis of gradient norms or loss spikes when router retraction is omitted.
- id: 8987d23bb487
  severity: writing
  text: "Compare the proposed MPI router against at least one recent alternative router\
    \ design (e.g., Switch Transformer, auxiliary\u2011loss\u2011free load balancing)\
    \ to contextualize the performance gains."
- id: af5dd2e2f1a1
  severity: writing
  text: Provide a reproducibility checklist (hyperparameter table, random seed, code
    repository link) and ensure all cited references in the bibliography are marked
    as verified.
- id: ba2ac3b39cf4
  severity: writing
  text: "Include an error analysis showing cases where MPI improves or harms routing\
    \ decisions, possibly with visualizations of router\u2011expert alignment."
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: Minor writing/clarity issues and missing comparative baselines; experiments
  need stronger justification.
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:38:19.024513Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

## Strengths
- The paper introduces a principled idea: aligning router rows with the principal singular direction of expert weights, grounded in linear algebra and power‑iteration.
- Theoretical derivations connect the update rule to manifold‑constrained gradient ascent, offering an intuitive justification.
- Empirical results across 1B–11B scale models show consistent improvements in pre‑training loss, downstream task accuracy, and load‑balancing metrics.
- The method adds negligible computational overhead and is compatible with existing MoE infrastructure.

## Concerns
- **Experimental breadth**: The paper primarily compares against vanilla MoE; it lacks direct comparisons with other recent router improvements (e.g., Switch Transformers, auxiliary‑loss‑free designs), making it hard to isolate the contribution of MPI.
- **Ablation clarity**: While ablations on power‑iteration and retraction are presented, the choice of expert weight (`W_g`) is only briefly justified. A more systematic study of different weight matrices and iteration counts would strengthen the claim that a single iteration suffices.
- **Stability analysis**: The discussion of numerical instability and the necessity of the retraction step is qualitative. Providing quantitative metrics (e.g., gradient norm trajectories, loss spikes) would better support the design decisions.
- **Reproducibility details**: Hyperparameters are listed in appendices, but a concise reproducibility checklist (random seeds, code URL, exact training schedule) is missing. Additionally, the bibliography verification status is not shown; ensuring all citations are verified is required for acceptance.
- **Writing issues**: Some sections contain redundant phrasing, minor grammatical errors, and occasional informal language (e.g., “we suspect that this reduction might be an artifact…”). A careful editorial pass would improve readability.

## Recommendation
The core idea of Manifold Power‑Iteration for MoE routers is novel and well‑motivated, and the empirical gains are promising. However, to fully assess the contribution, the manuscript needs additional comparative baselines, clearer ablation studies, and stronger reproducibility information. I recommend a **minor revision** focusing on clarifying methodology, expanding the experimental context, and polishing the writing. Once these points are addressed, the paper should be ready for publication.
