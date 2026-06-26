---
action_items:
- id: 2472073933ee
  severity: writing
  text: Correct the deployment cost claim in the Introduction. Table deploy_cost.tex
    shows ~2% overhead for 150 LoRAs, not the claimed 0.5%.
- id: 8cb40f003860
  severity: science
  text: Provide statistical significance testing for the claim of surpassing teacher
    models. The CLIP difference (0.727 vs 0.726) is negligible without error bars.
- id: 771b6d4e12cf
  severity: science
  text: Quantify the zero-shot composition success rate. Currently supported only
    by qualitative figures (Fig zip_AB_Test.pdf) without metrics across the 50 effects.
- id: 2bd1181c6a9f
  severity: writing
  text: Tone down the claim of "fundamentally resolving" feature interference. A BCR
    of 8.7% indicates mitigation, not resolution.
artifact_hash: 2a1b4c65ebf4844ee4cfea5a1931c70997d4322d1755391c095bba4101b76763
artifact_path: projects/PROJ-643-collectionlora-collecting-50-effects-in/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T10:43:56.261227Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper makes several strong claims that exceed the provided evidence, requiring careful revision to align assertions with data.

First, the Introduction claims deployment costs are reduced to "0.5% of the conventional paradigm" (Intro, Contributions). However, Table `deploy_cost.tex` shows 150 LoRAs: Baseline = 150 * 2.2G = 330G, Ours = 3 * 2.2G = 6.6G. This calculates to 2%, not 0.5%. This factual inconsistency undermines the scalability claim and suggests over-optimistic reporting.

Second, the Abstract and Conclusion state the method achieves "concept fidelity comparable to or better than independently trained teacher models." Table `main_result.tex` shows CLIP 0.727 (Ours) vs 0.726 (Base/Single Effect). This 0.001 difference is negligible and lacks statistical significance testing (e.g., error bars, p-values). Claiming "better than" based on this margin is overreach; "comparable" would be more accurate.

Third, the "Zero-Shot Inference of Effects Combinations" (Sec 3.2) is supported only by qualitative figures (Fig `zip_AB_Test.pdf`). No quantitative success rate is provided for this emergent capability across the 50 effects. Claiming it as a general property without metrics is premature.

Finally, the claim to "fundamentally resolve" feature interference (Abstract) is contradicted by a Bad Case Rate (BCR) of 0.087 (8.7%). While improved over baselines, an 8.7% failure rate is not a resolution. "Significantly mitigates" would be more honest.

Limitations regarding scaling to 180 effects are honestly stated, but the specific numerical claims require correction. The paper must ensure all quantitative claims are backed by rigorous statistical analysis or corrected to reflect the actual data.
