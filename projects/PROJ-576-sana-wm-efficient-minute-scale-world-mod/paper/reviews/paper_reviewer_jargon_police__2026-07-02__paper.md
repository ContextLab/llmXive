---
action_items:
- id: cb0a4ebab987
  severity: writing
  text: The manuscript is dense with specialized acronyms and domain-specific terminology
    that significantly raises the barrier to entry for non-specialist readers. While
    the technical depth is appropriate for the field, the lack of definitions for
    standard acronyms violates the principle of accessibility. Specifically, the Abstract
    introduces "6-DoF," "GDN," and "NVFP4" without definition. "6-DoF" should be spelled
    out as "six degrees of freedom" at first mention. "GDN" (Gated DeltaNet) is a
    core archi
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:47:06.504683Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is dense with specialized acronyms and domain-specific terminology that significantly raises the barrier to entry for non-specialist readers. While the technical depth is appropriate for the field, the lack of definitions for standard acronyms violates the principle of accessibility.

Specifically, the Abstract introduces "6-DoF," "GDN," and "NVFP4" without definition. "6-DoF" should be spelled out as "six degrees of freedom" at first mention. "GDN" (Gated DeltaNet) is a core architectural component and must be defined immediately. "NVFP4" is a proprietary quantization format that requires a brief explanation or expansion (e.g., "NVIDIA FP4 quantization") to be understood by a broader audience.

In Section 3, "DiT" is used repeatedly for "Diffusion Transformer" without prior expansion. Similarly, "VAE" (Variational Autoencoder) and "UCPE" (Unified Camera Positional Encoding) appear without definition. The term "Pl\"ucker" (referring to Plücker coordinates) is used in Section 3.2; while standard in computer vision, it is obscure to generalists and should be briefly contextualized (e.g., "Plücker ray coordinates").

Section 4 introduces "3DGS" (3D Gaussian Splatting) and "FCGS" without expansion. Section 5 relies heavily on "AR" (autoregressive) and "FVD" (Fréchet Video Distance) without defining them first. The Appendix uses "LoRA" (Low-Rank Adaptation) without definition.

To improve readability, every acronym should be defined at its first occurrence in the text (Abstract, Introduction, or Method). Additionally, terms like "Plücker," "RoPE" (Rotary Positional Embedding, used in Eq. 3.2), and "FSDP2" should be either expanded or briefly explained in a footnote or parenthetical to ensure the paper is accessible to researchers outside the immediate sub-field of efficient video generation.
