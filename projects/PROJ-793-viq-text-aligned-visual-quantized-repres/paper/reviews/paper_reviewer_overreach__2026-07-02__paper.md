---
action_items:
- id: f3a2a40411d5
  severity: writing
  text: The claim that ViQ 'ranks first among mainstream discrete visual autoencoders'
    (Abstract, Intro) is contradicted by Table 1 (sec/4-Experiments.tex), where UniTok
    achieves superior PSNR (25.32 vs 22.73), SSIM (0.77 vs 0.66), and rFID (0.37 vs
    0.62). The text must be revised to accurately reflect that ViQ is competitive
    or second-best, not first, to avoid over-claiming.
- id: a3b28b67417e
  severity: science
  text: The efficiency claim of '20%-70% acceleration' (Abstract) relies on a comparison
    where ViQ uses pre-computed offline codes while the baseline (SigLIP2-g) extracts
    features online. The paper does not explicitly state that the baseline's feature
    extraction time is excluded from the 'forward time' metric in a way that makes
    the comparison fair for end-to-end training latency. Clarify if the baseline comparison
    includes feature extraction or if the speedup is only for the LLM forward pass.
- id: bacd7f7d3617
  severity: writing
  text: The statement that ViQ 'surpasses the previous state-of-the-art scores...
    under 6B number of visual encoder parameters' (Intro) is misleading. Table 1 shows
    ViQ (1.3B) beats InternViT-2.5-6B (6.0B) on average, but the 6B model is a specific
    large variant. The claim implies a general superiority over all 6B models, whereas
    the comparison is against a specific baseline. Rephrase to specify the exact baseline
    being surpassed.
artifact_hash: b0d13f79598805d86a50b3ae742d6ff735642238ad128fe0a6c96ca6ef0ec5e0
artifact_path: projects/PROJ-793-viq-text-aligned-visual-quantized-repres/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:08:00.328416Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding performance rankings and efficiency gains that overreach the provided evidence.

First, the Abstract and Introduction state that ViQ "ranks first among mainstream discrete visual autoencoders" regarding reconstruction quality. However, Table 1 in Section 4 (sec/4-Experiments.tex) explicitly shows that UniTok achieves higher PSNR (25.32 vs 22.73), SSIM (0.77 vs 0.66), and lower rFID (0.37 vs 0.62) on the ImageNet-1K validation set. While the authors later acknowledge UniTok's strength in the Results section, the initial absolute claim of "ranking first" is factually unsupported by their own data and constitutes an over-claim. The text should be amended to reflect that ViQ is "highly competitive" or "ranks second" rather than first.

Second, the efficiency claims of "20%-70% acceleration" (Abstract) require clarification on the baseline comparison. The setup in Section 4.2.1 describes extracting ViQ codes offline, whereas the baseline (SigLIP2-g) extracts features online during the forward pass. If the "forward time" metric for the baseline excludes the feature extraction time (which is standard for VLM training where encoders are often frozen and pre-extracted), the comparison is unfair. If the baseline *does* include extraction, the speedup is valid. The paper currently lacks a clear statement on whether the baseline's feature extraction cost is included in the reported "forward time," leading to potential over-interpretation of the efficiency gains.

Finally, the claim that ViQ "surpasses the previous state-of-the-art scores... under 6B number of visual encoder parameters" (Introduction) is slightly imprecise. The data shows ViQ (1.3B) outperforms the specific *InternViT-2.5-6B* variant on average. However, phrasing it as surpassing scores "under 6B parameters" could imply a broader dominance over all models in that parameter range, which is not fully supported if other 6B models (not listed) perform differently. The claim should be tightened to specify the exact baseline model being surpassed.
