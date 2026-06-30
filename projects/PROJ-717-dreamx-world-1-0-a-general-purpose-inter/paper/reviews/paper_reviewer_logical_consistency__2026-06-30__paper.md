---
action_items:
- id: a7876ca5b86a
  severity: writing
  text: Clarify if the 0.14 point difference in Table 1 (PRoPE vs E-PRoPE) is statistically
    significant to support the 'comparable' claim.
- id: 198e70f78eb2
  severity: science
  text: Reframe the claim that DMD-forcing prevents camera degradation; data shows
    a 11.75 point drop in long-horizon control, suggesting it only mitigates the rate
    of decay relative to baselines.
- id: f8f44ef7f68c
  severity: science
  text: Address how memory evaluation logic holds if camera control errors exceed
    the retrieval thresholds used to identify revisit pairs.
artifact_hash: dd358f57d42e68a3445f4b34d5b2202a60d20e2d68878dcf007801dde467660f
artifact_path: projects/PROJ-717-dreamx-world-1-0-a-general-purpose-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T05:17:01.472996Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent narrative linking data curation, architectural modifications (E-PRoPE), training strategies (DMD-forcing, RL), and evaluation. However, there are minor logical gaps between the stated mechanisms and the quantitative evidence provided in specific sections.

First, regarding the **E-PRoPE efficiency claim**: The text in `sections/camera_training.tex` asserts that E-PRoPE achieves "comparable trajectory-following precision" to full PRoPE. Table 1 shows a score of 73.89 for PRoPE and 73.75 for E-PRoPE. While numerically close, the text does not explicitly state that this difference is statistically insignificant or within the margin of error. Without this clarification, the logical leap from "0.14 point difference" to "comparable" is slightly weak.

Second, the **causal claim regarding long-horizon camera control** in `sections/dmd_forcing.tex` requires stronger support. The text states that DMD-forcing is introduced to prevent "degraded camera controllability over long sequences." However, Table 3 (`sections/evaluation.tex`) reveals that the Camera Control score for the proposed model drops from 73.75 (5s) to 62.03 (30s). While the model outperforms baselines (which drop to ~63-65), the absolute degradation is significant. The logic that the mechanism "mitigates" degradation is sound if compared to a baseline, but the text implies a more robust preservation of control than the data suggests. The argument would be logically tighter if it explicitly framed the improvement as a "reduced rate of degradation" rather than a general prevention of degradation.

Third, the **logic of the Memory Evaluation** in `sections/evaluation.tex` contains a potential assumption gap. The evaluation relies on "geometry-based retrieval" to identify revisit pairs using specific thresholds ($\tau_\theta=2^\circ$, $\tau_t=0.1$). The paper admits that camera control is imperfect, especially over long horizons. If the camera control error exceeds these thresholds, the "revisit" pairs identified by the metric might not be true geometric revisits. The paper does not explicitly address how the evaluation logic holds up if the camera control error exceeds the retrieval thresholds, which could invalidate the "memory" conclusion if the metric is measuring consistency of a *different* location due to pose error.

These issues do not invalidate the core contributions but require clarifications in the text to ensure the conclusions strictly follow from the premises and data presented.
