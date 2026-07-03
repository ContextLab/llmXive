---
action_items:
- id: a07ab80f7b8b
  severity: writing
  text: Section 9 (Limitations) explicitly states 'No safety property is claimed'
    despite the system enabling tool execution and sandboxed code. Authors must add
    a dedicated 'Safety and Risk Mitigation' subsection detailing specific guardrails
    against indirect prompt injection, tool misuse, and sandbox escape, or explicitly
    state the system is for research-only use with no production deployment path.
- id: e01a7f26add6
  severity: writing
  text: The 'Sandbox' and 'Tool' abstractions (Section 4) allow agents to execute
    code and modify files. The paper lacks a discussion on data privacy, specifically
    how sensitive user data or secrets are handled within the session state and whether
    the sandbox enforces network isolation to prevent data exfiltration.
- id: 9dcd99d315d9
  severity: writing
  text: The 'Memory' component is described as a 'session-visible persistent plane'
    (Section 4). The authors must clarify if this memory stores PII or sensitive context
    and whether the system includes mechanisms for user consent, data retention limits,
    or the 'right to be forgotten' (deletion of specific session branches).
artifact_hash: b43d862ac677a6650e267995c2525b6b2c2aa8062f07856fac7d91db4441a929
artifact_path: projects/PROJ-775-openrath-session-centered-runtime-state/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:42:42.888247Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a technical architecture for agent runtime state but currently lacks sufficient depth regarding safety and ethical implications, particularly given the system's capability to execute code and manage persistent memory.

In Section 9 ("Limitations"), the authors state, "No safety property is claimed; tool use and interactive environments enlarge the attack surface, including the data/instruction confusion exploited by indirect prompt injection." While this admission is honest, it is insufficient for a system designed to be auditable and potentially deployed. The paper must include a dedicated subsection on "Safety and Risk Mitigation" that details specific architectural guardrails. For instance, how does the `Session` object prevent an agent from executing arbitrary code that escapes the `Sandbox`? How does the system handle indirect prompt injection where a tool's output might contain malicious instructions for the next agent turn? Without these details, the "audit-first" claim in the abstract is weakened, as the audit cannot verify safety properties that are not defined.

Furthermore, the `Memory` abstraction (Section 4, Table 1) is described as a "persistent-state plane." The paper does not address data privacy concerns. If this memory stores user interactions, does it comply with data protection regulations (e.g., GDPR)? Are there mechanisms for users to consent to memory storage, or to request the deletion of specific session branches containing sensitive information? The current text treats memory purely as a technical construct for state continuity, ignoring the ethical implications of persistent agent memory.

Finally, the `Tool` and `Sandbox` components (Section 4) enable agents to interact with external environments. The paper mentions "backend-aware boundaries" but does not discuss network isolation or resource limits. If an agent is compromised or acts maliciously, what prevents it from exfiltrating data from the host environment or the `Session` state? The authors should either describe the isolation guarantees of the `Sandbox` or explicitly restrict the system's use to controlled, non-production research environments in the limitations section.
