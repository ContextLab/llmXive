---
action_items:
- id: 1677bf2633f2
  severity: science
  text: "Provide confidence intervals or standard errors for all benchmark percentages\
    \ (e.g., HumanEval, LiveCodeBench, MMLU\u2011Redux) and report the number of evaluation\
    \ samples per metric."
- id: eb34e810424e
  severity: science
  text: Describe the random seeds, sampling procedures, and number of runs used for
    each evaluation; include whether results are averaged over multiple seeds or single
    runs.
- id: 154900f69885
  severity: science
  text: "Conduct statistical significance testing (e.g., paired t\u2011tests or bootstrap\
    \ tests) when comparing Mellum\u202F2 to baselines across the many benchmarks;\
    \ adjust for multiple comparisons (e.g., Bonferroni or Holm) given the large table\
    \ of metrics."
- id: 9a4c23797b6b
  severity: science
  text: Add ablation studies with statistical reporting to justify design choices
    such as the asymmetric PPO clipping range, IcePop truncation band, and concision
    penalty; include effect sizes and significance levels.
- id: 0bea49617152
  severity: writing
  text: Document the evaluation scripts, random seeds, and exact version of all benchmark
    suites in a reproducibility package; ensure the code for metric calculation is
    publicly released.
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:36:38.450191Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript reports an extensive set of benchmark percentages (e.g., HumanEval 41.5 % in Table 1, LiveCodeBench 30.9 % → 37.2 % after RL in Table 3, MMLU‑Redux 77.4 % → 78.1 % after RL) without any indication of variability or statistical certainty. Readers cannot assess whether observed improvements are meaningful or within expected noise. For each metric, the authors should report confidence intervals (e.g., 95 % CI) derived from bootstrapping or multiple evaluation runs, and disclose the sample size (number of prompts, number of generated outputs) used.

The evaluation protocol lacks details on randomness control. It is unclear whether the reported numbers stem from a single deterministic run (greedy decoding) or from multiple stochastic runs (e.g., with temperature sampling). The paper should specify the seeds used for model initialization, data shuffling, and evaluation order, and state whether results are averaged across seeds. This information is essential for reproducibility.

Given the dozens of benchmark comparisons, the authors perform many implicit hypothesis tests but do not correct for multiple comparisons. Without correction, the risk of false positives is high. The manuscript would benefit from a formal statistical testing framework (paired t‑tests or non‑parametric bootstrap) comparing Mellum 2 to each baseline, with an appropriate correction method (Bonferroni, Holm‑Šidák, or false discovery rate).

Several architectural and training design choices (asymmetric PPO clipping, IcePop truncation band, concision penalty) are presented as beneficial, yet no statistical evidence is provided. Ablation experiments should include effect sizes, confidence intervals, and significance testing to substantiate claims that these components improve performance.

Finally, the reproducibility package should contain the exact evaluation scripts, versioned benchmark datasets, and documented random seeds. Publishing this alongside the model checkpoints will enable the community to verify the reported statistics and build upon the work. Addressing these points will substantially strengthen the statistical rigor and credibility of the technical report.
