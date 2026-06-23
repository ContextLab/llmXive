---
action_items:
- id: 5b23c20dc441
  severity: science
  text: "Provide statistical uncertainty (e.g., confidence intervals or standard deviations)\
    \ for all quantitative results in Tables\u202F2 and\u202F3 and for the scaling\u2011\
    law curves (Figs\u202F7\u20119). This will allow assessment of effect size robustness\
    \ and variance across random seeds."
- id: cd395eedbb70
  severity: science
  text: "Report the number of random seeds and training runs used for each configuration\
    \ (e.g., Humanoid\u2011GPT\u2011S/B/L) and ensure that baseline methods (GMT,\
    \ TWIST, Any2Track) are re\u2011trained under identical seeds and data splits\
    \ to serve as proper controls."
- id: 1c45cbbc177b
  severity: science
  text: "Include an ablation that isolates the contribution of the Harmonic Motion\
    \ Embedding (HME) sampling strategy versus uniform sampling, with statistical\
    \ tests to rule out over\u2011fitting to a particular cluster configuration."
- id: 9c0a90029546
  severity: science
  text: "Clarify the exact train/validation/test split for the 2\u202FB\u2011frame\
    \ corpus (e.g., how many clips are held out, whether any overlap exists with the\
    \ real\u2011world dance sequences) to eliminate potential data leakage."
- id: 36118986d75d
  severity: science
  text: "Add significance testing (e.g., paired t\u2011tests or non\u2011parametric\
    \ equivalents) when comparing Humanoid\u2011GPT against baselines on the AMASS\u2011\
    test split to demonstrate that observed improvements are not due to chance."
- id: 85d478ff0b39
  severity: writing
  text: "Report the distribution of motion types (e.g., percentages of locomotion,\
    \ acrobatics, etc.) in the curated dataset and in the evaluation sets to verify\
    \ that the claimed \u2018diversity\u2011balanced\u2019 sampling truly covers the\
    \ motion manifold."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T12:59:27.728871Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents an ambitious scaling study of a GPT‑style humanoid motion tracker, yet the scientific evidence supporting its central claims is insufficiently quantified. The primary empirical results (Table 2, “Comparison of backbone architectures and scaling effects”) report single scalar metrics (e.g., SR, MPJPE) without any measure of variance or statistical significance, making it impossible to judge the reliability of the observed performance gains across data and model scales. Similarly, the real‑world evaluation (Table 3) is limited to four dance sequences and provides only point estimates; no confidence intervals, standard deviations, or number of repetitions are reported, raising concerns about reproducibility.

The experimental protocol lacks clear controls. Section 4.2 states that baseline methods (GMT, TWIST, Any2Track) are evaluated using the authors’ released checkpoints, but it does not specify whether these baselines were trained on the same data splits, random seeds, or hyper‑parameter budgets as Humanoid‑GPT. Without re‑training baselines under identical conditions, the comparison may be confounded by differences in data exposure or training effort.

The paper’s claim that “diversity and balance are both necessary” (Section 1, paragraph “Balanced Diversity Matters”) is supported only by a visual bubble plot (Fig. 4) and a single HME‑based diversity metric computed on a uniform 10 k‑sample per dataset. No statistical analysis is provided to demonstrate that the HME‑guided sampling yields a measurable improvement over a naïve uniform or random sampling baseline. An ablation study isolating this factor is missing.

Scaling‑law analyses (Figs 7‑9) are presented qualitatively; the fitted exponents or goodness‑of‑fit statistics are not reported, and the curves are shown without error bands. Consequently, the claim that performance follows a predictable power‑law with data size remains unsubstantiated.

Finally, the dataset construction process (Section 3.1) aggregates multiple public sources and an internal collection, but the exact train/validation/test partitioning of the 2 B‑frame corpus is not described. It is unclear whether any of the real‑world test motions overlap with the training set, which could artificially inflate zero‑shot performance.

To strengthen the scientific evidence, the authors should (i) report variance and statistical significance for all quantitative results, (ii) ensure fair, controlled baselines by re‑training them under identical conditions, (iii) provide rigorous ablations for the HME sampling strategy, (iv) disclose dataset splits and motion‑type distributions, and (v) include fit statistics for the scaling‑law curves. Addressing these points will make the central claims more robust and the work reproducible.
