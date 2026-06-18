---
action_items:
- id: 12ec90c4c05c
  severity: science
  text: Report statistical uncertainty for all benchmark results (e.g., standard deviation,
    confidence intervals) and indicate the number of evaluation runs per model.
- id: ab16f5f4dd13
  severity: science
  text: Provide details on random seeds, hardware variability, and whether multiple
    training runs were performed to assess reproducibility of the reported gains.
- id: 69014370be77
  severity: science
  text: Clarify the composition of validation and test splits for each benchmark (e.g.,
    number of prompts, whether they overlap with training data) and justify that no
    data leakage occurs.
- id: dc0187decdbc
  severity: science
  text: "Include ablation studies with replicated runs (at least three seeds) for\
    \ key architectural changes (Sliding Window Attention, YaRN layer\u2011selective\
    \ recipe, Multi\u2011Token Prediction head) to demonstrate that observed improvements\
    \ are robust."
- id: cf52a2e17146
  severity: science
  text: "Present effect sizes for the reported improvements (e.g., \u0394% on coding\
    \ benchmarks) alongside statistical significance tests against baselines."
- id: d3d0add300b4
  severity: science
  text: "Document any hyperparameter tuning procedures (grid search, Bayesian optimization)\
    \ and report how many configurations were explored to avoid inadvertent p\u2011\
    hacking."
- id: 828b15139a88
  severity: science
  text: "Add a control experiment where the same training budget is applied to a dense\
    \ 12\u202FB model (without MoE) to isolate the contribution of sparsity to the\
    \ efficiency claims."
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:36:31.525975Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a substantial engineering effort—Mellum 2, a 12 B‑parameter Mixture‑of‑Experts model with long‑context extensions and a two‑stage post‑training pipeline. However, from a scientific‑evidence perspective the reported results lack the rigor needed to substantiate the central claims.

**Benchmark reporting** – Tables \ref{tab:posttrain-eval-instruct} and \ref{tab:posttrain-eval-thinking} list single percentage values for dozens of benchmarks. The paper does not disclose the variance across evaluation runs, the number of random seeds used, or whether results are averaged over multiple generations. Without confidence intervals or standard deviations, it is impossible to judge whether the reported gains (e.g., “EvalPlus 78.4 % vs. 71.8 %”) are statistically meaningful or could be due to stochastic fluctuations.

**Sample size and data splits** – The RL data mix is described as “≈260 k prompts” per variant, but the validation set size, the exact prompt distribution per domain, and any overlap with the training data are omitted. Likewise, the SFT training tokens are reported (≈47 B and ≈167 B) without indicating how many distinct examples this corresponds to, nor whether the token count includes duplicated or highly similar samples. Precise sample‑size information is essential for assessing the power of the experiments.

**Controls and ablations** – The paper includes a few ablations (e.g., long‑context YaRN vs. uniform bump) but provides only a single curve per configuration. No replication across seeds is shown, and the impact of other architectural knobs (expert count, active‑expert ratio, GQA vs. standard attention) is not quantified. A proper control—training a dense 12 B baseline with identical compute budget—would isolate the contribution of sparsity to the claimed compute‑efficiency.

**Effect‑size framing** – Improvements are presented as raw percentages, yet the magnitude of the effect relative to baseline variability is unclear. Reporting Δ% together with statistical significance (e.g., paired t‑test or bootstrap) would allow readers to gauge practical relevance.

**Potential p‑hacking** – The methodology mentions “hyperparameters differ mainly in sequence budget and step count” but does not disclose the search space or how many configurations were tried before selecting the reported numbers. This opacity raises the risk of inadvertent over‑fitting to the benchmark suite.

**Safety evaluation** – HarmBench scores increase after RL (from 8.4 % to 23.1 % “↓”), indicating a regression, yet no statistical analysis or error bars are provided to assess the reliability of this trend.

In summary, the engineering contributions are clear, but the empirical evidence is under‑specified. Strengthening the scientific rigor through the actions listed above will make the claims more robust and reproducible.
