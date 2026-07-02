---
action_items:
- id: 4f51fdc44d3c
  severity: writing
  text: The manuscript relies heavily on domain-specific acronyms and jargon that
    are not defined at their first occurrence, creating a barrier for non-specialist
    readers. Specifically, the terms 'AR' (Augmented Reality), 'DiT' (Diffusion Transformer),
    'DMD' (Distribution Matching Distillation), 'FFN' (Feed-Forward Network), 'NFEs'
    (Network Function Evaluations), and 'CFG' (Classifier-Free Guidance) are introduced
    in the Abstract, Introduction, or early Method sections without expansion. For
    instance, '
artifact_hash: ad807d68c3634218d8a37b306582366b9db8e405a9dcf34fb28dd7323fcbdd9e
artifact_path: projects/PROJ-807-liveedit-towards-real-time-diffusion-bas/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:47:09.124627Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and jargon that are not defined at their first occurrence, creating a barrier for non-specialist readers. Specifically, the terms 'AR' (Augmented Reality), 'DiT' (Diffusion Transformer), 'DMD' (Distribution Matching Distillation), 'FFN' (Feed-Forward Network), 'NFEs' (Network Function Evaluations), and 'CFG' (Classifier-Free Guidance) are introduced in the Abstract, Introduction, or early Method sections without expansion. For instance, 'AR-oriented' appears in the Abstract before 'AR' is defined, and 'DiT' is used in the Introduction without spelling out 'Diffusion Transformer'.

Furthermore, the term 'chunk' is used repeatedly (e.g., 'chunk-by-chunk', 'chunk-wise') to describe the temporal processing unit, yet the paper never explicitly defines what constitutes a 'chunk' (e.g., number of frames, duration) until perhaps implicitly in the implementation details, leaving the reader to guess the granularity of the operation. The phrase 'naively truncated' in the Introduction is also stylistically questionable; 'simply' or 'directly' would be more neutral and precise.

To improve accessibility, the authors should ensure every acronym is spelled out upon its first appearance in the text. Additionally, the term 'chunk' should be explicitly defined with its specific parameters (e.g., 'a temporal chunk of 3 frames') in the Method section where it is first introduced as a core concept. Replacing subjective adjectives like 'naively' with neutral technical descriptors will also enhance the professional tone of the paper.
