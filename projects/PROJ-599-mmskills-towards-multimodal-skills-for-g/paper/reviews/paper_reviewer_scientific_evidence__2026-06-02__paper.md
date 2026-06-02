---
action_items:
- id: 9bdfec0d600d
  severity: science
  text: Add statistical significance testing (e.g., bootstrap confidence intervals
    or paired t-tests) for all main performance tables to confirm gains are not due
    to random variance.
- id: d3416e42cd2d
  severity: science
  text: Report multi-seed results (e.g., 3-5 seeds) with standard error bars to address
    the high variance observed in baseline performance (e.g., GLM-5V Text-only drop
    in Table 1).
- id: a7600e6c8c22
  severity: science
  text: Provide an explicit audit or similarity analysis confirming no task overlap
    between OpenCUA source trajectories and OSWorld/macOSWorld evaluation tasks to
    rule out data leakage.
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T20:26:38.404760Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The empirical evaluation provides broad coverage across six model families and four benchmarks, which strengthens the generalizability claim regarding multimodal procedural knowledge. Table 1 and Table 2 show consistent positive effect sizes for MMSkills over baselines, with OSWorld gains ranging from +6% to +18% absolute success rate. However, the scientific evidence lacks statistical rigor. The tables report point estimates without confidence intervals, standard deviations, or significance markers (p-values). Given the stochasticity of LLM agents, single-run reporting (implied by the absence of seed variance) is insufficient to confirm that observed gains are not due to random variation. For instance, in Table 1, GLM-5V shows a performance *drop* for Text-only skills on the "OS" domain (54.17% to 20.83%), suggesting high variance that is not captured by mean scores alone.

Additionally, the separation between skill generation sources and evaluation tasks requires stricter validation. Appendix B states skills are extracted from OpenCUA trajectories, but with 360 OSWorld test cases and 247 generated skills (Table 1 Appendix), the risk of task overlap or information leakage exists. The paper asserts separation but does not provide a task-ID overlap audit or embedding similarity analysis between source and test trajectories. This is a potential confound for the "generalization" claim. If source trajectories contain solutions to evaluation tasks, the gains reflect memorization rather than skill transfer. Finally, the ablation studies (Figure 3) rely on visual inspection of bar charts without error bars. To robustly support the claim that branch loading and state cards are necessary, statistical tests comparing ablated variants against the full MMSkills condition are needed. Reporting multi-seed averages (e.g., 3-5 seeds) with standard error bars for all main tables would significantly strengthen the evidence base.
