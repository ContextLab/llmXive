---
action_items:
- id: d973b404fd23
  severity: writing
  text: The paper presents a compelling method for incorporating gradient covariance
    into post-training quantization, but the experimental evidence relies heavily
    on single-run results without reported variance. Table 1 and Table 3 present headline
    perplexity and accuracy numbers (e.g., 8.15 vs 9.81 on LLaMA-2-7B at W2) as definitive
    facts. In the context of post-training quantization, where performance can fluctuate
    based on random seeds, calibration data ordering, or floating-point non-determinism,
    a
artifact_hash: 6bdf7827fba12b0d8bdf1afc2ca37e869d5688f3fbc4e54d47c586b30e10b890
artifact_path: projects/PROJ-1045-kronq-llm-quantization-via-kronecker-fac/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T04:00:22.339343Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for incorporating gradient covariance into post-training quantization, but the experimental evidence relies heavily on single-run results without reported variance. Table 1 and Table 3 present headline perplexity and accuracy numbers (e.g., 8.15 vs 9.81 on LLaMA-2-7B at W2) as definitive facts. In the context of post-training quantization, where performance can fluctuate based on random seeds, calibration data ordering, or floating-point non-determinism, a single run is insufficient to establish that the observed gains are robust. The absence of standard deviations or confidence intervals makes it impossible to distinguish a genuine methodological improvement from statistical noise or a lucky initialization.

Furthermore, the dramatic claim that GPTQ and GPTAQ "diverge" or produce "degenerate" quantizations at 2-bit on LLaMA-3-70B, while KronQ succeeds, is based on a single execution. Divergence in these algorithms can sometimes be sensitive to specific random seeds or the order of layer processing. To support the claim that KronQ is fundamentally more stable, the authors should demonstrate that the baselines consistently fail and KronQ consistently succeeds across multiple random seeds.

Finally, the ablation study in Table 4 effectively isolates the BiIP components but conflates the base quantizer (GPTQ vs. GPTAQ) with the proposed method. The table compares "KronQ (GPTAQ base)" against "GPTQ base" and "GPTQ base + BiIP". To rigorously isolate the contribution of the GPTAQ drift correction mechanism itself, a control run is needed: "KronQ with GPTQ base + BiIP" versus "KronQ with GPTAQ base + BiIP". Without this, the specific contribution of the asymmetric drift correction to the final gain remains partially confounded with the BiIP improvements.
