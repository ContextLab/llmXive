---
action_items:
- id: 45361c17c92c
  severity: science
  text: "Provide quantitative evaluation of video quality (e.g., FVD, IS, user preference\
    \ studies) for both the bidirectional and few\u2011step AR models, including confidence\
    \ intervals or statistical significance testing."
- id: bcf4a32d3035
  severity: science
  text: Report the size of the training and validation datasets (number of videos,
    total frames) used for each ablation (batch size, training steps, data source)
    and include variance measures (e.g., standard error) across multiple runs.
- id: e5bc17cf5999
  severity: science
  text: Include a clear description of random seeds, hardware configuration, and any
    nondeterministic components to enable exact replication of the reported latency
    and controllability results.
- id: 2ec88c41ac7a
  severity: science
  text: Add an objective metric for camera controllability (e.g., pose error, trajectory
    alignment score) rather than relying solely on visual inspection of a few examples.
- id: 2a6dd5e15be5
  severity: writing
  text: Present ablation results in tabular form with numeric values (e.g., latency,
    quality scores) instead of only qualitative figure captions, and discuss statistical
    robustness of observed trends.
- id: ca476e2c7206
  severity: science
  text: "Clarify the number of training steps and batch\u2011size experiments that\
    \ were repeated; if only a single run was performed, run multiple seeds to assess\
    \ variability and report the results."
- id: e05e54b58e36
  severity: writing
  text: "Provide details on the distribution of camera trajectories in the constructed\
    \ datasets (e.g., range of rotations, translations) to justify the claim that\
    \ ground\u2011truth trajectories are essential."
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:33:07.363289Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The manuscript introduces **minWM**, a full‑stack pipeline that converts existing bidirectional text‑to‑video (T2V) or text‑and‑image‑to‑video (TI2V) diffusion models into camera‑controllable few‑step autoregressive (AR) world models. While the engineering contribution (open‑source code, modular pipeline, latency reductions) is clear, the **scientific evidence supporting the central claims is insufficient**.

1. **Lack of quantitative quality metrics** – The paper reports first‑frame latency reductions (Table 1) but provides no objective measures of video fidelity (e.g., Fréchet Video Distance, Inception Score) or user‑perceived quality. The claim that “few‑step AR models preserve camera‑controllable generation capability” is supported only by a single visual example (Fig. 2) and qualitative descriptions. Without numeric quality scores and statistical analysis, it is impossible to assess whether the distillation sacrifices visual fidelity or controllability.

2. **No statistical rigor in ablations** – The ablation studies (Figures 3‑5) explore batch size, training steps, and data source, yet they present only curves/images without reporting sample sizes, variance, or confidence intervals. It is unclear whether the observed trends (e.g., batch size ≥ 16 enabling controllability) are robust or could be due to random seed effects. Repeating each ablation with multiple seeds and reporting mean ± std would be necessary to substantiate these findings.

3. **Undefined controllability metric** – Camera controllability is a core requirement for interactive world models, but the paper does not define a measurable criterion (e.g., pose error between intended and generated camera trajectories). The reliance on visual inspection leaves the claim vulnerable to subjective bias and makes replication difficult.

4. **Insufficient dataset description** – The paper mentions constructing datasets with “effectively ground‑truth trajectories” (Sec. 4.3) but does not quantify the number of videos, distribution of camera motions, or how these differ from the SpatialVid baseline. This omission hampers the ability to evaluate the generality of the approach.

5. **Reproducibility gaps** – While the code is released, the manuscript omits critical reproducibility details: random seeds, exact hardware specifications (beyond “single A800 GPU”), and whether the reported latency includes all preprocessing steps. Moreover, the training step counts (e.g., “5K‑step model”) lack information on convergence criteria or validation performance.

6. **Potential p‑hacking risk** – The selective presentation of only the “successful” configurations (e.g., batch size = 16) without showing failed runs or a systematic hyper‑parameter sweep raises concerns about cherry‑picking results.

To bring the scientific evidence up to community standards, the authors should augment the paper with **rigorous quantitative evaluations**, **statistical analysis of ablations**, and **clear, reproducible experimental protocols**. Only then can the central claim—that minWM enables real‑time, camera‑controllable video world models without sacrificing quality—be convincingly supported.
