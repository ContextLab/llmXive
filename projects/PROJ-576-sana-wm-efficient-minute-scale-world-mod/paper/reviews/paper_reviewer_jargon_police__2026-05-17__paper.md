---
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:58:53.455502Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript presents significant technical depth but relies heavily on undefined acronyms and dense terminology that excludes non-specialist readers. To improve accessibility without sacrificing precision, several terms require expansion or simplification.

In the **Abstract**, the term "6-DoF" is used immediately without defining "Degrees of Freedom." While standard in robotics, it should be spelled out at first use. Similarly, "NVFP4" quantization is mentioned without expansion, obscuring the specific precision format for general readers.

The **Introduction** introduces "UCPE" (Unified Camera Positional Encoding) in the "Dual-Branch Camera Control" paragraph without defining the acronym. "VAE stride" is also used assuming prior knowledge of Variational Autoencoder temporal compression. The phrase "spatiotemporally consistent" appears multiple times; while precise, "consistent across space and time" is plainer.

In **Section 3 (Method)**, "RoPE" (Rotary Positional Embeddings) is referenced in Eq. 3.2 without definition. "FCGS" appears in **Section 4 (Data Pipeline)** as "fit one FCGS 3D Gaussian Splatting reconstruction," but the acronym is never expanded. The **Appendix** uses "FSDP2" (Fully Sharded Data Parallel) and "LoRA" (Low-Rank Adaptation) without definition, despite these being critical implementation details.

Additionally, phrases like "chunk-causal autoregressive generator" and "attention-sink tokens" are highly specific jargon. Consider adding brief parenthetical explanations, such as "chunk-causal (processing video in segments with causal masking)" or "attention-sink (fixed context tokens to stabilize memory)."

Finally, "Pl\"ucker raymaps" in **Section 3.2** assumes geometric optics knowledge. A brief descriptor like "raymaps based on Pl\"ucker coordinates" would aid readability. Addressing these undefined acronyms and dense phrases will broaden the paper's reach while maintaining its technical rigor.
