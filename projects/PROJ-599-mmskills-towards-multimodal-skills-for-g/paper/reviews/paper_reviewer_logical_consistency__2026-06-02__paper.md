---
action_items:
- id: 14f18930953b
  severity: science
  text: Correct the claim in Section 3.2 regarding GLM-5V performance on macOSWorld.
    Table 2 shows identical Overall scores (51.75%) for Text-only and MMSkills, contradicting
    the text stating MMSkills improve GLM-5V on this benchmark.
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T20:21:21.398676Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical structure of the MMSkills framework is generally sound. The premise that visual agents require multimodal procedural knowledge (Section 1) follows from the limitation of text-only skills in state recognition. The proposed mechanism (branch loading) logically addresses the context pressure and anchoring risks identified in Section 2.4. The ablation study (Figure 2) supports the causal claim that branch loading and visual grounding are necessary components, as removing them degrades performance. The Generator pipeline (Section 2.3) maintains logical consistency regarding data separation, explicitly stating source trajectories are disjoint from evaluation tasks (Section 3.1, Appendix B), which prevents data leakage from invalidating the performance claims.

However, there is a critical inconsistency between the textual claims in the results and the provided data. Section 3.2 states: "On macOSWorld, MMSkills improve the completed large-model runs, including Gemini 3 Flash and GLM-5V". Table 2 (Auxiliary GUI and game-based visual-agent results) shows that for GLM-5V on macOSWorld, the Overall success rate for Text-only is 51.75% and for MMSkills is 51.75%. There is no improvement for GLM-5V on this benchmark, contradicting the explicit claim in the text. This undermines the generalization argument that MMSkills consistently improve performance across all model families and benchmarks.

Additionally, Section 3.2 claims "Text-only skills help but are less stable across domains". Table 1 supports this for Gemini 3.1 Pro (Text-only 40.76% < No skill 44.08%), and Table 2 shows Qwen3-VL-235B Text-only (43.36%) < No skill (47.55%), which supports the claim. The inconsistency is isolated to the GLM-5V macOSWorld claim.

To restore logical consistency, the authors must either correct the textual claim to reflect the actual data (e.g., "improve... except for GLM-5V on macOSWorld") or verify if the table data contains a typo. Without this correction, the conclusion that MMSkills are universally beneficial lacks full evidentiary support. The rest of the logical chain, from problem formulation to experimental validation, remains coherent.
