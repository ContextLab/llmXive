---
action_items:
- id: 349fdf26692f
  severity: science
  text: "The paper reports single-point performance numbers for each benchmark without\
    \ any measure of variance (e.g., standard deviation across random seeds) or statistical\
    \ significance testing. Add multiple training runs with different seeds and report\
    \ mean\u202F\xB1\u202Fstd or confidence intervals to demonstrate that improvements\
    \ are robust and not due to random chance."
- id: 74e840c7c69a
  severity: science
  text: The experimental setup lacks a clear description of the size of the validation
    and test sets used for each reasoning task, as well as the number of examples
    sampled for the toy verification. Provide exact sample counts and ensure that
    the same splits are used across baselines to avoid data leakage.
- id: 720c3c38ca6a
  severity: science
  text: "Hyperparameter selection (e.g., retaining ratio\u202F\u03C1_teacher, top\u2011\
    k selection, clipping threshold) appears to be tuned on the test set, and the\
    \ best checkpoint is chosen based on a single evaluation point. Adopt a held\u2011\
    out validation set and report performance on an untouched test set to prevent\
    \ over\u2011fitting to the evaluation metric."
- id: 9be81d107c38
  severity: science
  text: "The comparison to RLVR baselines uses optimization\u2011step counts from\
    \ the original papers, but does not control for differences in compute (e.g.,\
    \ batch size, GPU count) or training duration per step. Include a fair compute\u2011\
    budget comparison (e.g., total FLOPs or wall\u2011clock time) to substantiate\
    \ the claim of superior sample efficiency."
- id: b4eac29d28cc
  severity: science
  text: "The failure\u2011mode analysis (policy collapse) is presented qualitatively\
    \ with a single figure. Quantify the frequency and severity of collapse across\
    \ runs, and explore mitigation strategies (e.g., regularization, early stopping)\
    \ to assess the stability of d\u2011OPSD."
- id: f4976b52f57f
  severity: science
  text: "The toy verification experiment reports Pass@k improvements but does not\
    \ include statistical tests to confirm that the observed gains are significant.\
    \ Add appropriate significance testing (e.g., paired t\u2011test) for these comparisons."
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:42:18.239226Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript introduces d‑OPSD, an on‑policy self‑distillation framework for diffusion LLMs, and reports promising gains on four reasoning benchmarks. However, from a scientific‑evidence perspective the empirical validation is insufficiently rigorous. All reported results are single‑point scores without any indication of variability; there is no mention of random seed replication, confidence intervals, or statistical tests. This makes it impossible to assess whether the observed improvements over RLVR and SFT baselines are reproducible or could arise from stochastic training effects.

The experimental description also omits crucial details about dataset sizes and split handling. For the toy verification, only 500 sampled questions per task are used, but the selection criteria and whether these are disjoint from training data are unclear. Without explicit counts and split definitions, the risk of inadvertent data leakage cannot be ruled out.

Hyperparameter choices (retaining ratio ρ_teacher, top‑k selection, clipping threshold) are explored in ablations, yet the paper appears to select the best configuration based on the same evaluation metric used for final reporting. This constitutes a form of “test‑set tuning” that can inflate performance. A proper validation set should be used for model selection, with the test set reserved for final reporting.

Sample‑efficiency claims compare optimization‑step counts from the RLVR baseline to d‑OPSD, but the underlying compute budgets differ (e.g., number of GPUs, batch sizes, wall‑clock time). Without normalizing for total compute, the claim that d‑OPSD requires only ~10 % of the steps is not fully substantiated.

The failure‑mode analysis shows a single collapse curve; the frequency and conditions under which collapse occurs are not quantified. This limits confidence in the method’s stability and hampers reproducibility.

Overall, while the conceptual contributions are interesting, the empirical evidence lacks the statistical rigor and transparency needed to support the central claims. Addressing the points above—multiple seeds, variance reporting, clear dataset splits, proper validation, compute‑budget normalization, and quantitative failure‑mode analysis—will substantially strengthen the scientific validity of the work.
