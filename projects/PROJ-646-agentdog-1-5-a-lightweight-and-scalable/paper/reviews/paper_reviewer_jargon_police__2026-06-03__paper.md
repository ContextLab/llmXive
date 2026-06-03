---
action_items:
- id: 7610cf69efe2
  severity: writing
  text: Define acronyms SFT, RL, and MCP in the Abstract. SFT and RL appear in the
    first paragraph without expansion, and MCP servers are mentioned without defining
    the protocol.
- id: e8eb17af63a3
  severity: writing
  text: Define the term ATBench at first use in the Abstract or Introduction. Currently
    it appears as a proper noun without expansion (e.g., Agent Tool Bench).
- id: 4a9bf1da512d
  severity: writing
  text: Define XAI (Explainable AI) in Section 5 title or first paragraph. The term
    is used as a standalone acronym.
- id: db5bafa1cdfe
  severity: writing
  text: Define MoE (Mixture of Experts) in Figure 3 caption or related text. The caption
    references MoE models without defining the architecture type.
- id: cbf843ab90b2
  severity: writing
  text: Simplify the phrase 'influence-function purification' in Section 4.1. This
    is dense statistical jargon that may exclude non-specialist readers; consider
    'data selection using influence functions' or similar.
artifact_hash: 0da3b72044460a5165e111e630e8cbd536a6b5b6d368e4237e9f5b706de0008d
artifact_path: projects/PROJ-646-agentdog-1-5-a-lightweight-and-scalable/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T11:00:38.391479Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on jargon overuse and accessibility for non-specialist readers. The manuscript relies heavily on technical terminology that is often undefined at first appearance, particularly in the Abstract and early sections.

In the **Abstract**, acronyms SFT (Supervised Fine-Tuning), RL (Reinforcement Learning), and MCP (Model Context Protocol?) are used without definition. SFT and RL are standard in the field but should be spelled out for general accessibility in the summary. MCP servers are mentioned without clarifying what the protocol is. Additionally, **ATBench** appears without expansion; while cited, the name itself should be introduced clearly.

In **Section 4**, the phrase "influence-function purification" is highly technical. While the math follows, the term itself acts as a barrier. A plainer description, such as "selecting high-impact training samples," would improve readability without losing precision. The term "Trajectory-level" is used frequently (e.g., Section 4.1); while standard in agent research, "multi-step interaction-level" is clearer for a broader audience.

In **Section 5**, the title "Agentic XAI Attribution" uses XAI without definition (Explainable AI). Furthermore, the caption of **Figure 3** references "MoE models" (Mixture of Experts) without defining the architecture, assuming prior knowledge.

The adjective "**Agentic**" is used repeatedly (e.g., "Agentic AI", "Agentic Safety"). While concise, "Agent-based" is more standard English and may be more accessible. Similarly, "Guardrail" is industry jargon for safety filters; "Safety Filter" or "Safety Monitor" could be used interchangeably or defined upon first use.

Finally, "Finite-state Python simulators" (Section 5.3.1) uses "Finite-state" which implies Finite State Machines. "Finite-state" is correct but technical; "state-based" might be simpler. These changes will not alter the scientific content but will significantly improve readability for reviewers outside the immediate sub-field.
