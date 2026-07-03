---
action_items:
- id: 1f63a2fcf3c0
  severity: writing
  text: The manuscript contains several instances of specialized jargon and acronyms
    that are used without definition, which conflicts with the goal of making the
    work accessible to non-specialist readers. First, the term "block-causal attention"
    appears in the Abstract and Introduction as a central architectural component.
    While the paper explains that it enables incremental streaming, it does not define
    what distinguishes "block-causal" from standard "causal" attention. A brief plain-language
    explanat
artifact_hash: 17b9da44bd0e95030f93bbc19c09a0e8be715a82553be99ad52037aacf918aae
artifact_path: projects/PROJ-790-wan-streamer-v0-1-end-to-end-real-time-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:37:24.704348Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript contains several instances of specialized jargon and acronyms that are used without definition, which conflicts with the goal of making the work accessible to non-specialist readers.

First, the term **"block-causal attention"** appears in the Abstract and Introduction as a central architectural component. While the paper explains that it enables incremental streaming, it does not define what distinguishes "block-causal" from standard "causal" attention. A brief plain-language explanation (e.g., "attention that looks back only within fixed time blocks to allow parallel processing") would significantly improve clarity.

Second, **"flow-matching"** and **"conditional flow matching"** are introduced in Section 2.1 without definition. These are specific generative modeling techniques distinct from the more widely known "diffusion" or "noise prediction" methods. The text assumes the reader understands that this involves learning velocity fields to transport noise to data. A one-sentence clarification would help general readers grasp the novelty of the generation method.

Third, the acronym **"KV-cache"** (Key-Value cache) is used repeatedly in Sections 1 and 2.4 to describe the mechanism for preserving state. This is a standard optimization term in LLM serving but is not defined. The paper should spell out "Key-Value cache" at its first occurrence.

Fourth, **"VAE"** (Variational Autoencoder) is used in Section 1 ("causal audio and video VAEs") before the full term is explicitly defined in the text. While common in the field, the paper's commitment to reducing jargon suggests it should be spelled out upon first use.

Finally, the phrase **"streaming units"** is used to describe the 160 ms chunks of data processed by the model. This is a specific implementation detail that is not defined. Clarifying that these are "fixed-duration time blocks of input/output data" would remove ambiguity for readers unfamiliar with streaming inference pipelines.

Addressing these definitions will align the paper with its stated goal of being accessible to a broader audience beyond immediate specialists in streaming inference and diffusion models.
