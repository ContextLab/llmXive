---
action_items:
- id: 7d6edf6e602a
  severity: science
  text: Correct the Abstract claim that ViQ ranks 'first among mainstream discrete
    visual autoencoders' for reconstruction; Table 3 shows UniTok achieves higher
    PSNR (25.32 vs 22.73).
- id: 385dbacdafc5
  severity: science
  text: Clarify the 'AnyRes' control in Table 1; checkmarks indicate baselines lack
    AnyRes support, contradicting the text claim that the pipeline was adapted for
    fair comparison.
- id: 7a06cfcbcd02
  severity: science
  text: Provide statistical significance testing or error bars for the marginal benchmark
    gains (e.g., 0.1-0.2 points) to validate the 'surpassing SOTA' claim.
- id: 01c58c2030b8
  severity: science
  text: Verify and clarify the '30B vision-language tokens' training claim in Appendix
    A, as this is unusually high for Stage 2 quantization and impacts reproducibility.
artifact_hash: b0d13f79598805d86a50b3ae742d6ff735642238ad128fe0a6c96ca6ef0ec5e0
artifact_path: projects/PROJ-793-viq-text-aligned-visual-quantized-repres/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T16:37:44.639067Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented in ViQ is generally robust in terms of dataset scale (2000K SFT samples, 3B-30B pretraining tokens) and benchmark coverage (9 multimodal tasks). However, there are critical inconsistencies between textual claims and reported data that undermine the validity of the central claims.

First, the Abstract states ViQ achieves "high precision in low-level reconstruction... ranking first among mainstream discrete visual autoencoders." Table 3 (`sec/4-Experiments.tex`) contradicts this: UniTok reports a PSNR of 25.32, while ViQ reports 22.73. This factual error must be corrected to maintain scientific integrity.

Second, the control for resolution in Table 1 (`sec/4-Experiments.tex`) is ambiguous. The text claims baselines were adapted to the "any resolution" pipeline, yet the table checkmarks indicate most baselines (e.g., SigLIP2-g, InternViT) do not support AnyRes (`\ding{55}`). If baselines were forced to fixed resolution while ViQ used native resolution, the performance gains may be confounded by resolution rather than quantization quality. This requires explicit clarification.

Third, the reported gains on multimodal benchmarks are marginal (e.g., 63.9 vs 63.8 on Qwen2.5-7B). Without error bars or statistical significance testing, it is unclear if these differences are robust or within noise. Given the computational cost, effect sizes should be rigorously validated.

Finally, Appendix A claims Stage 2 training used "approximately 30B vision-language tokens." This is an order of magnitude higher than Stage 1 (3B) and significantly impacts reproducibility and resource claims. Please verify this figure and provide detailed training logs or schedules to support this claim. Addressing these evidence gaps is necessary before the paper can be accepted.
