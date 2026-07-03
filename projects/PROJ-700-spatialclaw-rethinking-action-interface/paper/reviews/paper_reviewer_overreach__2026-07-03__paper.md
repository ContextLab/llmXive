---
action_items:
- id: a017ec1d77ee
  severity: writing
  text: The claim of 'consistent gains' across all backbones (Abstract) contradicts
    Table 1 (main_results.tex), where Qwen3.5-397B shows negative deltas on 4/10 single-image
    benchmarks (e.g., -1.0 on ERQA). Qualify as 'consistent on average'.
- id: 1470e6d1570d
  severity: writing
  text: The claim of 'no benchmark-specific adaptation' (Abstract) is contradicted
    by the 'Planner' role (Sec 3.2, App D) which maps question shapes to tools. Refine
    to 'without fine-tuning' to avoid over-claiming prompt engineering as zero-shot.
- id: f1b70ae98aad
  severity: science
  text: The conclusion over-attributes success to the 'action interface' (Sec 6).
    Ablation (Table 2) shows removing perception tools drops performance to 51.4%
    (vs 48.7% No-tool), indicating tools drive most gains, not just the interface.
    Balance the claim.
artifact_hash: 03b4b7546f79862eef36a0d430e3a6b82062f65b52d01a2c8d4c65b5c5b34086
artifact_path: projects/PROJ-700-spatialclaw-rethinking-action-interface/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T11:11:12.915857Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the universality and mechanism of its performance gains that exceed the evidence provided in the tables and ablation studies.

First, the Abstract and Introduction assert that the framework achieves "consistent gains across six VLM backbones." This phrasing implies a uniform positive delta across all models and tasks. However, Table 1 (main_results.tex) explicitly shows that for the Qwen3.5-397B backbone, the method yields negative deltas on four single-image benchmarks (ERQA: -1.0, Omni3D: -1.9, ViewSpatial: -5.1, Video-MME: -0.5). While the *average* is positive, claiming "consistent gains" without qualification misrepresents the data, suggesting a robustness that the specific per-benchmark results do not support. The text should be amended to reflect that gains are consistent *on average* or *across most benchmarks*, rather than universally.

Second, the claim of operating "without any benchmark- or model-specific adaptation" (Abstract) is technically inaccurate. Section 3.2 and Appendix D describe a "Planner" role that is explicitly invoked to "map question shapes to tools" (e.g., coordinates -> vlm.locate + SAM3). This is a form of prompt-based adaptation or heuristic routing specific to the task structure. While the authors likely mean "without fine-tuning," the current phrasing suggests a zero-shot, zero-prompt-tuning capability that the described system does not possess. This distinction is crucial for reproducibility and fair comparison with baselines that may also use prompt engineering.

Finally, the Conclusion attributes the success primarily to the "action interface design" as a "critical driver." The ablation study in Table 2 (ablation_components.tex) challenges this interpretation. Variant (I) "No utility functions" (removing the specific code wrappers) only drops performance by 0.5% (56.9% to 56.4%), suggesting the *interface* (code execution) is indeed important, but the *specific utility functions* are not the primary driver. More critically, Variant (II) "No perception tools" drops performance to 51.4%, which is only a 2.7% gain over the No-tool baseline (48.7%). This indicates that the bulk of the performance (from 48.7% to 56.9%) is driven by the *perception tools* (Depth Anything 3, SAM3) rather than the iterative code interface itself. The paper over-attributes the success to the interface mechanism while under-acknowledging that the gains are largely contingent on the quality of the external perception models. The discussion should be balanced to reflect that the interface enables the *composition* of these tools, but the tools themselves are the primary source of the absolute performance lift.
