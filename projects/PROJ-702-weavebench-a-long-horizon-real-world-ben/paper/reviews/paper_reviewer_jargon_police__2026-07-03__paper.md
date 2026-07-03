---
action_items:
- id: deb3e3ba7534
  severity: writing
  text: The manuscript relies heavily on domain-specific jargon and undefined acronyms
    that create barriers for non-specialist readers. The most critical issue is the
    use of "CUA" (Computer-Use Agent) in the very first sentence of the Introduction
    without expansion. Similarly, "MCP" (Model Context Protocol) is used in Section
    1 and Table 1 without definition, assuming the reader is already familiar with
    this specific protocol. The term "rollouts" is used frequently (e.g., Section
    1, Section 3.4) to desc
artifact_hash: fe47fd5151ed0fa01e324bf6a3d1eb3486f522739d02266159e873e4cf63e576
artifact_path: projects/PROJ-702-weavebench-a-long-horizon-real-world-ben/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:08:14.825275Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific jargon and undefined acronyms that create barriers for non-specialist readers. The most critical issue is the use of "CUA" (Computer-Use Agent) in the very first sentence of the Introduction without expansion. Similarly, "MCP" (Model Context Protocol) is used in Section 1 and Table 1 without definition, assuming the reader is already familiar with this specific protocol.

The term "rollouts" is used frequently (e.g., Section 1, Section 3.4) to describe agent execution attempts. While standard in Reinforcement Learning, it is jargon that should be replaced with "agent trajectories" or "execution attempts" to improve accessibility. The metric "PassRate" is introduced in the Abstract and Section 1 without a clear definition of what constitutes a "pass" until Section 3.4, where the threshold $\tau=0.8$ is finally mentioned. This metric name should be defined earlier.

In Section 3.1, the properties P1, P2, and P3 are introduced as labels before their full definitions are provided in the subsequent text. These should be defined immediately or introduced with their full names first. Table 1 uses the abbreviation "X-app" without defining it in the caption or notes, making the column header opaque to readers unfamiliar with the authors' internal shorthand.

The term "backbone" is used in Section 4.1 to refer to the underlying language models. Replacing this with "base model" or "underlying LLM" would be more precise and less jargon-heavy. Finally, the term "ablation" in Section 4.3, while standard in ML, could be clarified as "single-channel restriction" or "controlled removal" to ensure the experimental design is clear to a broader audience. These changes are essential to ensure the paper's contributions are accessible beyond the immediate subfield of agent benchmarks.
