---
action_items:
- id: 02a497f70a76
  severity: writing
  text: Qualify the novelty claim in Contributions (Intro) regarding 'first to introduce
    multimodal skill package' given citations to Mirage-1 and XSkill.
- id: c2e6a6b7a2bb
  severity: science
  text: Add statistical significance tests (e.g., t-tests, confidence intervals) to
    Table 1 and 2 results to support claims of 'significant gains'.
- id: 8996dcce7d2f
  severity: writing
  text: Clarify that 'avoiding over-anchoring' is an inference from ablation results
    rather than a directly measured phenomenon in Section 3.4.
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T20:24:10.951965Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a well-motivated framework for multimodal procedural knowledge. However, several claims overreach the provided evidence and require calibration.

First, the novelty claim in the Contributions list states: "To the best of our knowledge, we are the first to introduce the **multimodal skill package**" (Introduction). This is contradicted by the Related Work section, which explicitly cites Mirage-1 ("hierarchical multimodal skills") and XSkill ("extracts skills from visually grounded experience"). While MMSkills proposes a specific structure (state cards + keyframes), claiming to be the "first" to introduce multimodal skill packages broadly is inaccurate. Please qualify this claim to reflect the specific representation (e.g., "first to propose state-conditioned packages with explicit verification cues").

Second, the Abstract and Section 4.1 claim "significant gains" across benchmarks. The tables report mean success rates without standard deviations, confidence intervals, or significance tests (e.g., paired t-tests). Without statistical validation, asserting "significant" improvements is an overreach. Please add error analysis or rephrase to "consistent improvements" if statistical testing is not feasible.

Third, the paper attributes performance gains to "avoiding over-anchoring to reference screenshots" (Section 3.4). While ablations show direct loading hurts performance, the paper does not measure "anchoring" directly (e.g., via attention visualization or error analysis of specific failures where the agent followed reference images instead of the live screen). The claim that branch loading solves over-anchoring is inferred from performance drops rather than proven. Please clarify this is a hypothesis supported by ablation rather than a measured phenomenon.

Finally, the claim that the same skill format works for "visually grounded game settings" (Section 4.1) risks overgeneralizing. While results show improvement on Minecraft and Mario, the paper does not analyze why GUI-specific state cards transfer to 3D/2D game environments. This domain shift warrants more discussion on the universality of the representation.

Addressing these points will ensure the paper's claims are strictly supported by the data.
