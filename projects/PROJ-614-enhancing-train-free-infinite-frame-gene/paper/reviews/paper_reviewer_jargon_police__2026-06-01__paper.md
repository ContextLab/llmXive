---
action_items:
- id: 6e7a18de3706
  severity: writing
  text: Define 'latents' with plain language (e.g., 'compressed representations')
    upon first use in Section 3.1 to aid non-specialist readers.
- id: b7c454ad9bb6
  severity: writing
  text: Provide a concise, intuitive explanation for 'noise span' in the Introduction
    or Section 3.2, as it is central to the method but currently defined only mathematically.
- id: 9aface39a642
  severity: writing
  text: Ensure all acronyms in tables (S.C., B.C., M.S., T.F., O.S.) are explicitly
    defined in the table caption or immediately preceding text, not just in the main
    body.
- id: 131b4a42dfc2
  severity: writing
  text: Simplify or define Appendix jargon such as 'MMDiT', 'KV Flush', and 'RoPE
    Cut' for readers who may only skim the main text.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T11:10:15.898471Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Jargon Overuse Review**

The manuscript is technically dense, which is expected for an ICML submission, but several terms create unnecessary barriers for non-specialist readers. The most frequent offender is "latents" (e.g., Section 3.1, Equation 1). While standard in diffusion literature, it should be accompanied by a plain-language gloss (e.g., "compressed representations") at first mention to ensure accessibility for readers from adjacent fields.

The core contribution relies heavily on the term "noise span" (Introduction; Section 3.2). Currently, this is defined implicitly through mathematical notation regarding time steps ($\tau$). A brief, intuitive sentence explaining what "noise span" represents physically (e.g., "the range of noise levels present in a batch") would significantly improve clarity without sacrificing precision. Similarly, "zigzag-structured latent queue" (Section 3.2) is highly specific jargon; a simplified descriptor or diagram reference in the text would help.

In Section 3.3, "Test-Time Scaling (TTS)" is introduced with a citation to LLM literature. Given the video generation context, a brief clarification on how TTS applies here (e.g., "expanding inference computation for quality") would bridge the gap between domains. Additionally, Table 1 and Table 2 utilize acronyms (S.C., B.C., M.S., T.F., O.S.) without inline definitions. While defined in Section 4.1, placing these definitions directly in the table captions or a footnote would prevent readers from flipping back and forth.

Finally, the Appendix contains significant jargon ("MMDiT", "KV Flush", "RoPE Cut", "sink frame"). While acceptable for experts, these terms assume familiarity with specific recent architectures. If the paper aims for broader impact, a glossary or brief parenthetical explanations in the Appendix would be beneficial. These are all text-based fixes that do not require new experiments.
