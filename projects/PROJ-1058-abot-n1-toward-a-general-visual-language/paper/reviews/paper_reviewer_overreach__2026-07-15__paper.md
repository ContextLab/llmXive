---
action_items:
- id: e215beb05d8d
  severity: writing
  text: Abstract claims the method 'ensures robust... navigation across... real-world
    benchmarks,' but Section 6.2 only provides qualitative case studies on one robot.
    No quantitative real-world metrics exist. Replace 'ensures... across real-world
    benchmarks' with 'demonstrates qualitative robustness on a single quadrupedal
    platform' or add quantitative real-world evaluation.
- id: 5290ee5fd3b3
  severity: writing
  text: Abstract states the method 'solves' coordinate drift and long-tail semantics.
    Results show significant reduction (e.g., 35% POI boost) but not elimination (4.6%
    indoor failure remains). Change 'solves' to 'significantly mitigates' to align
    with residual error rates.
- id: accb8b73fb4b
  severity: writing
  text: Introduction/Conclusion claim a 'general' model for 'open-world environments,'
    yet experiments cover only five specific tasks on fixed benchmarks. No zero-shot
    transfer to new tasks or unstructured domains is shown. Narrow the claim to 'generalist
    within the five evaluated tasks' or provide broader generalization evidence.
- id: d3554b2ac991
  severity: writing
  text: Conclusion states the model 'achieves state-of-the-art results on all five
    benchmarks.' However, Table 1 shows RxR-CE SR (73.9%) is second to Qwen-RobotNav-4B
    (75.2%). Clarify that SOTA is achieved on primary metrics or specify which metrics
    lead, as the current claim is factually inaccurate for RxR SR.
artifact_hash: f88378b8f34f2b343e5f44980e669d21b209180df8e509a6c35972c8ebfdc6e7
artifact_path: projects/PROJ-1058-abot-n1-toward-a-general-visual-language/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T03:45:05.129668Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several broad claims about the generality, robustness, and completeness of the ABot-N1 model that exceed the scope of the provided evidence.

First, the **Abstract** and **Conclusion** assert that the model "ensures robust, generalizable, and interpretable navigation across simulation and real-world benchmarks." While the simulation results are extensive, the "real-world" evidence is limited to qualitative case studies (Section 6.2, Figures 6-10) on a single quadrupedal robot platform. No quantitative metrics (Success Rate, SPL) are reported for the real-world deployment, nor is the method tested on different robot embodiments. The claim of "ensuring" robustness across real-world benchmarks is not licensed by qualitative examples alone. The text should be hedged to reflect that real-world generalization is *demonstrated qualitatively* on a specific platform, or quantitative real-world results must be added.

Second, the **Abstract** uses the strong verb "solves" regarding challenges like "coordinate drift and poor handling of long-tail semantics." The experimental results (Section 6.1) show significant *improvements* (e.g., a 35% boost in POI arrival, reducing failure rates from ~58% to ~23% in some cases), but they do not eliminate these problems. A 4.6% failure rate on indoor point-goal navigation (Table 4) indicates the problem is not "solved." The language should be adjusted to "significantly mitigates" or "substantially reduces" to accurately reflect the residual error rates.

Third, the **Introduction** and **Conclusion** frame ABot-N1 as a "general" foundation model for "open-world environments." The evaluation is strictly confined to five specific navigation tasks (point-goal, object-goal, POI-goal, instruction-following, person-following) on a fixed set of benchmarks (R2R-CE, RxR-CE, OVON, EVT-Bench, and two new internal benchmarks). There is no evidence of zero-shot transfer to entirely new task types (e.g., exploration, manipulation) or performance in truly open-world, unstructured environments outside the training distribution. The claim of "generality" should be scoped to "generalist within the five evaluated navigation tasks" or supported by broader generalization experiments.

Finally, the **Conclusion** states the model "achieves state-of-the-art results on all five benchmarks." While the model leads on most metrics, Table 1 shows that on the RxR-CE Val-Unseen split, ABot-N1's Success Rate (73.9%) is second to Qwen-RobotNav-4B (75.2%). The summary statement is therefore factually imprecise regarding the "all five" claim if interpreted as leading on every metric of every benchmark. The text should clarify that it achieves SOTA on the *primary* metrics of the tasks or specify the exact metrics where it leads.

These issues are primarily matters of rhetorical scope and honesty about limitations. They can be resolved by tightening the language in the Abstract and Conclusion to match the specific boundaries of the experimental evidence.
