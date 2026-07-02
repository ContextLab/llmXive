---
action_items:
- id: 6ed87c98610b
  severity: writing
  text: Define 'DiT' (Diffusion Transformer) at first use in Section 3.1. The acronym
    is used repeatedly without expansion, excluding readers unfamiliar with the specific
    transformer variant nomenclature.
- id: a8aa7cd12f75
  severity: writing
  text: Define 'KV caching' (Key-Value caching) upon first mention in the Abstract
    and Section 3.3. While common in LLM circles, this term is jargon that should
    be briefly explained for a general computer vision or robotics audience.
- id: 4016e227784d
  severity: writing
  text: Replace 'rollout' with 'simulation run' or 'sequence generation' in the Abstract
    and Section 3.3. 'Rollout' is domain-specific jargon (often from reinforcement
    learning) that may be opaque to readers from other subfields.
- id: ba65c25f2b88
  severity: writing
  text: "Define 'FVD' (Fr\xE9chet Video Distance) and 'FID' (Fr\xE9chet Inception\
    \ Distance) at their first appearance in Section 4.1. These acronyms are standard\
    \ but should be spelled out for non-specialist readers."
- id: f6bdbd10905a
  severity: writing
  text: Replace 'block-causal' with 'block-wise causal' or explain the specific masking
    mechanism in Section 3.1. The term is a compound jargon that assumes prior knowledge
    of specific attention masking strategies.
artifact_hash: 23197b85ae0bafaaddd0cb8ec8c0f5430ac77fd724ba8930f4eb33d7998307b0
artifact_path: projects/PROJ-641-https-arxiv-org-abs-2605-28816/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T23:23:02.011949Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized acronyms and domain-specific terminology that are not defined at their first occurrence, creating barriers for non-specialist readers.

In the **Abstract**, the term "KV caching" is introduced without definition. While standard in large language model literature, it is jargon that should be expanded to "Key-Value caching" with a brief parenthetical explanation of its function (storing past states for efficient autoregressive generation) to ensure accessibility. Similarly, "rollout" is used as a noun to describe the generation process; replacing this with "simulation run" or "sequence generation" would be more inclusive.

In **Section 3.1 (Preliminaries)**, the acronym "DiT" is used to refer to "Diffusion Transformer" without ever being spelled out. This is a critical omission for a paper claiming to present a new model architecture. The text assumes the reader knows this specific variant of the transformer architecture.

In **Section 4.1 (Quantitative Results)**, the metrics "FVD" and "FID" are used in the text and table headers without their full names (Fréchet Video Distance and Fréchet Inception Distance) being provided in the main body. While these are standard in video generation, the paper's scope extends to robotics and general simulation, where these specific acronyms may not be universally recognized.

Finally, the term "block-causal" in **Section 3.1** and **Section 3.3** is a compound jargon term. While the concept is explained via the masking equation, the term itself should be introduced as "block-wise causal attention" or similar to avoid assuming the reader is familiar with this specific attention pattern nomenclature.

These issues do not invalidate the science but significantly reduce the paper's accessibility to a broader audience, violating the principle of minimizing jargon overuse.
