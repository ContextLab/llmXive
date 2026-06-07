---
action_items:
- id: ff2b5a588bdc
  severity: writing
  text: Correct Abstract claim regarding text-only performance; Table 2 shows GLM-5V
    macOSWorld Overall is tied (51.75%) and Productivity is worse for MMSkills.
- id: fa9ff904aeb9
  severity: writing
  text: Align model version names in text with bibliography entries (e.g., GLM-5V
    vs GLM-4.5V, Kimi-K2.6 vs K2.5).
- id: 3621ec20f51d
  severity: writing
  text: Nuance 'first to introduce' claim in Introduction given related work on multimodal
    skills (e.g., Mirage-1).
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T00:43:48.840139Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong factual claims that require verification against the provided evidence and citations. First, the Abstract states "MMSkills improve performance over no-skill and text-only skill conditions" (Abstract, line 12). However, Table 2 shows that for GLM-5V on macOSWorld Overall, the text-only condition (51.75%) equals the MMSkills condition (51.75%), and for Productivity, text-only (62.86%) exceeds MMSkills (48.57%). This contradicts the "improve over text-only" claim. The Abstract should be qualified to reflect that improvements are primarily over no-skill baselines, or that gains are consistent over no-skill but mixed over text-only.

Second, there are discrepancies between model versions cited in the text and the bibliography. The text cites "GLM-5V-Turbo \citep{vteam2026glm5vturbonativefoundationmodel}" (Section 4.1, line 12), but the bibliography entry `vteam2026glm45vglm41vthinkingversatilemultimodal` lists the title as "GLM-4.5V and GLM-4.1V-Thinking". Similarly, "Kimi-K2.6 \citep{kimiteam2026kimik25visualagentic}" (Section 4.1, line 12) refers to a bib entry titled "Kimi K2.5: Visual Agentic Intelligence". These version mismatches undermine citation accuracy and should be corrected to ensure the referenced works match the evaluated models.

Third, the contribution "To the best of our knowledge, we are the first to introduce the multimodal skill package" (Introduction, line 135) is challenged by the Related Work citation `xie2025mirage` ("Mirage-1: Augmenting and Updating GUI Agent with Hierarchical Multimodal Skills"). While MMSkills differentiates via state cards, the "first" claim is aggressive given the existence of Mirage-1. Clarifying the novelty relative to Mirage-1 is recommended to avoid factual overstatement.

These issues do not invalidate the core method but require factual corrections to ensure accuracy.
