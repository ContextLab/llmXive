---
action_items:
- id: 4780954ad3be
  severity: science
  text: "Report variability (e.g., standard deviation or confidence intervals) for\
    \ all success\u2011rate numbers in Tables\u202F1 and\u202F2; the current percentages\
    \ lack any measure of statistical uncertainty."
- id: 2efd0d8018ca
  severity: science
  text: "Perform statistical significance testing (e.g., paired t\u2011test or non\u2011\
    parametric test) when comparing Guava\u2011Agent\u20114B against baselines, and\
    \ report p\u2011values with appropriate multiple\u2011comparison correction (e.g.,\
    \ Bonferroni or Holm)."
- id: 949f7287e285
  severity: science
  text: Provide a power analysis or justification for the chosen number of evaluation
    episodes (15 per task) to ensure the reported differences are not due to sampling
    noise.
- id: ce0be9ffc921
  severity: writing
  text: Specify random seeds and any stochasticity controls used during data generation,
    training (SFT and GRPO), and evaluation to enable exact reproducibility.
- id: 78cd444624b9
  severity: writing
  text: "Include a description of how the sparse task\u2011success reward is defined\
    \ and scaled in the GRPO stage; without this, the RL optimisation procedure cannot\
    \ be independently verified."
artifact_hash: 305fa4e0caf5509b3ff951ed539855921f525d3dfdda7d54d245e51eb00f86f3
artifact_path: projects/PROJ-739-guava-an-effective-and-universal-harness/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T00:44:43.460254Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents impressive engineering results but provides virtually no statistical analysis of the reported performance numbers. Success rates are reported as single percentages (e.g., 75.6 % overall for Guava‑Agent‑4B) without any indication of variability across the 15 evaluation episodes per task. This makes it impossible to assess whether observed differences between models (e.g., 75.6 % vs. 70.2 % for GPT‑5.4) are statistically meaningful or could arise from random fluctuations.

Moreover, the paper compares multiple baselines across several task categories (ID, OOD‑Object, OOD‑Prompt, OOD‑Long‑Horizon) but does not address the multiple‑comparison problem. When many pairwise comparisons are made, the chance of a false positive increases; a correction method (Bonferroni, Holm, or false‑discovery‑rate) should be applied and reported.

The experimental design also lacks a justification for the chosen sample size (15 episodes per task). A brief power analysis, or at least a discussion of the expected confidence interval width given this sample size, would help readers gauge the reliability of the results. Relatedly, the RL fine‑tuning stage (GRPO) mentions a “sparse task‑success reward” but provides no quantitative definition, scaling factor, or reward‑shaping details, hindering reproducibility of the RL component.

Reproducibility is further compromised by the absence of random seed specifications for data generation, supervised fine‑tuning, and RL training. Since the data engine introduces stochastic scene randomisation and perturbations, reporting the seeds (or a seed‑range) is essential for others to replicate the exact trajectories and training dynamics.

In summary, while the engineering contributions are solid, the statistical rigor of the evaluation is insufficient. Adding variability measures, significance testing with multiple‑comparison correction, a power analysis for episode counts, detailed RL reward specifications, and explicit random‑seed reporting will substantially strengthen the scientific validity and reproducibility of the work.
