---
action_items:
- id: d2af1ab95730
  severity: science
  text: "The benchmark tables (e.g., Table\u202F1, Table\u202F2) report single-point\
    \ scores without any indication of variance, confidence intervals, or number of\
    \ evaluation runs. Add standard deviations or confidence intervals and describe\
    \ how many random seeds were used."
- id: 78e0fda77f82
  severity: science
  text: "The paper does not describe the size or composition of the validation/test\
    \ splits for the long\u2011video and agentic benchmarks (e.g., LongVideoBench,\
    \ Video\u2011MME\u2011v2, LiveCodeBench). Provide exact sample counts and any\
    \ filtering criteria."
- id: 70baeb365aaf
  severity: science
  text: "No ablation study isolates the contribution of each major component (DSA,\
    \ MOPD, Context\u2011RL, Video\u2011RL). Include controlled experiments that remove\
    \ or replace each module to quantify its impact."
- id: 2550bc256815
  severity: science
  text: "Statistical significance testing is absent when claiming state\u2011of\u2011\
    the\u2011art performance over baselines. Perform appropriate tests (e.g., paired\
    \ t\u2011test, bootstrap) to support claims of superiority."
- id: f64478a38565
  severity: science
  text: "Potential p\u2011hacking risk: multiple benchmark rows are omitted (\"...\u202F\
    N\u202Frows\u202Fomitted\u202F...\") and only the best\u2011performing numbers\
    \ are shown. Provide the full result tables or a clear statement of selection\
    \ criteria."
- id: d59043bacdb8
  severity: science
  text: "The training data scale (e.g., \"500\u202FB tokens from DataComp, LAION,\
    \ CC12M, PD12M, COCO\") lacks precise token counts per modality and does not report\
    \ data quality controls. Detail the token distribution and any filtering steps."
- id: 5e47c7731e2d
  severity: science
  text: "Reinforcement learning sections (Synthetic\u2011Data RL, General RL, Specialized\
    \ RL) report percentage improvements (e.g., \"temporal IoU by \u22481\u202F%\"\
    ) without confidence intervals or statistical tests. Include variance measures\
    \ and describe the evaluation protocol."
- id: 1bf78587e593
  severity: science
  text: "The inference cost analysis (Figure\u202F2) presents cost reductions but\
    \ does not specify the hardware configuration, batch sizes, or measurement methodology.\
    \ Add a reproducible cost benchmarking protocol."
- id: a7abe224a29e
  severity: science
  text: "The paper claims \"no degradation of core reasoning\" after multi\u2011task\
    \ injection, yet no quantitative comparison to a pre\u2011injection baseline is\
    \ shown. Provide a controlled comparison on core reasoning benchmarks."
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:52:45.784160Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents an impressive multimodal MoE model with 256 K token context and a suite of benchmark results. However, from a scientific‑evidence perspective the central claims are insufficiently substantiated. All reported performance numbers are single deterministic values; there is no reporting of variability (standard deviations, confidence intervals) nor any description of how many evaluation runs or random seeds were used. This makes it impossible to assess whether observed differences (e.g., 74.1 vs. 61.6 on LongVideoBench) are statistically significant or could arise from stochastic variation.

The paper also omits critical details about dataset sizes and splits. For each benchmark (LongVideoBench, Video‑MME‑v2, LiveCodeBench, etc.) the exact number of test samples, the distribution across difficulty levels, and any filtering applied are not disclosed. Without this information, the robustness of the results cannot be judged, and replication is hindered.

A major methodological gap is the lack of ablation studies. The model integrates several novel components (DeepSeek Sparse Attention, Cross‑Modal Multi‑Teacher On‑Policy Distillation, Context‑RL, Video‑RL). The manuscript does not isolate the effect of each component through controlled experiments, leaving the attribution of performance gains ambiguous.

Statistical testing is entirely absent. Claims of “state‑of‑the‑art” performance should be backed by appropriate significance tests (e.g., paired bootstrap, t‑tests) comparing against strong baselines. Similarly, modest improvements (e.g., “temporal IoU by ≈1 %”) need confidence intervals to evaluate practical relevance.

The selective presentation of results (indicated by “... N rows omitted ...”) raises concerns about p‑hacking. Full result tables or a transparent selection criterion should be provided to avoid cherry‑picking.

Training data statistics are vague; the token count is given in aggregate, but the modality breakdown, source quality controls, and preprocessing steps are not described. This limits assessment of data bias or overfitting risk.

The RL sections report percentage gains without variance measures, and the inference cost figure lacks details on hardware, batch size, and measurement methodology, preventing reproducibility of the claimed speedups.

Finally, the claim that multi‑task injection does not degrade core reasoning is unsupported by any quantitative baseline comparison on pure reasoning benchmarks.

Addressing these issues—by adding variance reporting, detailed dataset descriptions, ablations, statistical significance testing, full result tables, and reproducible evaluation protocols—will substantially strengthen the scientific evidence supporting the paper’s central contributions.
