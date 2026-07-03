---
action_items:
- id: d6b2a2fd1e8e
  severity: science
  text: The PTF metric validity relies on a correlation of r=0.51 with per-phase averages
    (Appendix PTF Metric Validity). This indicates PTF captures only ~26% of the variance
    explained by simple averaging. The authors must provide a stronger statistical
    justification (e.g., variance decomposition or regression analysis) for why PTF
    is a distinct and necessary metric beyond a weighted average of APF/RPF/RAE.
- id: 621e0f39f985
  severity: science
  text: The claim that DPO training specifically improves trajectory direction (Section
    5.3) is based on a comparison of 1,198/1,750 probes. The evidence lacks a formal
    statistical test (e.g., paired t-test or Wilcoxon signed-rank) on the magnitude
    of the PTF improvement to rule out random variation, especially given the small
    sample size of the perturbation analysis (N=75 in Table 6).
- id: d9ee1d8ec024
  severity: science
  text: The 'MixedArc' ablation (Section 5.1) uses a deterministic hash to select
    donor characters. The authors must clarify if this selection process introduces
    any systematic bias (e.g., selecting characters with similar arc structures) that
    could artificially inflate the 'Vanilla' baseline performance, thereby underestimating
    the true effect size of the correct Arc.
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:15:04.940769Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a robust dataset construction pipeline with human validation (2-of-3 majority) for the Character Arcs, which strengthens the ground truth for the evaluation. The sample size of 4,601 probes across 17 novels is substantial for this domain. However, the statistical evidence supporting the novelty of the PTF metric is weak. In Appendix PTF Metric Validity, the authors report a Pearson correlation of r=0.51 between PTF and the average of per-phase metrics (APF, RPF, RAE). An r² of ~0.26 implies that PTF shares only a quarter of its variance with the per-phase scores, yet the paper treats PTF as a primary, distinct indicator of "trajectory" without demonstrating that it captures unique variance not explained by the component metrics. A regression analysis or variance decomposition is needed to justify PTF as a standalone metric rather than a redundant composite.

Furthermore, the claim that DPO training specifically enhances "trajectory direction" (Section 5.3) relies on a count of probes where the DPO model outperformed the SFT model (1,198/1,750) and a small-scale perturbation study (N=75 in Table 6). The perturbation results show large drops (e.g., -23.0 points for reversal), but without reported p-values or confidence intervals for these differences, it is difficult to assess the statistical significance of the effect size, particularly given the high variance in LLM generation. The ablation study using "MixedArc" (wrong character's arc) is a strong control, but the deterministic hash-based selection of donor characters requires a brief discussion on whether this method could inadvertently select arcs that are structurally similar to the target, potentially biasing the baseline. Finally, while the judge validation shows high correlation with humans (r=0.96), the Mean Absolute Deviation (MAD) of 4.7 points on a 100-point scale suggests a non-trivial error margin that should be contextualized when interpreting the small performance gaps (e.g., +2.2 to +8.4 points) between context modes.
