---
action_items:
- id: e636cebd4caf
  severity: writing
  text: Remove `(... omitted ...)` placeholders from tables in the LaTeX source to
    ensure the final PDF renders complete data and compiles without warnings.
- id: 92733eb3c97d
  severity: writing
  text: Add a brief subsection or appendix describing the literature search protocol
    (keywords, databases, inclusion criteria) to establish survey rigor.
- id: ce309b45c473
  severity: writing
  text: Verify all `\cite` keys in the `.tex` source match the `reference.bib` entries
    to prevent compilation warnings.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: Comprehensive survey with strong taxonomy; requires minor source cleanup
  and methodology clarification.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T05:18:23.196016Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths
- **Clear Taxonomy:** The three-layer structure (Harness Interface, Harness Mechanisms, Scaling the Harness) provides a coherent framework for organizing the rapidly evolving literature on code-agent systems.
- **Comprehensive Coverage:** The survey spans a wide range of domains (coding assistants, GUI/OS, embodied agents, scientific discovery) and includes recent works up to 2026.
- **Visual Summaries:** The use of figures (e.g., `overview.pdf`, `roadmap_sec2.pdf`) and tables to summarize methods enhances readability and comparison.
- **Forward-Looking:** The "Open Problems" section identifies critical gaps (e.g., oracle adequacy, shared state, safety governance) that guide future research.

## Concerns
- **Source Completeness:** The provided LaTeX source contains placeholders like `(... 19 rows omitted ...)` in tables. These must be removed or completed in the final build to ensure the paper is publication-ready.
- **Methodology Transparency:** As a survey, the paper should explicitly state the literature search protocol (e.g., search strings, databases used, inclusion/exclusion criteria) to establish rigor, which is currently implicit.
- **Bibliography Verification:** While the bibliography is extensive, the provided input is truncated. Ensure all cited works are verified and accessible in the final submission.
- **Repetition:** Some open challenges (e.g., evaluation, safety) are mentioned in multiple sections; minor consolidation could improve flow.

## Recommendation
This paper presents a valuable synthesis of the "code as agent harness" paradigm and is suitable for publication after minor revisions. The reviewers recommend `minor_revision` to ensure the LaTeX source is fully populated (removing table placeholders), the survey methodology is explicit, and all citations are verified. Once these changes are made, the paper will be ready for acceptance.
