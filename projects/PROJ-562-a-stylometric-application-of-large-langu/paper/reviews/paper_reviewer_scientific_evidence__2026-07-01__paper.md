---
action_items:
- id: 4c140d54cae8
  severity: science
  text: The ablation study results for the POS-only corpus are inconsistent. Table
    S3 (supplement.tex) shows non-significant t-tests for 5 of 8 authors (p > 0.05),
    yet the text claims 'models trained on part-of-speech-only corpora reliably learned
    author-specific patterns for just 3 of the 8 authors' without explicitly defining
    the reliability threshold or addressing the high false-negative rate in the statistical
    tests.
- id: c387877c6015
  severity: science
  text: The training stopping criterion (cross-entropy loss <= 3.0) is determined
    by manual inspection of generated samples (Methods, line 138). This introduces
    potential bias and lacks a rigorous, quantitative justification. The authors should
    provide a sensitivity analysis showing how varying this threshold impacts the
    final stylometric distance metrics and attribution accuracy.
- id: 84e475f45b68
  severity: science
  text: The statistical power of the t-tests is unclear. With only 10 random seeds
    (n=10) per condition, the degrees of freedom are low (df ~9-18). The authors should
    report effect sizes (e.g., Cohen's d) alongside p-values to demonstrate that the
    observed differences are not just statistically significant but practically meaningful,
    especially for authors with borderline significance in ablation studies.
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:24:29.026197Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling application of LLMs to stylometry, with a clear hypothesis and a generally robust experimental design involving 10 random seeds and held-out test sets. The core finding—that models trained on a specific author's corpus predict that author's held-out text with lower cross-entropy than other authors' texts—is supported by strong statistical evidence (Table 1, Fig 1B) across the main experiment. The use of 10 random seeds helps mitigate variance from data sampling, and the consistent separation of "same" vs. "other" losses is a strong signal.

However, the scientific evidence for the ablation studies (Section 3.4) requires clarification. In the POS-only ablation, the text states that models "reliably learned author-specific patterns for just 3 of the 8 authors." Yet, Supplementary Table 3 (supplement.tex) shows that for 5 authors (Thompson, Melville, Fitzgerald, Baum, and potentially others depending on the exact p-value cutoff used), the p-values are > 0.05 (e.g., Thompson p=0.3179, Melville p=0.4337). The manuscript does not explicitly define the threshold for "reliable" learning in this context, nor does it discuss the implications of these non-significant results for the other 5 authors. Given the small sample size (n=10 seeds), the statistical power may be low, but the authors should explicitly report effect sizes (e.g., Cohen's d) to contextualize these findings. Without effect sizes, it is difficult to determine if the non-significant results are due to a lack of stylistic signal in POS sequences or simply insufficient statistical power.

Additionally, the training stopping criterion (cross-entropy loss <= 3.0) is based on "manual inspection" of generated samples (Methods, line 138). While this is a pragmatic approach, it introduces a subjective element that could bias the results. A more rigorous justification, such as a convergence analysis or a sensitivity analysis showing how different loss thresholds affect the final attribution accuracy, would strengthen the methodological robustness. The current approach risks overfitting to a specific loss value that may not be optimal for all authors, potentially inflating the apparent distinctiveness of styles.

Finally, while the Oz book attribution is a successful case study, the sample size for this specific claim is n=1 (one contested book). While the result aligns with historical consensus, the evidence for the generalizability of the method to single-book attribution problems remains anecdotal. The authors should temper their claims regarding the method's utility for single-book attribution until tested on a larger set of contested works.
