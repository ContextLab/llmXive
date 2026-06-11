---
action_items:
- id: 3de30d5836b9
  severity: science
  text: Add statistical significance tests (e.g., bootstrap or t-test) for WER differences
    in Tables 1 and 2 to rule out random variance.
- id: a255b62ff599
  severity: science
  text: Explicitly quantify the domain gap between the 2M simulated training clips
    and real-world benchmarks to support 'in-the-wild' claims.
- id: f61f496f7356
  severity: science
  text: Clarify if semantic metrics in Table tab:judge use a held-out LLM or the same
    model family to avoid evaluation circularity.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:16:50.570531Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a robust methodology for ASR under adverse conditions, but the scientific evidence requires strengthening in three areas to support the central claims.

First, **statistical significance is missing** from the primary quantitative claims. In Table 1 (NOIZEUS 0dB), Mega-ASR reports 19.80% WER vs. 23.97% for Qwen3-ASR. While the relative reduction is substantial, no confidence intervals, p-values, or variance estimates are provided (Section 5.1). Given the stochasticity of RL training (DG-WGPO) and the small test sets (e.g., NOIZEUS subsets), these gains could potentially arise from variance. The authors should perform bootstrap resampling or significance testing to validate that the improvements are robust.

Second, the **simulated-to-real domain gap** is under-addressed regarding the "in-the-wild" claim. Section 3.1 states the 2.4M dataset is "synthesized clips" via spectrogram-level simulation. While the "Voices-in-the-wild-Bench" includes 1,500 real recordings (Section 3.3), the training distribution is entirely synthetic. The evidence does not sufficiently demonstrate that the model generalizes beyond the simulation parameters (e.g., reverberation tails, noise spectra) to truly unseen acoustic environments. A discussion or ablation on the realism of the simulation parameters is needed to support the external validity of the results.

Third, the **semantic evaluation methodology** introduces potential circularity. Table `tab:judge` uses an "LLM-judge" to measure hallucinations and missed content. Section 5.2 notes the LLM-judge variant was discarded for training due to cost, but it is used for final semantic reporting. If the judge shares architecture or training data with the model, the semantic gains may be artifacts of alignment rather than genuine robustness. The authors should specify the judge's provenance or supplement with human evaluation for the semantic claims.

Finally, the hyperparameter sensitivity analysis (Table `tab:hp-alpha`, `tab:hp-tau`) suggests the reward weights are finely tuned. With multiple tunable parameters ($\tau, \alpha_{\text{dyn}}, \alpha_s$), there is a risk of overfitting to the validation set distribution. A cross-validation or out-of-distribution test on a held-out dataset not used for tuning would strengthen the evidence of generalization.

Addressing these points will solidify the empirical foundation of the proposed framework.
