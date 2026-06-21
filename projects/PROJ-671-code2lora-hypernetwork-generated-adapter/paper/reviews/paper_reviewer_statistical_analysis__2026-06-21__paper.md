---
action_items:
- id: 9dbcec06b733
  severity: science
  text: "Provide statistical significance testing (e.g., paired t\u2011tests or bootstrap)\
    \ for all reported performance differences in Tables\u202F1\u20133, and report\
    \ p\u2011values or confidence intervals."
- id: 4098276978af
  severity: science
  text: Report variance measures (standard deviation, standard error) across multiple
    training runs for each method; currently only point estimates are shown.
- id: b9ad242ee5aa
  severity: science
  text: "Address multiple\u2011comparison correction (e.g., Bonferroni or Holm) given\
    \ the large number of baselines and metrics evaluated."
- id: e18144116771
  severity: writing
  text: "Specify random seeds, data\u2011split randomness, and any nondeterministic\
    \ training settings to enable exact reproducibility of the results."
- id: 0c8510996094
  severity: science
  text: "Include effect\u2011size metrics (e.g., Cohen\u2019s d) alongside raw EM/CodeBLEU\
    \ improvements to contextualize practical significance."
artifact_hash: fad4da344b5e72bb204a08d5e9a960cbc3b14e42d22c2e81bf4f3bf3224fac8e
artifact_path: projects/PROJ-671-code2lora-hypernetwork-generated-adapter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:46:34.414811Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents extensive empirical results (Sections 5.1–5.3, Tables 1–3) comparing Code2LoRA variants against a wide suite of baselines. While the reported point metrics (Exact Match, EditSim, CodeBLEU) are informative, the statistical treatment of these results is insufficient for rigorous scientific claims.

1. **Absence of Significance Testing** – The paper reports single‑value performance for each method but does not indicate whether observed gains (e.g., +5.1 pp EM for codelorastatic over the strongest baseline in Table 1) are statistically reliable. Given the stochastic nature of training large language models, paired significance tests (e.g., bootstrap resampling of the test set or paired t‑tests across multiple random seeds) should be performed and p‑values reported.

2. **Missing Confidence Intervals / Variance** – No standard deviations, confidence intervals, or error bars accompany the EM, EditSim, or CodeBLEU scores. This omission makes it impossible to assess the stability of the reported improvements, especially when differences are modest (e.g., 0.8 pp between codeloraevo and method‑plora in Table 2). Reporting 95 % confidence intervals would clarify the practical relevance of these differences.

3. **Multiple‑Comparison Issue** – The authors evaluate >10 baselines across three metrics and two data splits (CR/IR). Conducting multiple pairwise comparisons inflates the family‑wise error rate. A correction method (Bonferroni, Holm‑Šidák, or false discovery rate) should be applied, and adjusted significance levels reported.

4. **Reproducibility Details** – Section 6 lists hyperparameters but omits random seed settings, data‑shuffle procedures, and any nondeterministic GPU operations (e.g., cuDNN nondeterminism). Providing these details, along with scripts to reproduce the exact splits (Table 2), is essential for independent verification.

5. **Effect‑Size Reporting** – Raw percentage improvements are presented without context. Including effect‑size measures (Cohen’s d or Cliff’s δ) would help readers gauge the magnitude of gains relative to variability.

Addressing these points will substantially strengthen the empirical claims and align the work with standard statistical rigor expected in machine‑learning research.
