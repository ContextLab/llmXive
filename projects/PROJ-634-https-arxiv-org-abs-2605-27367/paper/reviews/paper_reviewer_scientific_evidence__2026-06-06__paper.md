---
action_items:
- id: 63d72bc73269
  severity: science
  text: Report scene-level variance (std dev) for key metrics in main tables (e.g.,
    Tab:main_leaderboard_filtered) to assess robustness beyond point estimates.
- id: 25b04ac8e9e4
  severity: science
  text: Clarify data overlap between DA-Next training sets (Tab:training_datasets)
    and benchmark evaluation sets (Tab:datasets_summary) to rule out data leakage
    on Ego/Wrist views.
- id: 59804c266daf
  severity: science
  text: Justify hyperparameter consistency across paradigms; TTT methods may require
    specific tuning not captured by 'recommended configurations' (Appendix:limit).
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T10:38:33.249748Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the benchmark's breadth (546 scenes, 19 datasets) is strong, providing a robust foundation for the claim that current models lack all-round capabilities. However, evidence regarding the specific superiority of the proposed **DA-Next** model requires clarification to ensure claims are not confounded by data overlap.

First, **data leakage risk** exists between the training and evaluation sets. `secs/danext.tex` indicates DA-Next is trained on datasets including **Xperience**, **Aria**, and **RoboTwin**. These same datasets are explicitly included in the benchmark evaluation (`tabs/datasets/ropedia.tex`, `tabs/datasets/adt.tex`). Since the paper highlights DA-Next's gains in **Egocentric and wrist-view domains** (`secs/new_findings.tex`), the performance improvement may reflect in-domain training data match rather than architectural generalization. To isolate the architectural contribution, the authors should report results on benchmark subsets that exclude datasets used in DA-Next training.

Second, **statistical robustness** is not fully demonstrated. Main result tables (e.g., `tabs/main_leaderboard_filtered.tex`) report single point estimates without standard deviations or confidence intervals. Given the deterministic frame selection protocol, scene-level variance is critical to determine if gains are consistent or driven by specific scene characteristics. Without variance metrics, the reported effect sizes (e.g., +47% AbsRel) lack context regarding reliability.

Third, **experimental controls** for hyperparameters need strengthening. The `appendix:limit.tex` section states models use "recommended configurations." For Test-Time Training (TTT) methods, performance is highly sensitive to learning rates and iteration counts. If baselines were not tuned to their optimal settings while DA-Next was, the comparison favors the proposed model. Explicitly stating whether per-model tuning occurred is necessary for a fair scientific comparison.

Addressing these points will solidify the evidence that DA-Next offers genuine architectural advantages rather than data-specific benefits.
