---
action_items:
- id: c5512689e5fb
  severity: writing
  text: The manuscript is dense with domain-specific acronyms and abbreviations that
    hinder accessibility for readers outside the immediate niche of generative video
    and robotics. While the technical precision is high, the text frequently assumes
    prior knowledge of terms that should be explicitly defined or replaced with plain
    English. Specifically, the term "6-DoF" appears in the Abstract and Introduction
    without definition. While standard in robotics, a general computer science reader
    may not immediat
artifact_hash: 583182a56bc8cd93d801cd098b02d980b9a48cb375dac6cc8130da68f508615f
artifact_path: projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:04:55.607094Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is dense with domain-specific acronyms and abbreviations that hinder accessibility for readers outside the immediate niche of generative video and robotics. While the technical precision is high, the text frequently assumes prior knowledge of terms that should be explicitly defined or replaced with plain English.

Specifically, the term "6-DoF" appears in the Abstract and Introduction without definition. While standard in robotics, a general computer science reader may not immediately grasp "Degrees of Freedom." Similarly, "nATE" is introduced in Section 5 and used throughout the Appendix without ever being spelled out as "normalized Average Translation Error." This forces the reader to guess the metric's nature or search external literature.

The acronym "DiT" (Diffusion Transformer) is used repeatedly in the Experiments section (e.g., describing LTX, LongCat, Kairos) without a prior definition. While "Transformer" is well-known, the specific "Diffusion" variant is a distinct architectural choice that warrants a brief explanation or full spelling at first use.

Furthermore, the table captions and text rely heavily on "FPP" and "TPP" for First-Person and Third-Person perspectives. These are gaming/VR conventions that should be written out in full in the main text or table headers to ensure clarity for a broader academic audience. Finally, "VLM" is used extensively to describe the evaluation judges (e.g., in Section 5 and Appendix C) but is never defined as "Vision-Language Model."

To improve readability and inclusivity, the authors should perform a pass to ensure every acronym is defined at its first occurrence and consider replacing highly specific jargon (like "DoF" or "DiT") with descriptive phrases where the context allows, or at least providing a brief parenthetical explanation.
