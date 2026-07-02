---
action_items:
- id: 4365bcea938c
  severity: science
  text: The paper claims significant improvements (e.g., 8.1% on GEditBench) but does
    not report standard deviation, confidence intervals, or the number of independent
    training runs. Without variance estimates or a statistical significance test (e.g.,
    t-test), it is impossible to determine if these gains are robust or due to random
    seed variance.
- id: 53f2107d4227
  severity: science
  text: The 'DiffusionOPD' baseline is described as a 'paper-faithful reproduction'
    in the appendix. The review requires explicit confirmation that the reproduction
    code was validated against the original paper's reported numbers on a shared subset
    before being used as a baseline for comparison, to ensure the 8.1% gain is not
    an artifact of a weak baseline implementation.
- id: aec36baff49d
  severity: science
  text: The 'Realism Absorption' experiment relies on a 'proprietary' reward model
    for evaluation. The paper must provide a detailed description of this model's
    architecture, training data, and validation metrics, or release a proxy version,
    to allow independent verification of the claimed 9.9% improvement and the 85.3%
    gap closure.
artifact_hash: 345c406695aa2dde1374386d01dde68941ce2b695d941d4807a3dc21f8ee698f
artifact_path: projects/PROJ-797-danceopd-on-policy-generative-field-dist/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:41:57.932823Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented in the paper is generally strong in its experimental design, particularly in the systematic ablation of the three core design choices (routing, query state, and query density). The use of multiple baselines (Joint Training, Weight Merging, Off-Policy, DiffusionOPD, Flow-OPD) across four distinct settings (T2I/Edit, Local/Global, Realism, CFG) provides a comprehensive view of the method's performance. The ablation studies in Section 4.2 and 4.3 effectively isolate the contribution of each component, supporting the claim that hard routing and single-query on-policy distillation are superior to soft mixing and dense querying.

However, the statistical rigor of the reported results requires strengthening. The main results in Table 2 and the ablation tables (Tables 4, 5, 6) report single-point averages without any measure of variance (standard deviation or standard error). In deep learning experiments, especially those involving stochastic training and evaluation on benchmarks like GEditBench and GenEval, performance can vary significantly across different random seeds. The claimed improvements (e.g., 8.1% over the best OPD baseline, 16.1% over the best composition baseline) are substantial, but without confidence intervals or a report of the number of independent runs (e.g., "mean ± std over 3 seeds"), it is difficult to assess the statistical significance of these gains. A p-value or a statement that the improvement exceeds the variance of the baseline is necessary to rule out the possibility that the results are due to favorable random seeds.

Furthermore, the evaluation of the "Realism Absorption" setting relies entirely on a "proprietary" reward model (Section 4.1.C and Appendix). While the authors claim this model is used for evaluation, the lack of transparency regarding its architecture, training data, and validation against human preference makes it impossible to independently verify the claim that DanceOPD "closes 85.3% of the student-to-teacher reward gap." If the reward model is biased or poorly calibrated, the entire conclusion regarding realism absorption is unsupported. The authors should either release the reward model (or a proxy) or provide a detailed technical report on its construction and validation to ensure the evidence is reproducible.

Finally, the baseline "DiffusionOPD" is a reproduction implemented by the authors (Appendix A.2). While the authors describe the reproduction details, there is no evidence provided that this reproduction was first validated against the original DiffusionOPD paper's results on a standard benchmark to ensure parity. If the reproduction is suboptimal, the reported 8.1% improvement could be an artifact of a weak baseline rather than a genuine advantage of DanceOPD. A validation step showing that the reproduced DiffusionOPD matches the original paper's reported performance on a shared subset of data is required to establish the validity of the comparison.
