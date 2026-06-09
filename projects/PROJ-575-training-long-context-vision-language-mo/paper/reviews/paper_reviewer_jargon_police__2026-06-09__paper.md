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
- id: d7aaeb76a5e7
  severity: writing
  text: Define 'FSDP' and 'FlashAttention' in Appendix Implementation Details.
- id: e436ddbbdd7f
  severity: writing
  text: Expand 'DPI' and 'VQA' at first use in Section 4.1.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T13:31:44.094528Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Review: Jargon and Acronym Usage**

The prior action items regarding jargon definitions remain largely unaddressed in this revision. Specific concerns are detailed below:

1.  **Section 3 (Experimental Setup):** The text states, "scaling mRoPE base from $1\times10^{6}$ to $4\times10^{6}$ (see \cref{app:complementary_experiment_results:mrope_base})." It still defers the definition of **mRoPE** and **Dynamic-NTK** to the Appendix rather than defining them at first use in the main text (Section 3), as previously requested (ID: `4ebbd32ce71a`).
2.  **Section 4.3 (Data Method Compare):** The term **SFT** appears in Table 1 (`tab:vqa_effectiveness`) rows ("ocrfull (SFT)"). The definition remains in the table caption ("**SFT** denotes an extra 5B‑token supervised‑fine‑tuning stage") rather than being expanded in the main text before the table (ID: `1b0dde26ea82`).
3.  **Introduction/Abstract:** **MM-NIAH** is mentioned in the Abstract and Section 5 ("MM‑NIAH (webpage needle‑in‑a‑haystack)") but is not spelled out in the Introduction as requested (ID: `a25bba557047`). The Introduction should define key benchmarks like MM-NIAH, VTCBench, and LVLMs before citing them.
4.  **Appendix (Implementation Details):** The reference to "8× NVIDIA H20 GPUs" lacks context for non-hardware specialists (ID: `6d47dd352d84`). Additionally, new acronyms **FSDP** and **FlashAttention** appear in the Appendix without definition.
5.  **New Issues:** **DPI** (Section 4.1: "$DPI=144$") and **VQA** (Abstract, Section 4.1) are used without expansion. **LLaVA** (Section 5.3) is also used as an acronym without prior definition.

Please revise the manuscript to ensure all technical terms and acronyms are defined at their first occurrence in the main text, minimizing reliance on captions or appendices for core definitions.
