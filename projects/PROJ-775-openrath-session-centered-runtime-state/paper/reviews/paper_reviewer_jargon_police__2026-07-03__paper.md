---
action_items:
- id: ed80ae35fc91
  severity: writing
  text: The manuscript relies heavily on specialized software engineering and programming
    language jargon that creates a barrier for non-specialist readers, particularly
    those in social sciences, humanities, or general computer science who are not
    familiar with specific runtime architecture patterns. In the Abstract, the term
    "backend-aware" is used to describe the Session object without defining what a
    "backend" is in this context (e.g., an execution environment, a sandbox provider,
    or a cloud service)
artifact_hash: b43d862ac677a6650e267995c2525b6b2c2aa8062f07856fac7d91db4441a929
artifact_path: projects/PROJ-775-openrath-session-centered-runtime-state/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:44:01.657862Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized software engineering and programming language jargon that creates a barrier for non-specialist readers, particularly those in social sciences, humanities, or general computer science who are not familiar with specific runtime architecture patterns.

In the **Abstract**, the term "backend-aware" is used to describe the `Session` object without defining what a "backend" is in this context (e.g., an execution environment, a sandbox provider, or a cloud service). Similarly, "lineage metadata" is used; "lineage" is a data provenance term that should be replaced with "history of changes" or "branch history" to improve clarity. The phrase "evidence-gated" appears in the contributions list (Section 1.3) and later sections; this is internal protocol jargon that should be defined as "claims pending verification" or similar plain language.

In **Section 1.2**, the authors describe `Memory` as an "agent-bound persistent state plane." The word "plane" here is unnecessary geometric jargon for a "layer" or "level" of storage. The term "first-class" is used repeatedly (e.g., "first-class runtime value") to denote importance or explicit handling. While standard in programming language theory, it is jargon that should be replaced with "primary" or "explicit" for a general audience.

**Section 4** introduces "JSONL" without defining the acronym (JSON Lines). While common in data engineering, it is not universal. Additionally, the text mentions a "smoke suite" and "smoke tests" in **Section 7** and **Section 9**. This is software testing jargon that should be briefly explained (e.g., "basic verification tests") to ensure all readers understand the nature of the evaluation.

Finally, the term "composable" is used in the Abstract and Section 1.2. While precise in functional programming, it is jargon that can be replaced with "able to be combined" or "modular" to broaden accessibility. The paper would benefit from a glossary or inline definitions for these terms to ensure the core argument about runtime state is accessible to a wider academic audience.
