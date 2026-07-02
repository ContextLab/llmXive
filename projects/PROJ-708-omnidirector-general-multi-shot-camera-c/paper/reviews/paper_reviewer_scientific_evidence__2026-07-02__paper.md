---
action_items:
- id: 05b85773de9f
  severity: science
  text: Ground truth for RRE/RTE relies on DPA-V3, a monocular estimator prone to
    scale drift. The paper lacks a sensitivity analysis or error bounds for these
    labels. Without quantifying the evaluator's noise floor, reported improvements
    may reflect estimator bias rather than true model superiority.
- id: 4aec264d5d13
  severity: science
  text: GSB and Sem-Pre metrics rely solely on Gemini 3.1 Pro without human validation
    or inter-rater reliability checks. Relying on an LLM judge for primary qualitative
    benchmarks introduces significant bias risk. Please provide human evaluation results
    or validate the judge's correlation with human preference.
- id: c5a18ccdcd98
  severity: science
  text: Ablation study (Table 2) shows large metric drops (e.g., Sem-Pre 83% to 38%)
    but lacks statistical significance reporting. Please provide standard deviations,
    confidence intervals, or details on random seeds to rule out variance as a factor
    in these dramatic performance changes.
artifact_hash: a65d314d17ec7712e12f1ec0ba7f4dba5e22b080c532708ee9eae2b427ffd22c
artifact_path: projects/PROJ-708-omnidirector-general-multi-shot-camera-c/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T06:48:04.382806Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence for OmniDirector is conceptually strong but lacks the statistical rigor required to fully support its quantitative claims of superiority.

The primary concern is the ground-truth definition for the core metrics. The authors use DPA-V3 (Section 5.1) to extract camera poses from reference videos to calculate Relative Rotation Error (RRE) and Relative Translation Error (RTE). DPA-V3 is a monocular depth/pose estimator, which is inherently susceptible to scale ambiguity and temporal drift, particularly in the "complex real-world scenes" the authors claim to evaluate. The paper asserts "scale-invariant" metrics but does not demonstrate that the ground-truth labels themselves are robust to the specific failure modes of DPA-V3. If the ground truth has a high noise floor, the reported improvement of OmniDirector (RRE 2.64 vs. 4.11 for CamCloneMaster) may be an artifact of the model learning the specific biases of the DPA-V3 estimator rather than true geometric fidelity. A sensitivity analysis or a comparison with a multi-view ground truth (where available) is necessary to validate these numbers.

Secondly, the reliance on Gemini 3.1 Pro for the GSB (Good/Same/Bad) evaluation (Table 3) and semantic transition accuracy (Sem-Pre) introduces a significant validity threat. The paper provides no details on the prompts used, the temperature settings, or, crucially, any validation of the LLM's scoring against human raters. In generative AI research, LLM-as-a-judge metrics are notoriously prone to bias, especially when the judge model (Gemini) and the generator (OmniDirector) may share training data or when the judge is evaluating its own domain of expertise. The claim that OmniDirector achieves 94.26% narrative consistency based solely on an LLM score is not robust without human verification or a clear demonstration of the judge's correlation with human preference.

Finally, the ablation study in Table 2 presents dramatic performance drops (e.g., Sem-Pre falling from 83.79% to 38.45% without Trans PE) without reporting statistical significance. While the effect size is large, the absence of standard deviations, confidence intervals, or a description of the random seeds used for these specific ablation runs makes it difficult to rule out variance as a factor. Given the high stakes of these claims for the proposed "hierarchical prompt expansion" mechanism, the evidence needs to be more statistically grounded.

The paper is sound in its conceptual approach, but the quantitative evidence requires strengthening through more robust ground-truth validation and human-in-the-loop evaluation to rule out evaluator bias.
