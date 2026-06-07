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
reviewed_at: '2026-06-07T00:47:44.489209Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This re-review evaluates the current revision against the three prior action items regarding scientific evidence. None of the prior items have been adequately addressed in the provided manuscript text.

**1. Statistical Significance Testing (Item 9bdfec0d600d)**
The main performance tables (Table 1: `tab:osworld-domain-results`, Table 2: `tab:auxiliary-results`, Table 3: `tab:skill-usage-analysis`) continue to report single-point success rates or metrics without any measure of statistical significance. There is no mention of bootstrap confidence intervals, paired t-tests, or p-values in the captions or the surrounding text (Section 4). Without this, the claim that MMSkills "consistently improve" performance is not statistically supported, as the observed gains could be due to random variance in the test set or model initialization.

**2. Multi-Seed Results (Item d3416e42cd2d)**
The paper still presents results as single numbers (e.g., "44.08%", "50.11%" in Table 1). There is no indication in Section 4 (`Experiments`) or Appendix C (`Experiment Details`) that experiments were run with multiple random seeds (e.g., 3-5). Consequently, standard error bars or variance metrics are absent. This is critical for claims about robustness, especially given the noted "high variance observed in baseline performance" in the prior review (e.g., the GLM-5V Text-only drop).

**3. Data Leakage Audit (Item a7600e6c8c22)**
While the Introduction and Appendix B (`Skill Source Statistics`) state that skills are extracted from "non-test trajectories" and "public non-evaluation trajectories," there is still no explicit audit or similarity analysis provided. The manuscript asserts separation (e.g., "separate from evaluation tasks" in Section 3.2) but does not provide evidence such as a similarity score distribution, task ID cross-reference, or explicit confirmation that no evaluation task instances appear in the OpenCUA source pool. Given the reliance on public datasets (OpenCUA, OSWorld), a quantitative audit is necessary to rule out data leakage conclusively.

No new scientific evidence issues were identified in this revision, but the central claims regarding performance gains remain unsupported by the required statistical rigor. Please address the three items above to validate the empirical results.
