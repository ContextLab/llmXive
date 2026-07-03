---
action_items:
- id: 1302c321730b
  severity: science
  text: The ablation studies on training steps (Sec 4.3, Fig. ablation-steps) and
    batch size (Sec 4.3, Fig. ablation-bs) rely entirely on qualitative visual inspection
    of generated frames. To support the claim of 'strong controllability' or 'failure
    to learn,' quantitative metrics (e.g., camera pose error RMSE, trajectory alignment
    scores) or statistical significance tests across multiple seeds are required to
    rule out cherry-picking.
- id: f89869030e77
  severity: science
  text: The latency claims in Table 1 (Sec 4.1) report single-run measurements on
    a single A800 GPU without reporting variance, standard deviation, or confidence
    intervals. Given the stochastic nature of GPU scheduling and memory allocation,
    a single measurement is insufficient to substantiate the precise speedup factors
    (e.g., 236.64x) claimed.
- id: 8f347d97c75d
  severity: science
  text: The paper claims the framework is 'architecture-general' by instantiating
    it on Wan2.1 and HY1.5 (Sec 1, Sec 4). However, the experimental evidence is limited
    to these two specific models. To robustly support the generalization claim, the
    authors should either include a third distinct architecture or explicitly qualify
    the claim to the tested architectures.
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:45:05.440037Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling engineering framework for converting bidirectional video diffusion models into real-time autoregressive world models. However, from a strict scientific evidence perspective, the validation of the core claims relies heavily on qualitative visual inspection and single-point measurements, which introduces significant risks of bias and overfitting to specific hyperparameters.

First, the ablation studies in Section 4.3 (lines 230-260) regarding training steps and batch sizes are the primary evidence for the "practical guidance" contribution. The authors assert that models are "completely uncontrollable" at 2k steps or "fail to learn" at batch sizes <4 based solely on visual examples in Figures `ablation-steps` and `ablation-bs`. Without quantitative metrics—such as the Mean Squared Error (MSE) between the generated camera trajectory and the ground truth, or a perceptual alignment score—these claims are subjective. It is impossible to verify if the "uncontrollable" models are merely noisy or truly failing to condition, or if the "successful" models at 8k steps are simply overfitting to the specific training seeds shown. The lack of statistical replication (e.g., results averaged over 3-5 random seeds with error bars) makes it difficult to distinguish between a robust training dynamic and a lucky initialization.

Second, the latency results in Table 1 (lines 185-198) are presented with high precision (e.g., 1.137s, 236.64x speedup) but lack any measure of uncertainty. Latency in deep learning inference is highly variable due to system noise, memory fragmentation, and GPU scheduling. Reporting a single measurement without standard deviation or a confidence interval undermines the scientific rigor of the performance claim. A robust evaluation would require reporting the mean and standard deviation over a large number of inference runs (e.g., n=100) to establish the stability of the speedup.

Finally, while the instantiation on Wan2.1 and HY1.5 demonstrates the framework's utility, the claim of being "architecture-general" (Abstract, lines 12-13) is only weakly supported by two data points. While not a fatal flaw, the evidence would be significantly stronger if the authors acknowledged the limited scope of the architectural validation or provided a brief discussion on why these two specific architectures (cross-attention vs. MMDiT) are sufficient to prove generalization.

To elevate the scientific evidence, the authors should replace qualitative assertions with quantitative metrics for controllability, report statistical variance for latency measurements, and clarify the scope of their architectural generalization claims.
