---
action_items:
- id: 4ebbd32ce71a
  severity: writing
  text: Define 'mRoPE' and 'Dynamic-NTK' at first use in Section 3 instead of relying
    on Appendix references.
- id: 1b0dde26ea82
  severity: writing
  text: Expand 'SFT' before Section 4.3 usage; do not defer definition to Table 1
    caption.
- id: a25bba557047
  severity: writing
  text: Spell out 'MM-NIAH' and other benchmark acronyms in the Introduction before
    citing them.
- id: 6d47dd352d84
  severity: writing
  text: Clarify 'H20' GPU reference in Appendix for non-hardware specialists.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T11:02:28.428034Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates strong technical depth but relies heavily on domain-specific acronyms and undefined technical terms that may hinder accessibility for non-specialist readers. Several critical terms appear before their definitions, creating barriers for readers outside the immediate subfield. In Section 3 (Experimental Setup), "mRoPE" and "Dynamic-NTK" are introduced without expansion. While "mRoPE" is elaborated in the Appendix (Section 7.2.3), it appears in the main setup section first without context. Similarly, "Dynamic-NTK" is cited but not explained, leaving readers unfamiliar with positional scaling heuristics unsure of its function.

In Section 4.3 (Comparing Long-Document VQA and OCR Transcription), "SFT" is used ("5B-token SFT stage") before being defined in Table 1's caption. This forward-referencing is confusing. The Introduction (Section 1) mentions "MM-NIAH" without defining the acronym, relegating the definition to the Appendix (Section 7.2.4). Benchmark acronyms like MMLongBench and VTCBench are also used in the Introduction without immediate expansion. Additionally, hardware specifics like "H20" (Section 7 Appendix) assume knowledge of specific GPU models, which may not be universal.

To improve clarity and inclusivity, expand all acronyms at first use in the main text. Provide brief parenthetical explanations for specialized techniques like mRoPE (multimodal Rotary Positional Embeddings) and Dynamic-NTK where possible. Ensure benchmark names are spelled out before abbreviations. These edits will reduce cognitive load for a broader audience without sacrificing technical precision.
