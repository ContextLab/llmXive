---
artifact_hash: 815458de8568b35ab5a02599bda9f602ed2dc04d545bca014bc4749f57af838e
artifact_path: projects/PROJ-564-qwen-image-vae-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:43:15.118064Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on over-claiming and over-reach in the paper's claims, conclusions, and generalizations.

**1. Overstated "State-of-the-Art" Claims (Introduction, Section 5)**

The paper repeatedly uses "state-of-the-art" (SOTA) without clear qualification. On Table 1 (Recon@Imagenet/FFHQ), Qwen-Image-VAE-2.0-f16c128 shows PSNR 35.90/43.10, but FLUX.2-dev (f16c128) achieves PSNR 34.34/40.36—both are f16c128 models, yet FLUX.2-dev is not discussed as a competitor in the text despite being in the same table. The SOTA claim should be qualified (e.g., "among open-source models" or "in our evaluated baselines").

**2. Text Fidelity Claim Without Full Baseline Coverage (Section 5.1.2)**

The paper claims: *"To the best of our knowledge, this is the first f16 autoencoder to achieve text fidelity exceeding f8 VAEs"* (NED 0.9617 vs. FLUX.1-dev's 0.9546). However, Table 2 shows FLUX.2-dev (f16c128) achieves NED 0.9535—nearly identical to f16c128's 0.9617. The claim should acknowledge FLUX.2-dev's comparable performance and clarify whether FLUX.2-dev was excluded from the "first f16 exceeding f8" claim due to release timing or other factors.

**3. Diffusability Claims Lack Convergence Evidence (Section 5.1.3)**

The paper claims models *"facilitate rapid DiT convergence"* and *"significantly accelerate convergence compared to existing high-compression baselines"* (Abstract, Introduction). However, the downstream DiT experiments (Table 1, Generation columns) report only IS/gFID at 80 epochs. No convergence curves, training time comparisons, or epoch-to-quality tradeoffs are provided. The convergence claim is unsupported by the reported data.

**4. KL/GAN Removal Justification Insufficient (Section 4.1)**

The paper asserts that removing KL loss and GAN loss *"can be removed to achieve better performance and training stability"* and claims this demonstrates *"the feasibility and effectiveness of a simplified training objective, providing insights for future VAEs."* This is a broad generalization. No ablation study quantifies how much KL/GAN removal contributed vs. other factors (data scale, alignment strategy, architecture). The claim should be tempered to reflect that this holds for their specific training regime, not as a general principle.

**5. Qwen-Image-2.0 Integration Claim is Vague (Section 5.2.3)**

The paper states integration into Qwen-Image-2.0 *"further validates the diffusability of our latent space at a foundation-model scale"* but only provides a footnote: *"The VAE integrated into Qwen-Image-2.0 is an intermediate variant derived from the methodological framework established in this work."* No quantitative evidence (e.g., generation metrics, user studies, or comparative ablations) is provided. This is a significant overreach given the paper's focus on diffusability as a core contribution.

**6. f32 Compression Comparison to f8 is Aggressive (Section 5.1.1)**

The paper claims f32c192 *"performs comparably to established f8 VAEs (e.g., Wan2.1), despite operating at a 4× compression factor."* However, Table 1 shows Wan2.1 (f8c16) achieves PSNR 31.29/38.16 on ImageNet/FFHQ, while f32c192 achieves 31.13/37.52—very close but not clearly "comparable" without statistical significance testing or qualitative analysis. The 4× compression claim should acknowledge that f32c192 has 12× more channels (192 vs. 16), which is a significant architectural difference beyond just compression ratio.

**Recommendations:**

- Qualify SOTA claims with explicit scope (e.g., "among evaluated baselines")
- Include convergence curves or training efficiency metrics for diffusability claims
- Provide ablation study for KL/GAN removal contribution
- Add quantitative evidence for Qwen-Image-2.0 integration benefits or reframe as qualitative observation
- Clarify the f32 vs. f8 comparison context (channel dimension differences)
- Acknowledge FLUX.2-dev's comparable NED performance in text fidelity discussion
