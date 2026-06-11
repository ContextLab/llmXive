---
action_items:
- id: 25d29374f3f8
  severity: science
  text: Report effect sizes (e.g., Cohen's d) for all t-tests in Table 1 and Supplementary
    Tables to quantify stylistic separation magnitude.
- id: b7f510296d4e
  severity: science
  text: Clarify sample sizes and independence assumptions for the ablation study statistical
    comparisons (Sec. 3.4).
- id: 4e15f2e069f5
  severity: science
  text: Discuss potential genre/period confounds given all 8 authors are classic English
    literature (Methods, Sec. 2.1).
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T16:34:40.182432Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The study employs a rigorous experimental design with 10 random seeds per author (Methods, Sec. 2.2), providing robust replication of the training procedure. Standardizing the training token budget to 643,041 tokens per author controls for corpus size disparities (Methods, Sec. 2.1). However, the sample size of eight authors limits the generalizability of the claim that LLMs universally capture "author-specific writing patterns" (Abstract). While the t-tests in Table 1 show highly significant differences (e.g., Austen t = 50.64, p < 10^-43), effect sizes (e.g., Cohen's d) are omitted, making it difficult to assess the practical magnitude of stylistic differences beyond statistical significance. The degrees of freedom in Table 1 (e.g., df = 47.38 for Austen) suggest Welch's t-test was used to account for unequal variances between same-author and other-author loss distributions, which is appropriate given the small N of seeds (10).

The Oz book attribution (Sec. 3.3) relies on a single contested text; while it aligns with prior work [NiloBino03], it functions as a case study rather than a blind test on an unknown attribution. The ablation studies (Sec. 3.4) effectively demonstrate that POS-only models fail to distinguish authors (p = 0.141 in Supplement Table 3), strengthening the claim that lexical and syntactic features are primary drivers. However, the comparison of intact vs. ablated models uses t-tests (e.g., t(11.77) = 3.21) without specifying the exact sample sizes used for those specific comparisons. The stopping criterion (loss < 3.0) based on manual inspection (Methods, Sec. 2.2) introduces a potential bias if the threshold correlates with stylistic distinctiveness rather than just convergence. Additionally, the confusion matrix (Fig 3) shows Baum/Thompson proximity, suggesting genre or period confounds rather than pure style. To strengthen the scientific evidence, report effect sizes for all primary t-tests and clarify the sample sizes and independence assumptions in the ablation statistical tests. Acknowledge genre confinement in limitations regarding generalizability.
