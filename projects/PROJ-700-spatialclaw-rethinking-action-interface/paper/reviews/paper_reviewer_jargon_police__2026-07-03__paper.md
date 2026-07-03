---
action_items:
- id: 84ed441ac4e8
  severity: writing
  text: The manuscript relies heavily on domain-specific jargon that creates a barrier
    for non-specialist readers, particularly in the Introduction and Method sections.
    First, the term "agentic" is used repeatedly (e.g., "Agentic Spatial Reasoning",
    "agentic loop") without definition. It is a buzzword in the field but means little
    to a general reader. The authors should use "autonomous" or "agent-based" and
    define the concept of an "agent" simply as a system that can make decisions and
    take actions. Sec
artifact_hash: 03b4b7546f79862eef36a0d430e3a6b82062f65b52d01a2c8d4c65b5c5b34086
artifact_path: projects/PROJ-700-spatialclaw-rethinking-action-interface/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T11:12:17.743180Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific jargon that creates a barrier for non-specialist readers, particularly in the Introduction and Method sections.

First, the term **"agentic"** is used repeatedly (e.g., "Agentic Spatial Reasoning", "agentic loop") without definition. It is a buzzword in the field but means little to a general reader. The authors should use "autonomous" or "agent-based" and define the concept of an "agent" simply as a system that can make decisions and take actions.

Second, the phrase **"action interface"** is central to the paper's contribution but is never explicitly defined in plain language. It is treated as a known concept. The authors should clarify this early on, perhaps as "the specific method or language (in this case, code) the AI uses to request help from external tools."

Third, technical terms like **"orchestration space"** (Section 1) and **"perception primitives"** (Section 3.1) are unnecessarily dense. "Orchestration space" could simply be "workspace" or "execution environment," and "perception primitives" could be "basic perception tools" or "pre-defined functions." These terms add cognitive load without adding precision.

Fourth, acronyms and specific technical jargon appear without definition. **"SE(3)"** (Section 4.1) is standard in robotics but obscure to general AI researchers; it should be introduced as "3D rigid body transformations (SE(3))". Similarly, **"AST checker"** (Section 3.2) and **"KV reuse"** (Appendix) use acronyms (Abstract Syntax Tree, Key-Value) that should be spelled out or replaced with plain English descriptions (e.g., "code syntax checker," "caching of model states").

Finally, the term **"backbone"** is used to refer to the underlying VLMs (e.g., "Qwen3.5-397B backbone"). While common in the field, "base model" or "underlying model" is more accessible.

The paper's core idea—using a persistent code environment for spatial reasoning—is clear, but the presentation is cluttered with jargon that excludes readers outside the specific sub-field of agentic systems and robotics. A revision to simplify these terms would significantly improve the paper's accessibility.
