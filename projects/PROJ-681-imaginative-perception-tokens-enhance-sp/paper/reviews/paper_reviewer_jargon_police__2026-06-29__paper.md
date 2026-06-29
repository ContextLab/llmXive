---
action_items:
- id: fa943ba848d6
  severity: writing
  text: Define all acronyms (IPT, PT, PET, MVC, CB, VLM, VQ-VAE, VQ-GAN, CoT, EgoDir,
    PathArr) at first use in the text body, not just in tables or title.
- id: c12a97262489
  severity: writing
  text: Clarify the 'HM3D' reference in Section `supp_data_pet` (Habitat) which cites
    Matterport3D; ensure dataset names are consistent and defined.
- id: 4728c2f10bab
  severity: writing
  text: Expand 'Imaginative Perception Tokens' to full name with '(IPT)' abbreviation
    in the first paragraph of the main text, not just the title.
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:23:24.132113Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on jargon overuse and accessibility for non-specialist readers. The manuscript relies heavily on acronyms that are either undefined or defined only in tables, creating barriers for readers outside the immediate subfield.

In Section `supp_vlms` (Imaginative Token Exploration with Different VLMs), the text introduces "VLM" (Vision-Language Models), "VQ-VAE", "VQ-GAN", and "CB" (Codebook) without spelling them out. While standard in the field, a general audience requires these expansions at first mention. Similarly, "Text CoT" appears in `e002` without defining "Chain-of-Thought".

Task-specific acronyms are frequently used in tables without definition. Table `tab:qwen_discrete` and `tab:qwen_modality` use "PT" and "PET" without explicitly stating "Path Tracing" and "Perspective Taking" in the caption or preceding text. Table `tab:pt_breakdown` uses "EgoDir" and "PathArr" (likely Egocentric Direction and Path+Arrow) which are not defined in the provided text chunks. These should be expanded in the table captions or footnotes.

Additionally, Section `supp_data_pet` refers to "HM3D" while citing `chang2017matterport3d`. This inconsistency between the acronym (Habitat-Matterport 3D) and the citation (Matterport3D) may confuse readers regarding the dataset source.

Finally, while the title defines "Imaginative Perception Tokens", the text body (e.g., `e000`, `e001`) uses "IPT" immediately without re-establishing the full term. The first paragraph of the main text should explicitly state "Imaginative Perception Tokens (IPT)" to ensure the abbreviation is anchored for the reader.

Addressing these points will significantly improve the paper's accessibility without altering its scientific content.
