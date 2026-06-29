---
action_items:
- id: f3485f5bb1bc
  severity: science
  text: Report confidence intervals or standard errors for MCC scores across the 5
    seeds (Methodology) to quantify uncertainty in main results.
- id: a377b89dc37c
  severity: science
  text: Address multiple-comparisons issue for the 13 category-level scaling correlations
    (Table 1) using FDR or Bonferroni correction.
- id: ffa73680eadd
  severity: science
  text: Provide statistical significance tests (e.g., paired t-tests or bootstrap
    CIs) for the 30 controlled-pair differences (Appendix) rather than point estimates
    alone.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:31:00.368240Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical methodology is largely appropriate for the domain, utilizing Spearman correlation for non-linear scale-performance relationships and MCC for class-imbalanced tasks. However, uncertainty quantification is insufficient to fully support the comparative claims. The Methodology section specifies 5 random seeds (13, 17, 42, 123, 997), yet the main results (e.g., macro-MCC in Section 3) report only point estimates without standard errors or confidence intervals. Given the variance observed in few-shot regimes (e.g., 78.2% drop), reporting mean ± SE would strengthen claims about model rankings and stability.

In Table 1 (per-category scaling), 13 Spearman correlations are tested for significance (p<0.05). Without correction for multiple comparisons (e.g., Benjamini-Hochberg), the risk of Type I errors is elevated. While the non-significant findings (species classification, chromatin accessibility) are robust, the significant correlations should be contextualized with FDR control to ensure validity across the 13 categories.

The Appendix (Controlled-Pair Comparisons) enumerates 30 pairs to isolate factors (architecture, pretraining, tokenization). Differences (Δ MCC) are reported as point estimates (e.g., +0.149 for Omni-DNA vs. eccDNAMamba). Without paired statistical tests across seeds or tasks, it is unclear if these differences exceed noise. For instance, the claim that "Transformers outperform SSMs" relies on these differences; bootstrap confidence intervals would validate this.

Finally, the removal of `Evo-1-131k` as an outlier (Figure 1 caption) improves correlation (ρ: 0.565 → 0.685). While justified by domain mismatch, this should be explicitly labeled as a sensitivity analysis rather than the primary correlation metric to avoid selection bias concerns. The probe stability analysis (Appendix) is strong, showing high rank correlation (ρ=0.964) between linear and MLP probes, which supports the linear probing choice.

Overall, the analysis is rigorous but requires enhanced uncertainty reporting to support the comparative claims.
