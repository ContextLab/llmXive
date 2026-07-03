---
action_items:
- id: c8ee1eca6cf2
  severity: writing
  text: The claim of establishing the 'strongest open-data mobile GUI agent' is overreaching
    given ForgeQwen3-8B's 10.3% MobileWorld score, which is lower than OpenMobile-8B's
    17.7%. Qualify this claim to specify 'strongest among 8B models' or 'strongest
    using annotation-free adaptation' to avoid misleading readers.
- id: f6533d7a7735
  severity: writing
  text: The abstract states the adapted generalist (67.2%) is 'close to' the closed-data
    base (69.0%), but omits that the adapted specialized model reaches 77.6%. This
    framing conflates the adapted generalist's performance with the specialized model's
    potential, overstating the generalist's relative capability. Clarify the comparison
    targets.
- id: a581942f213b
  severity: writing
  text: The paper claims 'annotation-free' adaptation, yet relies on human-curated
    benchmarks (AndroidWorld/MobileWorld) for task generation and evaluation. The
    system is not fully autonomous in an open world. Clarify that 'annotation-free'
    applies to training data generation, not the entire evaluation or task definition
    pipeline.
artifact_hash: eb6909e8c26be542682832f5d7b13c92b92b728f8b94fb6c9612acad1621be79
artifact_path: projects/PROJ-782-mobileforge-annotation-free-adaptation-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:30:16.817085Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding the "strongest" performance and the degree of "annotation-free" adaptation that slightly exceed the evidence provided in the results tables.

First, the Abstract and Conclusion assert that the method establishes the "strongest open-data mobile GUI agent in our evaluation." While the adapted ForgeOwl-8B (41.0%) outperforms other open-data 8B models, the ForgeQwen3-8B variant achieves only 10.3% on the MobileWorld out-of-domain benchmark. This is substantially lower than the 17.7% reported for OpenMobile-8B (Table 2, Section 4.3). By grouping these results under a single "strongest" claim without qualification, the paper risks misleading readers about the generalizability of the generalist model. The claim should be refined to specify "strongest among 8B models adapted via annotation-free methods" or similar, acknowledging that other open-data baselines (like OpenMobile) perform better on out-of-domain tasks without this specific adaptation pipeline.

Second, the Abstract states that the adapted Qwen3-VL-8B (67.2%) is "close to" the closed-data GUI-Owl-1.5-8B base (69.0%). This framing obscures the fact that the *adapted* GUI-Owl-1.5-8B (ForgeOwl-8B) achieves 77.6%, a significant 8.6 percentage point improvement over its base. The narrative suggests the adaptation brings the generalist up to the level of the *base* specialized model, but the specialized model itself benefits greatly from the same adaptation. The text should clarify that the adaptation pipeline improves both models, and the "close to" comparison is specifically between the adapted generalist and the *unadapted* specialized base, not the adapted specialized model.

Finally, the repeated emphasis on "annotation-free" adaptation (Abstract, Introduction) implies a complete lack of human supervision. However, the task generation relies on MobileGym exploring specific apps within the AndroidWorld and MobileWorld benchmarks, which are human-curated environments with predefined task structures. While the *rollout data* is not manually labeled, the *task definitions* and *evaluation metrics* are human-defined. The paper should temper claims of "fully annotation-free" to "annotation-free training data generation" to accurately reflect that the system operates within a human-structured evaluation framework rather than a truly open, unstructured environment.
