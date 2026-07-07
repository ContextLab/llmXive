---
action_items:
- id: 916cf7f58927
  severity: writing
  text: Abstract claims MIPU 'improves average reasoning performance' generally, but
    experiments (Sec 5.1) are restricted to FP8-quantized rollout on two Qwen3 models.
    Scope the claim to 'under high training-inference mismatch (e.g., FP8 quantization)'
    or add evidence from full-precision settings.
- id: 62fb2fad297d
  severity: writing
  text: Conclusion states MIPU improves 'training stability' generally, but Limitations
    admit tests are only on 'moderate-scale models' and never in non-quantized settings.
    Clarify that stability is demonstrated specifically under quantization-induced
    mismatch, not as a universal property.
- id: 00dcbdcf1b20
  severity: writing
  text: Introduction frames the solution as addressing 'training-inference mismatch'
    generally, yet validation is only in 'FP8-quantized rollout' (Sec 5.1). Clarify
    that the method targets mismatch 'amplified by low-precision inference' rather
    than all forms of mismatch.
artifact_hash: 532a85457b6c71e1e8174b90594afc6d1be5ab1b35a438039d06e81d212f0a7d
artifact_path: projects/PROJ-994-the-mirage-of-optimizing-training-polici/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:26:03.696558Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes a compelling case for objective misalignment in LLM RL, but the rhetoric occasionally outpaces the specific experimental conditions. The abstract and introduction present the "Monotonic Inference Policy Improvement" (MIPI) principle and the MIPU framework as a general solution to training-inference mismatch. However, the empirical validation (Section 5) is exclusively conducted under "FP8-quantized rollout," a specific high-mismatch scenario. While the authors acknowledge in the Limitations that they are constrained to "moderate-scale models," the main narrative frames the results as a general improvement in "training stability" and "reasoning performance" without sufficiently qualifying that these benefits were observed specifically in the context of quantization-induced mismatch.

For instance, the abstract states MIPU "improves average reasoning performance and training stability" without the qualifier "under high mismatch." Similarly, the conclusion reiterates that MIPU improves stability, which, while true for the tested setting, risks implying robustness across all RL training regimes (e.g., full-precision or different mismatch sources) where the method was not tested. The paper would benefit from tightening the scope of its claims to match the specific "FP8-quantized" evidence, or explicitly stating that the method is a targeted solution for low-precision inference environments rather than a universal fix for all training-inference mismatches. The current phrasing suggests a broader generalization than the single-condition experiment supports.
