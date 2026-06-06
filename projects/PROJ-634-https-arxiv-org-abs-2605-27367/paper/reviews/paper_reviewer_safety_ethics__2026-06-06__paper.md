---
action_items:
- id: 4b1a687b67d6
  severity: writing
  text: 'Add a Data Ethics and Privacy subsection addressing: (1) consent mechanisms
    for datasets containing human subjects (e.g., ScanNet++, Aria, Waymo); (2) privacy
    protections applied to real-world imagery; (3) license compliance across all 19
    aggregated datasets. Table tab:dataset_profile_summary_cited shows licenses but
    lacks privacy discussion.'
- id: e13eabcdb338
  severity: writing
  text: Include a Dual-Use Considerations paragraph in the Limitations section (appendix/limitation.tex)
    acknowledging potential misuse of spatial foundation models for surveillance,
    autonomous weapons, or other harmful applications. This is standard practice for
    computer vision papers with deployment implications.
- id: a722fda7567d
  severity: writing
  text: "Add a Safety Considerations statement addressing deployment in safety-critical\
    \ applications (autonomous vehicles, robotics). The paper evaluates camera pose,\
    \ depth, and trajectory estimation\u2014metrics directly relevant to safety-critical\
    \ systems. Current text (secs/limitation.tex) only discusses evaluation cost and\
    \ memory constraints."
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T10:36:55.771992Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

**Safety and Ethics Review**

This benchmark paper aggregates 19 public datasets (including real-world imagery from ScanNet++, KITTI, Waymo, Aria Digital Twin, etc.) to evaluate spatial foundation models. From a safety and ethics perspective, several concerns require attention before publication:

**1. Privacy and Human Subjects (secs/related.tex, tab:dataset_profile_summary_cited)**

Many aggregated datasets contain real-world imagery potentially featuring people, private property, or sensitive locations. The paper's dataset summary table shows license information but does not address:
- Consent mechanisms for human subjects in datasets like ScanNet++, Aria Digital Twin, DROID (robot manipulation with human operators)
- Privacy protections applied to real-world imagery
- Whether any datasets include personally identifiable information

Given the paper's scale (72,540 evaluation frames across 546 scenes), a dedicated Data Ethics subsection should clarify how privacy was addressed during data aggregation and curation.

**2. Dual-Use Risks (Introduction, secs/intro.tex)**

Spatial foundation models with the capabilities evaluated here (depth estimation, camera pose, 3D reconstruction) have clear dual-use potential for surveillance, autonomous weapons systems, or other harmful applications. The paper makes no acknowledgment of these risks. This is inconsistent with current best practices for computer vision papers that discuss deployment implications.

**3. Safety-Critical Deployment Considerations (secs/limitation.tex)**

The benchmark evaluates metrics directly relevant to safety-critical systems (autonomous vehicles, robotics). The Limitations section only discusses evaluation cost, memory constraints, and hyperparameter selection. A safety considerations statement should address:
- Potential for model failures in safety-critical deployments
- Recommendations for validation before deployment
- Known failure modes from the benchmark (e.g., OOD performance in ego-view/wrist-view domains as shown in Fig. geobench_domain_ood)

**4. Conflict of Interest Disclosure**

The paper introduces a new dataset (DA-Next-5M) and model (Depth-Anything-Next) alongside the benchmark. A conflict of interest statement should clarify whether the authors have financial or institutional ties to ropedia or related organizations that could benefit from benchmark results.

These are writing-level concerns that can be addressed through manuscript revision without requiring new experiments.
