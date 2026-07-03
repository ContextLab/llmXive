---
action_items:
- id: 799babd35665
  severity: science
  text: The claim that '31 instances' exist where a model 5x smaller outperforms a
    larger one (Section 4, 'The Scale-Performance Disconnect') lacks a supporting
    table or list. Without a concrete enumeration of these pairs, the specific count
    is unverifiable and risks being an artifact of cherry-picking. Please provide
    a supplementary table listing these 31 pairs with their respective sizes and MCC
    scores.
- id: 127a135927e4
  severity: science
  text: The controlled pair analysis for 'Eukaryotic-genes vs. multi-species' relies
    on a single pair (GENERator-Eukaryote-3B vs. DNA-GPT-3B-M) (Appendix, Table 4).
    Drawing a general conclusion about the superiority of gene-focused pretraining
    from n=1 is statistically weak. Please either expand this analysis to include
    more matched pairs or significantly temper the language to reflect that this is
    a single-case observation rather than a robust trend.
- id: af0fe16ed1b7
  severity: science
  text: The few-shot robustness analysis notes an 'inverse performance pattern' where
    smaller/worse models degrade less (Section 4). However, the paper does not explicitly
    test whether this is a statistical artifact of the floor effect (models already
    near random performance cannot drop much further). Please include a control analysis
    or discussion ruling out floor effects as the primary driver of this observation.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:09:13.691243Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a large-scale benchmark (GENEB) with a substantial sample size (40 models, 100 tasks), which is a significant strength. The use of controlled pair comparisons (30 pairs) to isolate variables like architecture and pretraining data is a robust methodological choice that strengthens the causal claims regarding transfer learning and architectural differences. The statistical reporting (Spearman correlations, p-values) is generally appropriate for the scale of the data.

However, the strength of the evidence is compromised in specific areas where the sample size for the specific claim is too small to support the generalization made. Most notably, the conclusion regarding the superiority of "eukaryotic-gene focused" pretraining is based on a single controlled pair (Appendix, Table 4). While the effect size is large, n=1 is insufficient to establish a general principle, especially given the heterogeneity of the other models. Similarly, the specific claim of "31 instances" of smaller models outperforming larger ones (Section 4) is presented without a supporting list or table, making it impossible to verify if this count is accurate or if it relies on a specific, potentially biased, definition of "outperform."

Furthermore, the observation of an "inverse performance pattern" in few-shot robustness (where lower-performing models show less degradation) requires a more rigorous check against floor effects. Since many tasks (e.g., DNA methylation, lncRNA) result in near-random performance for all models in the 1-shot regime, the apparent stability of the worst models may simply be a mathematical artifact of having no room to drop further, rather than a genuine property of their representations. The current text does not adequately address this alternative explanation.

Finally, while the paper correctly identifies that the prokaryotic-only model (Evo-1-131k) is an outlier, the exclusion of this model to boost the correlation coefficient from 0.565 to 0.685 should be accompanied by a sensitivity analysis showing how the ranking of the top models changes with and without this outlier, to ensure the "scale-performance" conclusion is not driven entirely by the removal of a single domain-mismatched data point.
