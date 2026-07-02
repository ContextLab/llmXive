---
action_items:
- id: 4edd2be8393e
  severity: science
  text: The efficiency claims (20%-70% speedup) compare online feature extraction
    against offline pre-computed codes. Clarify if the reported speedup includes the
    amortized cost of encoding or if the baseline was also pre-processed to ensure
    a fair comparison.
- id: f69f1a618aa7
  severity: science
  text: Table 1 shows ViQ trailing SOTA on specific benchmarks like OCRBench. Provide
    statistical significance tests (e.g., p-values or confidence intervals) to confirm
    the aggregated average improvement is robust against variance across the nine
    benchmarks.
- id: 91f518ff209d
  severity: science
  text: The claim of a unique trade-off between reconstruction and understanding relies
    on comparing different models. Include an ablation varying reconstruction loss
    weight to causally demonstrate the trade-off within a single architecture.
artifact_hash: b0d13f79598805d86a50b3ae742d6ff735642238ad128fe0a6c96ca6ef0ec5e0
artifact_path: projects/PROJ-793-viq-text-aligned-visual-quantized-repres/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:09:01.076850Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence for ViQ is generally robust, supported by extensive benchmarking across nine diverse multimodal tasks and ablation studies validating the two-stage training pipeline. The use of consistent fine-tuning data (2000K samples from LLaVA-OneVision) and a standardized evaluation toolkit (LMMs-Eval) strengthens the validity of the comparative results in Table 1 (sec/4-Experiments.tex). The ablation studies (Table 3, sec/4-Experiments.tex) effectively isolate the contributions of proximal representation, bottleneck size, and loss combinations, demonstrating that the $L_\infty$ normalization and VAE latent loss are critical for performance.

However, there are concerns regarding the rigor of the efficiency claims and the statistical interpretation of the results. In Section 4.2.1, the reported 20%-70% training speedup compares an online feature extraction baseline (SigLIP2) against a method using pre-computed discrete codes (ViQ). While the authors mention considering "offline code extraction time," the metric "whole iteration step" is ambiguous. If the baseline's feature extraction is performed online during training while ViQ's is pre-computed, the comparison may conflate architectural efficiency with data preprocessing strategies. The paper should explicitly state whether the baseline was also pre-processed or if the speedup accounts for the full pipeline cost including encoding.

Furthermore, while the aggregated average scores in Table 1 show ViQ surpassing the 6B parameter InternViT-2.5, the performance is not uniform. ViQ underperforms on detail-intensive benchmarks like OCRBench and AI2D. The authors attribute this to the "inherent loss of high-frequency details" in discrete tokenization. While plausible, the paper lacks statistical significance testing (e.g., standard deviations over multiple runs or confidence intervals) to confirm that the marginal gains in the aggregate score are statistically significant and not due to random variance across the benchmarks.

Finally, the claim that ViQ achieves a "favorable trade-off" between reconstruction and understanding relies on comparing ViQ's metrics against UniTok's. UniTok achieves significantly higher PSNR (25.32 vs 22.73) but lower understanding scores. The paper argues this is due to UniTok's direct reconstruction objective. To strengthen this causal claim, an ablation study showing the impact of varying the reconstruction loss weight ($\lambda_{recon}$) on both understanding and reconstruction metrics within the same model architecture would provide more direct evidence than comparing two different models with different training objectives.
