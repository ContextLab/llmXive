---
action_items:
- id: 6f81f79f35f4
  severity: writing
  text: The manuscript suffers from significant jargon overuse, relying heavily on
    unexplained acronyms and marketing-style terminology that obscures meaning for
    non-specialist readers. The term "Physical AI" is used repeatedly as a proper
    noun without definition, creating an immediate barrier to entry. Similarly, "Native"
    is used as a modifier for "Pre-training Paradigm" and "Unified Architecture" without
    technical justification, functioning more as a buzzword than a descriptor. Acronyms
    are frequently
artifact_hash: 926e7dfe86ab0c8e4b8d20a90a842eec681ad7b82ae76075a7b3082533c6260d
artifact_path: projects/PROJ-740-kairos-a-native-world-model-stack-for-ph/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T18:03:55.219359Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript suffers from significant jargon overuse, relying heavily on unexplained acronyms and marketing-style terminology that obscures meaning for non-specialist readers. The term "Physical AI" is used repeatedly as a proper noun without definition, creating an immediate barrier to entry. Similarly, "Native" is used as a modifier for "Pre-training Paradigm" and "Unified Architecture" without technical justification, functioning more as a buzzword than a descriptor.

Acronyms are frequently introduced without definition. "CEDC," "SOTA," "WAM," "DiT," "GLA," "SWA," "DSWA," "MoT," "DPO," "SFT," "VAE," "CoT," "DMD," and "CM" all appear in the text or tables before being spelled out. For instance, in Section 2.1, the text lists "SWA, DSWA, GLA" without defining them, and later in Section 5.1, "DMD" and "CM" are used without prior expansion. Table 1 relies entirely on acronyms like "T2I" and "N2V" which are only defined in footnotes, forcing the reader to cross-reference constantly.

Furthermore, the paper uses dense technical shorthand like "FP8," "INT8," and "INT4" in Section 5.2 without clarifying the bit-depth or format for a general audience. The consistent failure to define these terms at their first occurrence violates standard academic writing practices and unnecessarily excludes readers who are not deeply embedded in the specific sub-fields of diffusion models and robotics. The text should be revised to spell out all acronyms upon first use and replace vague marketing terms like "Native" with precise technical descriptions.
