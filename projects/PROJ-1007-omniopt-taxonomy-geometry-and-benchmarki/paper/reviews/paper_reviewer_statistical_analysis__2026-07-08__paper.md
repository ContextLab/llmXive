---
action_items:
- id: 9c20cd32e10f
  severity: science
  text: "Section 5.2 and Tables 3-10 report single-point performance metrics (e.g.,\
    \ '13.53 PPL', '80.53%') without any measure of uncertainty (SD, SE, or CI) or\
    \ mention of the number of random seeds used. In deep learning benchmarking, single-run\
    \ results are indistinguishable from noise. Report mean \xB1 SD over at least\
    \ 3 seeds for all headline numbers, or explicitly state that results are from\
    \ a single run and treat them as illustrative rather than definitive."
- id: 7fd90f157c50
  severity: writing
  text: Section 5.2.1 and Table 1 claim 'best' or 'worst' performance (e.g., APOLLO
    at 13.53 vs AdamW at 14.48) based on point estimates. Without reported variance
    or a statistical test (e.g., paired t-test or bootstrap), these differences cannot
    be distinguished from random fluctuation. Add error bars to figures and report
    statistical significance or effect sizes for all comparative claims.
- id: 232cfdfd60fd
  severity: science
  text: The paper compares 24 optimizers across multiple architectures and scales
    (Section 5.2), effectively performing dozens of pairwise comparisons. However,
    no correction for multiple comparisons (e.g., Bonferroni, Holm, or FDR) is mentioned
    when declaring 'winners' or 'tiers'. This inflates the false-positive rate. Apply
    a correction method to the reported p-values or rephrase claims to avoid implying
    statistical significance where none was tested.
artifact_hash: dbc48f30e617ac30caed20a396534de7c2a315d3d80c0dacd34ca49ae13f2258
artifact_path: projects/PROJ-1007-omniopt-taxonomy-geometry-and-benchmarki/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-08T03:13:14.300727Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical treatment of the benchmark results in this paper is insufficient to support the definitive ranking and "winner" claims made in the text. While the experimental design (Section 5.1) is extensive, the analysis of the resulting data lacks the necessary rigor to distinguish signal from noise.

The primary issue is the reporting of **point estimates without uncertainty**. Throughout Section 5.2 and the Appendix tables (e.g., Tables 3-10), results are presented as single numbers (e.g., "13.53 PPL", "80.53% accuracy"). In stochastic deep learning training, performance varies significantly across random seeds. Reporting a single run (or an unreported average) as a fixed property of an optimizer is statistically unsound. The paper claims APOLLO is the "best" at 13.53 PPL compared to AdamW's 14.48, but without standard deviations or confidence intervals, it is impossible to know if this 0.95 difference is real or a lucky seed. The field standard for such benchmarks is to report mean ± standard deviation over at least 3-5 seeds.

Furthermore, the paper makes numerous **comparative claims** (e.g., "SOAP holds top PPL in 7/8 scenarios," "Muon improves DeiT-S by >5 percentage points") without addressing the **multiple comparisons problem**. With 24 optimizers tested across 4 architectures and 2 scales, the authors are effectively running hundreds of hypothesis tests. Highlighting the "best" performers without correcting for multiplicity (e.g., via Bonferroni or Benjamini-Hochberg) guarantees that some "significant" findings are false positives. The text uses terms like "best" and "wins" as if they are statistically proven facts, but no p-values, effect sizes, or confidence intervals are provided to back them up.

Finally, the **ablation study** in Section 5.2.8 (Muon) reports specific PPL drops (e.g., "70.74" vs "16.86") but again provides no variance estimates. While the magnitude of the drop is large, the lack of replication data prevents a formal assessment of the stability of these gains.

To fix this, the authors must either re-run experiments with multiple seeds to compute uncertainty metrics or, if re-running is not feasible, explicitly qualify all results as "single-run observations" and remove definitive claims of superiority. The current presentation parades point estimates as exact truths, which misleads the reader about the reliability of the findings.
