---
action_items:
- id: e757febf0744
  severity: writing
  text: Define all acronyms at first use (WER, RL, LoRA, DAPO, GRPO, RIR) in the main
    text, not just in appendix or context.
- id: 13f3c71b0eff
  severity: writing
  text: Replace 'In-the-wild^2' in title with plain text (e.g., 'In-the-wild Squared'
    or 'Second-Generation In-the-wild') to avoid math notation confusion.
- id: 4fc7d16d630c
  severity: writing
  text: Expand technical terms like 'atomic acoustic effects', 'agentic check', and
    'backbone preservation' with brief plain-language explanations.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:26:03.487614Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This manuscript exhibits a high density of domain-specific terminology and acronyms that obscure meaning for non-specialist readers. While the core contributions are clear to an ASR expert, the jargon load creates unnecessary barriers to entry.

First, several acronyms are introduced without explicit expansion. In the Abstract, "WER" appears before "word error rates" is fully defined as an acronym (it is spelled out in the Introduction but not linked to the acronym there). In Section 4, "RL training" is mentioned without expanding "Reinforcement Learning". Similarly, "LoRA" is used in Section 4 and the Appendix without defining it as "Low-Rank Adaptation" in the main body. "DAPO" and "GRPO" are cited or used in equations (Appendix) without textual expansion of their full names. "RIR" is used in Section 3 ("RIR convolution") without defining "Room Impulse Response". These must be defined at first occurrence.

Second, the title uses "In-the-wild^2". The superscript notation is mathematical jargon that may confuse readers expecting standard text. A plain-text equivalent should be used.

Third, specific methodological terms rely on metaphorical or niche jargon. "Atomic acoustic effects" is defined but "Atomic" is a metaphor that could be "Basic" or "Fundamental". "Agentic check" relies on current AI buzzwords; "automated verification" is plainer. "Backbone preservation" uses "backbone" as ML jargon for the base model; "base model preservation" is clearer. "Rollouts" is standard RL jargon but should be contextualized for general readers.

Finally, Appendix metrics "CPI" and "BAP" are defined via equations but the acronyms themselves are not spelled out in the text preceding the equations. Ensuring every acronym is defined once and that metaphors are grounded in plain language will significantly improve accessibility without sacrificing technical precision.
