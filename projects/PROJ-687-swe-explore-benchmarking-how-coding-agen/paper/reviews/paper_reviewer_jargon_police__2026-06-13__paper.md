---
action_items:
- id: 4a3e9af9a3d8
  severity: writing
  text: Replace "trajectory-grounded supervision" with "supervision from agent execution
    paths" in Abstract and Section 3.3 to improve accessibility for non-specialists.
- id: 3e88591bfeff
  severity: writing
  text: Define "Oracle" as "Ideal Baseline" on first use in Section 5.3 to clarify
    it represents perfect context rather than a specific tool.
- id: eebd53b23a86
  severity: writing
  text: Simplify "context-efficiency" to "context usage efficiency" in Section 4.2
    and Abstract to reduce compound jargon density.
artifact_hash: 4f74e000b69de2d67ea831b1e89044d5ab493f7912139c51fbf7fc4d4c2ada92
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T21:59:46.568766Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript introduces SWE-Explore, a benchmark for repository exploration. While the technical contribution is clear, the text relies heavily on specialized jargon that may exclude non-specialist readers, particularly those outside the immediate coding-agent benchmarking community.

Specific instances of jargon overuse include:
1. "Trajectory-grounded supervision" (Abstract, Section 3.3): "Trajectory-grounded" is opaque. Consider "supervision derived from successful agent execution paths".
2. "Context-efficiency" (Abstract, Section 4.2): This compound term is defined later but used early. "Efficiency of context usage" is clearer.
3. "Agentic explorers" (Section 5.1): "Agents that explore" is more accessible.
4. "Oracle" (Section 5.3, Table 3): While standard in IR, "Ideal Baseline" or "Perfect Context" is more descriptive for general readers.
5. "Restricted-context protocol" (Introduction, Section 4.2): "Protocol using limited context" reduces cognitive load.
6. "Line budget" (Abstract): "Limit on code lines" is plainer.
7. "Noise rate" (Section 4.2): "Rate of irrelevant content" is more intuitive.
8. "Resolve rate" (Section 5.2): "Fix success rate" is more direct.

Several acronyms are defined (nDCG, DCG, FUH, CtxEff), which is good practice. However, the density of defined terms in the Metrics section (Section 4.2) creates a barrier. A glossary or simplified introductory text for these metrics would help.

The paper assumes familiarity with SWE-bench variants (Verified, Pro, Multilingual). A brief parenthetical explanation (e.g., "SWE-bench Verified (a high-quality subset)") would aid readability.

Overall, the jargon is consistent with the field but could be simplified to broaden the audience without sacrificing precision. The current density of specialized terms in the Abstract and Introduction risks alienating readers from adjacent fields (e.g., general NLP or software engineering) who might benefit from this work. Simplifying these terms would enhance the paper's impact and accessibility while maintaining technical accuracy.
