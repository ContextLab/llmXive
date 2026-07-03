---
action_items:
- id: bb9fc1ca5db5
  severity: writing
  text: The paper presents a comprehensive benchmark (SpatialBench) and a new model
    (Depth-Anything-Next, \ours), but the experimental design contains significant
    confounds that prevent the evidence from fully supporting the specific claims
    about architectural superiority and data quality. First, the headline claim that
    \ours achieves +47% to +59% depth gains over DA3-Giant (Table 1) is confounded
    by training data. The paper states \ours was trained on a new, curated dataset
    (\dataset) specifically desi
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T21:32:24.714996Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive benchmark (SpatialBench) and a new model (Depth-Anything-Next, \ours), but the experimental design contains significant confounds that prevent the evidence from fully supporting the specific claims about architectural superiority and data quality.

First, the headline claim that \ours achieves +47% to +59% depth gains over DA3-Giant (Table 1) is confounded by training data. The paper states \ours was trained on a new, curated dataset (\dataset) specifically designed to address egocentric/wrist-view gaps, while DA3-Giant was trained on a different mixture. The design does not isolate whether the performance gain comes from the architectural changes (scale tokens, camera conditioning) or simply from the superior quality and domain relevance of the new training data. To support the claim that the *model* is better, the authors must run a control experiment training the baseline DA3-Giant architecture on the exact same \dataset mixture with identical hyperparameters. Without this, the gain is indistinguishable from a data scaling effect.

Second, the paper reports single-point performance metrics (e.g., AbsRel 0.050) across 41 models without any measure of variance (standard deviation, standard error, or confidence intervals) or seed count. In 3D reconstruction tasks, results can fluctuate significantly based on random initialization, data shuffling, or minor hyperparameter sensitivities. A reported improvement of a few percentage points (e.g., the +3.1% AUC@30 gain) is well within the range of typical run-to-run variance for these models. The evidence design fails to rule out that these "improvements" are statistical noise. The authors should report results averaged over at least 3-5 random seeds with mean ± SD to demonstrate that the observed effects are stable and reproducible.

Finally, the finding that "Data quality > Volume" relies on comparing models with different architectures and different training data simultaneously. To rigorously support this, an ablation is needed where a single model architecture is trained on both the curated pseudo-GT data and a larger, noisy dataset. The current design attributes the performance difference to data quality, but it could equally be attributed to the specific architectural choices of the model trained on the curated data.

These issues do not invalidate the benchmark itself, which is a valuable contribution, but they weaken the evidentiary support for the specific claims regarding the new model's architecture and the specific drivers of performance gains.
