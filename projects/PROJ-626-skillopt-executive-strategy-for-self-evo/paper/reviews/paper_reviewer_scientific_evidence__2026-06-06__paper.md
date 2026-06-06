---
action_items:
- id: c3d5558fc272
  severity: science
  text: Report variance (standard deviation) across multiple random seeds for the
    52 cells in Table 1. Single point estimates without variance prevent statistical
    significance claims.
- id: ee480dd615be
  severity: science
  text: Justify the small training set sizes for LiveMathematicianBench (35 items)
    and ALFWorld (39 tasks). Demonstrate sensitivity to training set size to rule
    out overfitting.
artifact_hash: 50b35337a8a43777b79c281c4b9b1469c17e33c9dc40d15b61bd05b1b7b347e8
artifact_path: projects/PROJ-626-skillopt-executive-strategy-for-self-evo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T18:44:07.423419Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

## Re-Review: Scientific Evidence

This re-review assesses the current revision against the three prior action items regarding scientific robustness. While the authors have added a sensitivity analysis for training set size, the core statistical evidence remains insufficient for the strength of the claims made.

### Status of Prior Action Items

**Item c3d5558fc272 (Variance Reporting): UNADDRESSED**
Table 1 (`tab:main_results_by_harness` in `sections/3_methods.tex`) continues to report single point estimates for all 52 evaluated cells. There are no standard deviations, error bars, or footnotes indicating variance across multiple random seeds. The text in `sections/4_experiments.tex` states, "We report each benchmark's native hard score... on held-out test splits," but does not mention multiple optimization seeds. Without variance estimates, the claim that the method is "best or tied on 52 of 52 cells" cannot be statistically validated. A difference of 0.1 points between methods (e.g., 87.3 vs 87.2) is indistinguishable from noise without variance.

**Item ee480dd615be (Training Set Size): PARTIALLY ADDRESSED BUT INSUFFICIENT**
The authors added Panel (a) to Table 4 (`tab:ablation_sweeps` in `sections/3_methods.tex`), showing performance sensitivity to training set size (1 example to 100%). This demonstrates that more data generally helps (e.g., LiveMath 59.1 → 70.5). However, the justification for using the small default pools (35/39 items) remains weak without confidence intervals. The sensitivity analysis itself uses single points, so it is unclear if the gains (e.g., 64.8 vs 65.9) are significant. The text in `sections/4_experiments.tex` notes the pools are "tightly bounded" but does not rule out overfitting on these small sets without statistical evidence.

**Item 9b8c3e5ee02f (Compute Budgets): ADDRESSED**
The text in `sections/4_experiments.tex` under "Cost per point of test-set gain" now explicitly contextualizes the 70x variance in training token costs ("Two regimes are visible..."). This adequately explains the efficiency claims without requiring normalization.

### New Issues
No new scientific evidence issues were introduced in this revision.

### Recommendation
The variance requirement (Item c3d5558fc272) is critical for any claim of statistical dominance. The revision must run the main experiments with multiple seeds (e.g., 3-5) and report standard deviations in Table 1. The training set justification should be strengthened by discussing the confidence intervals or significance tests on the sensitivity data.
