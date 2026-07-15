---
action_items:
- id: 9793c1be2148
  severity: writing
  text: Abstract claims 'in-the-wild' success, but experiments use 4 curated, synchronized
    datasets. Narrow claim to 'evaluated sparse-view benchmarks' or define 'in-the-wild'
    scope explicitly.
- id: 0b27bb60ab29
  severity: writing
  text: Conclusion claims 'practical deployment' readiness, yet limitations admit
    failure on dynamic objects and shadows. Qualify deployment claim to exclude scenarios
    requiring these features.
- id: db11fb9272f0
  severity: writing
  text: Abstract claims 'first pipeline' without qualifying scope. Add 'to our knowledge'
    or specify 'among Gaussian-based pipelines' to align with the limited baseline
    comparison provided.
artifact_hash: ca7acd8eb96627c08c8e24703eed6a4159188067f14a19009f5f71e7f58b21ed
artifact_path: projects/PROJ-1056-4d-human-scene-reconstruction-from-low-o/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T02:34:10.186004Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a robust methodology for 4D reconstruction under sparse-view constraints, but the rhetoric in the abstract and conclusion occasionally exceeds the specific boundaries of the experimental evidence.

First, the term "in-the-wild studio capture" is used to frame the problem and the solution's applicability. While the introduction defines this as "sparse, low-overlap cameras... in sports venues, healthcare facilities, and home environments," the experimental validation is restricted to four specific, curated datasets (EgoHumans, Harmony4D, Mobile Stage, SelfCap) with synchronized, calibrated inputs. The phrase "in-the-wild" typically connotes uncalibrated, asynchronous, and highly variable real-world data. By claiming the method solves the "in-the-wild" problem based solely on these curated benchmarks, the paper risks overgeneralizing its robustness to truly unstructured environments. The abstract's claim of achieving state-of-the-art results across "diverse real-world datasets" should be tempered to reflect the specific nature of the evaluated datasets.

Second, the conclusion asserts that the method brings high-fidelity capture "closer to practical deployment." However, the limitations section explicitly notes that the method cannot reconstruct dynamic objects (like basketballs or props) and that shadows are baked into the static background, failing to follow human motion. These are significant functional gaps for many "practical" use cases in sports or interactive scenarios. The claim of practical readiness overreaches the demonstrated capabilities; the text should qualify the deployment claim to exclude scenarios requiring dynamic object handling or accurate shadow interaction.

Finally, the claim of being the "first pipeline" to achieve this specific combination of high-fidelity reconstruction and consistent refinement is strong. While the paper compares against relevant baselines, the absolute "first" claim requires a comprehensive survey of all prior art to be fully substantiated. A more precise phrasing, such as "the first among Gaussian-based pipelines" or "to our knowledge, the first to combine these specific components," would better align the claim with the evidence provided.

These are primarily rhetorical adjustments to ensure the scope of the claims matches the scope of the evidence, rather than fundamental flaws in the science.
