---
action_items:
- id: 58e1c47d4402
  severity: science
  text: The paper reports single-point metrics (PSNR, SSIM, NED) without confidence
    intervals, standard deviations, or statistical significance testing. Given the
    claim of 'state-of-the-art' performance, statistical validation (e.g., bootstrapped
    CIs or paired t-tests) is required to distinguish signal from noise, especially
    for marginal gains in Table 1 and 2.
- id: 3261e44c5687
  severity: science
  text: The NED metric calculation (Eq. 1) relies on a single OCR model (PP-OCRv5)
    without reporting its own error rate or variance. The claim that 'biases largely
    cancel' is unverified; a sensitivity analysis or error propagation estimate is
    needed to ensure NED differences reflect VAE performance rather than OCR stochasticity.
- id: 8096b3f497cc
  severity: science
  text: The benchmark construction (Sec 2.2) involves deterministic filtering and
    deduplication but lacks a statistical power analysis or justification for the
    sample size (~3K). It is unclear if this sample size is sufficient to detect the
    reported effect sizes with adequate power, particularly for the f32 compression
    tier where baselines vary widely.
artifact_hash: 815458de8568b35ab5a02599bda9f602ed2dc04d545bca014bc4749f57af838e
artifact_path: projects/PROJ-564-qwen-image-vae-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T19:48:52.745092Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the evaluation in `sec/experiment.tex` is insufficient to support the strong claims of "state-of-the-art" performance.

First, **lack of uncertainty quantification** is a critical omission. Tables 1 and 2 present point estimates for PSNR, SSIM, and NED without any measure of variance (e.g., standard deviation) or confidence intervals. In reconstruction tasks, performance can fluctuate based on the specific subset of images sampled. Without reporting the standard deviation over multiple random seeds or bootstrap confidence intervals, it is impossible to determine if the reported margins (e.g., the 0.0071 SSIM gain in Table 2) are statistically significant or within the noise floor of the evaluation. The claim of superiority requires statistical significance testing (e.g., paired t-tests or Wilcoxon signed-rank tests) across the benchmark samples.

Second, the **validity of the NED metric** relies on an unverified assumption. Equation 1 defines NED based on the output of a single OCR model (PP-OCRv5). The authors assert that "biases largely cancel" when comparing original and reconstructed images. However, OCR models have non-trivial error rates and stochastic behaviors. If the OCR model fails to recognize text in the original image due to noise, or if it hallucinates characters, the NED calculation becomes confounded. The paper lacks a sensitivity analysis or an error propagation estimate to demonstrate that the observed NED improvements are robust to the inherent variance of the OCR engine. A control experiment measuring the OCR model's self-consistency (NED of an image against itself after OCR) would be necessary to establish a baseline noise floor.

Finally, the **sample size justification** for OmniDoc-TokenBench is missing. The benchmark consists of ~3,000 images. While this is a substantial number, the paper does not provide a power analysis or statistical justification for this size relative to the effect sizes observed. For the f32 compression tier, where baseline performance varies drastically (NED 0.07 to 0.57), the variance is high. Without reporting the distribution of scores (e.g., via box plots or error bars) or conducting a power analysis, the robustness of the conclusions regarding the f32c192 model's superiority remains statistically unproven.

To proceed, the authors must re-run evaluations to report mean ± standard deviation, perform significance testing against baselines, and provide a sensitivity analysis for the OCR-based metric.
