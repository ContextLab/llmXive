---
action_items:
- id: 50f8adb666ba
  severity: science
  text: The paper claims a 30% relative WER reduction on compositional scenarios but
    does not report confidence intervals or statistical significance tests (e.g.,
    bootstrap or paired t-tests) for these gains. Given the high variance in WER across
    different acoustic conditions, statistical validation is required to confirm the
    robustness of the reported improvements.
- id: 3602bd0d1781
  severity: science
  text: The 'Voices-in-the-wild-2M' dataset is entirely synthetic, generated via spectral
    manipulation. The paper lacks a rigorous cross-validation experiment demonstrating
    that performance gains on this synthetic benchmark transfer to a held-out, purely
    real-world dataset not used in any training or validation step. Without this,
    the claim of 'in-the-wild' robustness is partially unverified.
- id: 069a0960ec62
  severity: science
  text: "The ablation study (Table 4) shows that removing the sentence-level structural\
    \ reward ($R_{struc}$) causes the largest degradation. However, the paper does\
    \ not provide a sensitivity analysis on the specific threshold $\tau=0.3$ used\
    \ for the WER-gated fusion. A small shift in this threshold could significantly\
    \ alter the balance between token-level and sentence-level rewards, yet the robustness\
    \ of this hyperparameter choice is not fully explored."
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:54:29.846313Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented in "Mega-ASR" is generally strong, supported by extensive ablation studies and comparisons against a wide range of baselines. The proposed dataset, "Voices-in-the-wild-2M," addresses a clear gap in compositional acoustic scenarios, and the dual-granularity reward mechanism (DG-WGPO) is logically motivated by the observed shift in error modes at high WER. The ablation results in Table 4 effectively isolate the contribution of each component, particularly highlighting the necessity of the sentence-level structural reward for handling hallucinations.

However, several aspects of the evidence require strengthening to fully support the central claims of robustness and generalization. First, while the paper reports significant relative WER reductions (e.g., "over 30%"), it lacks statistical significance testing. Word Error Rate (WER) can exhibit high variance across different acoustic conditions and utterance lengths. Without confidence intervals or results from statistical tests (such as bootstrap resampling or paired t-tests) on the benchmark results, it is difficult to ascertain whether the observed improvements are statistically significant or potentially due to random variation in the test set.

Second, the primary evaluation relies heavily on the synthetic "Voices-in-the-wild-2M" dataset and its derived benchmark. While the authors validate the simulator against real data during the construction phase, the final performance claims are largely based on this synthetic environment. The paper would benefit from a more rigorous evaluation on a completely independent, held-out real-world dataset that was not involved in any stage of the simulation calibration or model training. This would provide stronger evidence that the learned robustness generalizes to truly "in-the-wild" conditions rather than overfitting to the specific spectral artifacts of the simulation pipeline.

Finally, the sensitivity of the WER-gated fusion threshold ($\tau$) warrants further investigation. The ablation study in Table 6 shows that $\tau=0.3$ yields the best results, but the performance drop-off for $\tau=0.2$ and $\tau=0.4$ is relatively modest. A more detailed analysis of how the model's performance varies across a continuous range of $\tau$ values, or an analysis of the distribution of WERs in the training data relative to this threshold, would strengthen the justification for this specific hyperparameter choice and demonstrate the stability of the proposed reward mechanism.
