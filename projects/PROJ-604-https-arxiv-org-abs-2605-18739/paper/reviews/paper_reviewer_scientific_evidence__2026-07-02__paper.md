---
action_items:
- id: bec9feedbf25
  severity: science
  text: Table 1 (sec/05_experiment.tex) reports training iteration times but lacks
    standard deviation or confidence intervals across multiple runs. Given the stochastic
    nature of training and the claim of a 2.1x speedup, statistical significance testing
    or error bars are required to rule out variance as a confounding factor.
- id: dce7a756d140
  severity: science
  text: The claim of 'strong performance' on VBench-Long (Table 2, sec/05_experiment.tex)
    relies on a single aggregate score without reporting the variance across the 120K
    dataset samples or the specific distribution of scores. A statistical test comparing
    the mean/median of LongLive-2.0 against the best baseline (LongLive) is needed
    to confirm the improvement is not due to random sampling.
- id: 160b2ba84f4e
  severity: science
  text: The ablation study for NVFP4 quantization (Appendix, Table 'appendix_ll2_precision_settings')
    compares PTQ vs. Pre-trained NVFP4 but does not include a baseline BF16 model
    trained with the exact same random seeds and data shuffling to isolate the quantization
    effect from training dynamics. Re-running the BF16 baseline with matched seeds
    is necessary to attribute the ~1.0 point drop solely to quantization.
artifact_hash: de9cc7b61426b053f14e2745d8dcacce77bcfbd73c84f2c8e9aae072a3bf9bd1
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:01:55.743881Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling system-level contribution, but the scientific evidence supporting the quantitative claims requires strengthening regarding statistical rigor and experimental controls.

First, the efficiency claims in Table 1 (sec/05_experiment.tex) are presented as single-point measurements (e.g., 639.5s for 64s video). In distributed training systems, iteration time can fluctuate due to network jitter, GPU thermal throttling, or data loading variance. Without reporting standard deviations or results from multiple independent runs (e.g., n=3 or n=5), it is impossible to determine if the reported 2.1x speedup is statistically significant or within the noise margin of the hardware. The authors should provide error bars or a statistical significance test (e.g., t-test) comparing the NVFP4+Balanced SP configuration against the BF16+SP baseline.

Second, the performance evaluation on VBench-Long (Table 2, sec/05_experiment.tex) relies on aggregate scores. While the authors claim LongLive-2.0 achieves the "best average rank," the table does not provide the variance of these scores across the test set or the number of samples used for the 60s generation benchmark. Given the high dimensionality of video generation metrics, a single run on a specific prompt set may not be representative. The authors should report the mean and standard deviation of the scores across multiple seeds or a larger, stratified subset of the benchmark to ensure the observed improvements are robust.

Third, the ablation study in the Appendix regarding NVFP4 quantization (Table 'appendix_ll2_precision_settings') compares a PTQ model and a Pre-trained NVFP4 model against a BF16 baseline. However, the BF16 baseline appears to be a standard training run, while the NVFP4 models involve specific quantization-aware training procedures. To rigorously isolate the impact of the precision format from potential differences in training dynamics (e.g., optimizer behavior, gradient noise), the authors should ideally re-run the BF16 baseline with the exact same random seeds, data shuffling, and hyperparameters used for the NVFP4 runs. Without this control, the ~1.0 point drop in VBench scores for the NVFP4 model could be partially attributed to training instability rather than the quantization format itself.

Finally, the claim that the "clean pipeline" (Section 4.1) leads to better results is qualitative. While the authors compare their pipeline to complex multi-stage baselines, they do not provide a controlled experiment where the *only* variable changed is the pipeline complexity (e.g., training a model with the LongLive-2.0 infrastructure but using the Self-Forcing multi-stage algorithm, or vice versa). While this may be difficult to implement, a more detailed analysis of the training loss curves or convergence rates between the proposed method and the baselines would provide stronger evidence that the pipeline simplification does not come at the cost of optimization stability.
