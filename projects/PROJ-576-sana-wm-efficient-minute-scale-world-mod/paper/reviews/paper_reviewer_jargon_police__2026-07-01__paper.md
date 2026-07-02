---
action_items:
- id: 2fa19a270a5a
  severity: writing
  text: 'Acronyms without definition: Terms like "DiT" (Section 3), "AR" (Section
    5), "SFT" (Appendix), and "LoRA" (Appendix) are used without being spelled out
    first. "6-DoF" appears in the Abstract and Introduction but is never expanded
    to "six degrees of freedom."'
- id: 8d3dec6156f4
  severity: writing
  text: 'Hardware/Toolchain Specifics: "NVFP4" (Abstract) and "OOM" (Figure 2 caption)
    are specific to NVIDIA''s ecosystem and developer slang, respectively. These should
    be replaced with "4-bit floating point quantization" and "runs out of memory"
    to maintain formal tone and accessibility.'
- id: 56457a7ab072
  severity: writing
  text: "Unexplained Geometric/Math Terms: \"UCPE\" and \"Pl\\\"ucker\" (Section 3)\
    \ are introduced as if they are common knowledge. A brief parenthetical explanation\
    \ (e.g., \"Pl\xFCcker coordinates, a method for representing 3D lines...\") is\
    \ necessary for clarity."
- id: 9ba941d12875
  severity: writing
  text: 'Metric Acronyms: "FVD" and "VBench" (Section 5) are standard in the niche
    but obscure to the general scientific audience. They should be defined upon first
    mention. The paper would benefit from a "glossary-style" approach in the introduction
    or a strict rule of "define at first use" throughout the text. Currently, the
    density of undefined acronyms forces the reader to constantly pause and infer
    meaning or look up external references, disrupting the flow of the argument.'
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:48:31.140965Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and technical shorthand that significantly raises the barrier to entry for non-specialist readers. While the technical depth is appropriate for the target venue, the writing frequently assumes prior knowledge of specific architecture names, hardware formats, and evaluation metrics without providing plain-language definitions.

Specific instances of jargon overuse include:
1.  **Acronyms without definition:** Terms like "DiT" (Section 3), "AR" (Section 5), "SFT" (Appendix), and "LoRA" (Appendix) are used without being spelled out first. "6-DoF" appears in the Abstract and Introduction but is never expanded to "six degrees of freedom."
2.  **Hardware/Toolchain Specifics:** "NVFP4" (Abstract) and "OOM" (Figure 2 caption) are specific to NVIDIA's ecosystem and developer slang, respectively. These should be replaced with "4-bit floating point quantization" and "runs out of memory" to maintain formal tone and accessibility.
3.  **Unexplained Geometric/Math Terms:** "UCPE" and "Pl\"ucker" (Section 3) are introduced as if they are common knowledge. A brief parenthetical explanation (e.g., "Plücker coordinates, a method for representing 3D lines...") is necessary for clarity.
4.  **Metric Acronyms:** "FVD" and "VBench" (Section 5) are standard in the niche but obscure to the general scientific audience. They should be defined upon first mention.

The paper would benefit from a "glossary-style" approach in the introduction or a strict rule of "define at first use" throughout the text. Currently, the density of undefined acronyms forces the reader to constantly pause and infer meaning or look up external references, disrupting the flow of the argument.
