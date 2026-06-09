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
- id: 886c11510e7d
  severity: writing
  text: Define 'UniPC' upon first use in Appendix (Section 'Implementation on Different
    Foundation Models') as it is a specific sampler acronym not universally known.
- id: 86b1a4b820d8
  severity: writing
  text: Expand 'DDPM' and 'DDIM' acronyms in Section 3.1 (e.g., 'Denoising Diffusion
    Probabilistic Models') for readers unfamiliar with diffusion nomenclature.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T21:55:24.421765Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Jargon Overuse Review — Re-Review Assessment**

This re-review confirms that the four prior action items regarding jargon and acronym definition remain **unaddressed** in the current revision. The manuscript continues to rely on specialized terminology without sufficient scaffolding for non-specialist readers.

1.  **Section 3.1 ('latents'):** The term "compact latents" is used without a plain-language definition (e.g., "compressed representations"). This assumes familiarity with VAE internals.
2.  **Section 3.2 ('noise span'):** The concept remains defined mathematically (range of noise levels) without an intuitive explanation (e.g., "the variation in noise intensity across frames processed simultaneously").
3.  **Table Acronyms:** While Section 4.1 defines S.C., B.C., etc., the tables in Section 4.3 (Ablation Study, `tab:ab_1`) reuse these acronyms without redefinition in the immediate vicinity or caption, violating the "immediately preceding text" requirement for standalone table comprehension.
4.  **Appendix Jargon:** Terms like 'MMDiT', 'KV Flush', and 'RoPE Cut' appear in the Appendix (`app:imple_different_models`, `app:comp_sf`) without English definitions. Additionally, some terms appear with mixed Chinese characters (e.g., `KV 刷新`), which is inconsistent.

**New Issues Identified:**
*   **'UniPC':** Introduced in the Appendix without expansion.
*   **'DDPM'/'DDIM':** Used in Section 3.1 without full expansion (e.g., "Denoising Diffusion Probabilistic Models").

Please address these writing-level barriers to ensure accessibility for a broader ML audience.
