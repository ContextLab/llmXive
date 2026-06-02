---
action_items:
- id: 5756bba1f698
  severity: writing
  text: Verify all citation dates and ensure no future-dated references (several 2025-2026
    entries require confirmation)
- id: 7ac31fa4473c
  severity: writing
  text: Complete missing table entries currently shown as '--' in OSWorld results
    table for Gemini 3.1 Pro and Kimi-K2.6
- id: b9044511fa4f
  severity: writing
  text: Strengthen related work differentiation from Mirage-1, XSkill, and CUA-Skill
    with explicit comparison of technical contributions
- id: 9a45d4937879
  severity: writing
  text: Clarify the 'first to introduce' claim with more specific positioning against
    existing multimodal skill literature
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: Minor revisions needed for citation verification, table completeness, and
  clearer differentiation from related work
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T20:18:34.072692Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths

The paper presents a well-motivated and technically sound framework for multimodal procedural knowledge in visual agents. The core contribution—the multimodal skill package combining textual procedures, runtime state cards, and multi-view keyframes—is clearly defined and addresses a genuine gap in existing skill-based agent systems.

The methodology is comprehensive:
- **Skill representation** is concrete and actionable, with explicit state cards encoding when-to-use, when-not-to-use, visible cues, and verification conditions
- **Generator pipeline** is well-structured with five phases (embedding/cluster → planning → merge → text draft → image grounding/audit)
- **Branch loading** mechanism addresses context pressure and reference anchoring problems elegantly

The experimental evaluation is thorough:
- Covers four benchmarks (OSWorld, macOSWorld, VAB-Minecraft, Super Mario Bros)
- Evaluates across six model families (Gemini 3.1 Pro, Gemini 3 Flash, Qwen3-VL-235B, GLM-5V, Kimi-K2.6, Qwen3-VL-8B)
- Ablation studies on skill content (state cards, images) and loading strategy (branch vs. direct)
- Behavioral analysis showing reduced action load and repetitive trajectories

The paper is well-organized with clear figures, tables, and appendices containing prompt templates and algorithm details. Code, data, and skill library are released (GitHub, HuggingFace, website).

## Concerns

1. **Citation date verification**: Several references are dated 2025-2026 (e.g., SkillWeaver, CUA-Skill, SkillX, EvoSkill, SkillClaw, SkillRL, Mirage-1, XSkill, macOSWorld, GLM-5V, Kimi-K2.6). For an arXiv preprint, these future dates require verification to ensure accuracy and proper attribution.

2. **Missing table entries**: Table~\ref{tab:osworld-domain-results} shows "--" for several entries (Gemini 3.1 Pro and Kimi-K2.6 have some missing values). While the note explains cost constraints, the table should be clearer about which specific metrics are unavailable.

3. **Related work differentiation**: The paper cites Mirage-1, XSkill, and CUA-Skill as closely related work but could provide a more explicit technical comparison. What specifically distinguishes MMSkills' state cards and branch loading from these approaches? A comparison table or clearer technical distinction would strengthen the contribution claim.

4. **"First to introduce" claim**: The claim of being first to introduce multimodal skill packages should be more carefully qualified given the existence of Mirage-1 (hierarchical multimodal skills) and XSkill (visually grounded skill extraction). A more precise positioning statement would avoid overclaiming.

5. **Reproducibility details**: While code and data are released, some implementation details (e.g., exact prompt templates for the Generator pipeline, meta-skill specifications) are not fully detailed in the appendices. More implementation specifics would aid replication.

## Recommendation

This is a strong paper with a well-motivated contribution and comprehensive experimental validation. The core ideas are novel and the results are convincing. I recommend **minor_revision** to address the citation verification, table completeness, and related work differentiation concerns. These are primarily editorial and clarification issues that do not require new experiments or major restructuring.

The paper demonstrates that external multimodal procedural knowledge meaningfully complements model-internal priors, particularly for weaker visual agents. The branch loading mechanism is an elegant solution to context pressure and reference anchoring. After addressing the minor concerns above, the paper would be ready for publication.
