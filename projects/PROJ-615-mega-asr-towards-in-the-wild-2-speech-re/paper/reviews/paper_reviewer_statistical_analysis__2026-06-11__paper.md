---
action_items:
- id: d3059d3a8051
  severity: science
  text: Report confidence intervals or standard deviations for all WER metrics in
    Tables 3, 4, and 5 to quantify uncertainty.
- id: ae532054c52f
  severity: science
  text: Perform statistical significance tests (e.g., bootstrap or paired t-test)
    for main performance claims against baselines.
- id: 7dcc3247074a
  severity: science
  text: Clarify the number of random seeds used for training and evaluation to ensure
    reproducibility of reported WERs.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:17:53.482800Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling framework for robust ASR, but the statistical analysis supporting the performance claims requires strengthening to meet publication standards. 

**1. Lack of Uncertainty Quantification:** 
Throughout the experimental results (e.g., Table 3 "Performance comparison on noisy and robust ASR benchmarks" and Table 4 "Ablation of A2S-SFT"), Word Error Rates (WER) are reported as single point estimates (e.g., 6.70 vs. 7.93). In ASR evaluation, WER variance can be substantial depending on test set composition. There are no confidence intervals, standard deviations, or error bars provided. Without this, it is impossible to determine if the observed improvements are statistically distinguishable from random fluctuation. 

**2. Missing Significance Testing:** 
The paper claims "significant advantages" and "state-of-the-art robustness" based on absolute WER reductions (e.g., Abstract claims 45.69% vs. 54.01% on VOiCES). However, no formal hypothesis testing is conducted. Standard practice in robust speech recognition (e.g., CHiME challenges) often requires significance testing (e.g., bootstrap resampling) to validate that improvements are not due to dataset sampling bias.

**3. Hyperparameter Search and Overfitting Risk:** 
Section "Analysis" (Obs. 4) and Table 5 describe sweeping hyperparameters ($\alpha_{\text{dyn}}$, $\alpha_s$, $\tau$) and selecting the best configuration based on validation WER. This introduces a risk of overfitting to the validation set. The manuscript should report whether the final results were re-evaluated on a held-out test set after hyperparameter tuning to ensure generalizability.

**4. Reproducibility Details:** 
The "Experimental setup" section specifies learning rates and batch sizes but omits the number of random seeds used for training runs. Statistical robustness requires averaging results over multiple seeds (e.g., 3-5 runs) to account for stochastic optimization variability.

**Recommendation:** 
To support the scientific validity of the claims, the authors must re-run evaluations to compute confidence intervals and perform significance tests. Additionally, reporting the variance across multiple random seeds will strengthen the reproducibility of the results. These additions are critical for establishing the statistical soundness of the proposed method's superiority over baselines.
