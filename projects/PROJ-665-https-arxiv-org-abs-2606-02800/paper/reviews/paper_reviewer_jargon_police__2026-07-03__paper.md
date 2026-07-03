---
action_items:
- id: 7d8c91fb94ae
  severity: writing
  text: 'The manuscript exhibits significant jargon density that impedes accessibility
    for non-specialist readers. The term "Physical AI" is used repeatedly as a proper
    noun in the Abstract and Introduction without a definition, effectively gatekeeping
    the paper''s scope to those familiar with this specific industry branding. Similarly,
    critical architectural acronyms are introduced without expansion: "AR" and "DM"
    appear in Section 2.2 without being defined as "autoregressive" and "diffusion"
    (or "denois'
artifact_hash: 868016604b8d9a3bb37ad3c74cf4a71a551a99c22f54a694c5fb583a974a744e
artifact_path: projects/PROJ-665-https-arxiv-org-abs-2606-02800/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T12:40:52.671124Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript exhibits significant jargon density that impedes accessibility for non-specialist readers. The term "Physical AI" is used repeatedly as a proper noun in the Abstract and Introduction without a definition, effectively gatekeeping the paper's scope to those familiar with this specific industry branding. Similarly, critical architectural acronyms are introduced without expansion: "AR" and "DM" appear in Section 2.2 without being defined as "autoregressive" and "diffusion" (or "denoising") respectively. "MoT" is used in Section 2.3 without explicitly stating "Mixture-of-Transformers" first.

In the data and training sections, "SFT" (Section 3.1) and "SDG" (Abstract, Section 4) are used as standard nouns without defining "supervised fine-tuning" or "synthetic data generation." The term "VLA" (Section 1) is used to describe a model class without spelling out "vision-language-action." Furthermore, specific task modes like "FD" and "ID" (Section 2.2, 5.4) are used as acronyms for "forward dynamics" and "inverse dynamics" without prior definition. "MRoPE" (Section 2.4) and "CoT" (Section 3.1) also lack full expansions on first use. Finally, the benchmark "HUE" (Section 5.2) is introduced as "Cosmos HUE" without clarifying the acronym's meaning or full name. These omissions force the reader to guess the meaning of fundamental concepts, violating the principle of plain language.
