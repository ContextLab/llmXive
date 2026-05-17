---
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:49:34.030548Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling ablation studies regarding architectural stability (Fig. 4, `fig:gdn-key-scaling`) and the necessity of the two-stage refiner (Tab. `tab:ltx23_original_refiner_ablation`). However, the central claims regarding performance superiority lack sufficient statistical evidence. Table 1 (`tab:vbench`) reports point estimates for Pose Accuracy and VBench scores without error bars or standard deviations across multiple seeds. Given the stochastic nature of diffusion models, a single run per method (implied by the table structure) is insufficient to establish statistical significance for the reported margins (e.g., RotErr 4.50 vs 10.47).

Furthermore, the evaluation protocol introduces potential noise. Camera accuracy is measured by estimating poses from generated videos using Pi3X and aligning them to ground truth (Sec. 5.2). This compounds estimation errors: if the generator produces artifacts that confuse the pose estimator, the metric reflects estimator failure rather than generation failure. The paper does not quantify the pose estimation error on the ground-truth videos themselves to establish a baseline noise floor.

The benchmark sample size (80 scenes, Sec. 5.2) is relatively small for robust claims about "stronger action-following accuracy" across diverse environments. Additionally, efficiency comparisons are confounded by resolution differences; baselines like LingBot-World are evaluated at 480p while SANA-WM uses 720p (Tab. 1), making the $36\times$ throughput claim partially attributable to resolution scaling rather than purely architectural efficiency. The training data sources (Tab. `tab:data_overview`) are diverse, but the potential for distributional shift between public videos and the benchmark's synthetic initial frames (Nano Banana Pro) is not analyzed. To strengthen the evidence, please report standard deviations over multiple seeds, validate pose estimation accuracy on ground-truth videos, and clarify whether efficiency metrics control for resolution or provide 480p baselines for fair comparison.
