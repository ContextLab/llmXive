---
action_items:
- id: 8f42325ad1b6
  severity: writing
  text: The manuscript relies heavily on specialized terminology that creates a barrier
    for readers outside the immediate subfield of LLM agent evaluation. While the
    concepts are sound, the density of jargon without immediate definition or plain-language
    equivalents reduces accessibility. First, the term "agentic" is overused as a
    standalone adjective (e.g., "agentic process," "agentic deep research," "agentic
    scenario curation"). In Section 1 and Section 3.2, this term is used to describe
    the methodolo
artifact_hash: 85696f027c2296857479727071f7c34ef0cc40db782dc072c038e2773b79f464
artifact_path: projects/PROJ-680-socrates-towards-reliable-automated-eval/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T17:20:32.160857Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology that creates a barrier for readers outside the immediate subfield of LLM agent evaluation. While the concepts are sound, the density of jargon without immediate definition or plain-language equivalents reduces accessibility.

First, the term **"agentic"** is overused as a standalone adjective (e.g., "agentic process," "agentic deep research," "agentic scenario curation"). In Section 1 and Section 3.2, this term is used to describe the methodology but is never defined. Does it imply autonomy, multi-agent interaction, or a specific tool-use capability? Replacing "agentic" with "agent-driven" or "multi-agent" would immediately clarify the mechanism for a broader audience.

Second, the phrase **"socio-cognitive axes"** and **"socio-cognitive probing"** are introduced in the Abstract and Introduction as if they are standard, self-explanatory categories. While the paper later lists the axes (strategy, emotion, etc.), the umbrella term "socio-cognitive" is not defined. A reader unfamiliar with the specific literature on "social cognition" in AI might not grasp that this refers to "variations in social and psychological factors." Defining this term or using "social-psychological variations" would be more inclusive.

Third, **"trajectory-aware"** (Introduction) and **"multi-state tracking"** (Section 5.2) are technical descriptors that obscure the underlying meaning. "Trajectory-aware" simply means the evaluation considers the sequence of turns, not just the final state. "Multi-state tracking" likely refers to the difficulty of monitoring multiple parties' hidden states simultaneously. These terms should be replaced with their functional descriptions (e.g., "sequence-aware," "multi-party state tracking") to ensure the specific challenge is understood without requiring domain-specific vocabulary.

Finally, the use of **"rejection sampling"** in Section 3.2 to describe the scenario filtering process is technically accurate but potentially confusing in a non-statistical context. Clarifying that this means "filtering out scenarios that resolve on their own" would prevent misinterpretation by readers who might expect a statistical resampling technique.

Addressing these points by defining terms at first use or substituting them with plainer language will significantly improve the paper's readability for a general AI audience without sacrificing precision.
