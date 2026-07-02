---
action_items:
- id: 79f62d53ee99
  severity: writing
  text: Teaser caption (main-llmxive.tex, lines 108-112) claims training latency is
    1372.9 ms, but Table 1 (sec/05_experiment.tex, line 108) reports 1372.9 s. The
    unit 'ms' is a typo that misrepresents the magnitude of the speedup.
- id: eb9ce6cde487
  severity: writing
  text: Abstract (line 48) claims 1.84x inference speedup. Table 3 (sec/05_experiment.tex,
    line 136) shows this ratio comes from comparing 4-step BF16 (24.8 FPS) to 2-step
    NVFP4 (45.7 FPS). The claim conflates quantization with step distillation; clarify
    that the speedup requires both.
- id: 875ff2d71028
  severity: writing
  text: "Section 3.2 (sec/03_inference_infra.tex, line 168) claims a 3.6x KV-cache\
    \ compression ratio. While 4/(9/8) \u2248 3.55, the text implies this is the total\
    \ ratio including overhead. Clarify that 3.6x is the theoretical payload compression\
    \ before scale overhead."
artifact_hash: de9cc7b61426b053f14e2745d8dcacce77bcfbd73c84f2c8e9aae072a3bf9bd1
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:00:53.046193Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper generally maintains high factual accuracy regarding its core contributions and experimental results. The claims about NVFP4 training and inference speeds, memory reductions, and the "clean pipeline" are well-supported by the provided tables (Table 1, Table 3, Table 4) and the described methodology. The citations to NVFP4 specifications (nvidia2024blackwell, ocp2023mx) and related quantization works (cook2025four, abecassis2025pretraining) appear appropriate and support the technical definitions provided.

However, there are minor discrepancies in unit reporting and comparative baselines that require correction to ensure the claims are strictly accurate:

1.  **Unit Discrepancy in Teaser:** The teaser figure caption (main-llmxive.tex, lines 108-112) states training latency is reduced from "1372.9 ms" to "639.5 ms". Table 1 (sec/05_experiment.tex, line 108) clearly lists these values as "1372.9" and "639.5" with the column header "(s)" for seconds. A latency of ~1.3 seconds per iteration is plausible for long video training, whereas 1.3 milliseconds is physically impossible for a 5B model. The caption incorrectly uses "ms", which misrepresents the scale of the result.

2.  **Attribution of Speedup:** The abstract and teaser claim a "1.84x faster inference" speedup. Table 3 (sec/05_experiment.tex, line 136) shows the BF16 baseline (4 steps) at 24.8 FPS and the final NVFP4 model (2 steps) at 45.7 FPS. The ratio 45.7/24.8 is indeed ~1.84. However, this speedup is a compound effect of NVFP4 quantization *and* the reduction from 4 to 2 denoising steps (distillation). The text implies NVFP4 alone achieves this, or conflates the two optimizations. The claim should be refined to state that the *combination* of NVFP4 and 2-step distillation achieves this speedup, as the NVFP4 4-step model (29.7 FPS) only offers a ~1.2x speedup over the BF16 baseline.

3.  **Compression Ratio Clarity:** In Section 3.2, the claim of a "3.6x KV-cache compression ratio" is mathematically derived from the 4-bit data size (0.5 bytes) plus the specific overhead model (9/8 bytes total). While the math holds, the phrasing "close to a 3.6x" is slightly ambiguous regarding whether it includes the scale factors in the denominator. The current text is acceptable but could be more precise by explicitly stating the formula used (4 / 1.125).

These issues are primarily presentational and do not invalidate the scientific findings, but they should be corrected to ensure the paper's claims are rigorously accurate.
