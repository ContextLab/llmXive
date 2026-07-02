---
action_items:
- id: 9979ce734b90
  severity: writing
  text: The abstract claims the dataset supports 'future loco-manipulation,' but Table
    1 shows only 277 hand-centric trajectories with no whole-body data. Rephrase to
    state it provides a 'motion-scale prior' for such tasks, not a direct resource.
- id: 3ca754657b3e
  severity: writing
  text: The introduction claims robustness 'without force sensing,' yet limitations
    admit this causes failure at high damping. Qualify the claim to 'improves robustness
    relative to baselines' to avoid implying the sensor-less problem is solved.
- id: 3f811f87c658
  severity: writing
  text: The abstract describes 56% success at x4 damping as 'high task success.' This
    overstates the result. Change to 'maintains superior relative robustness' or 'retains
    non-trivial success' to accurately reflect the 44% failure rate.
artifact_hash: aac12eff083d8d7168328cdeef9fdab897d5808d01d31c99a8c36453db9b88d3
artifact_path: projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:31:17.791555Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that slightly overreach the empirical evidence provided, particularly regarding the scope of the released dataset and the generalizability of the robustness claims.

First, the Abstract and Conclusion (lines 24-26, 338-340) claim the work provides a "pure-geometry dexterous interaction resource to support future loco-manipulation." This is an overstatement. The dataset described in Section 3.3 and Table 1 consists of 277 hand-object trajectories for 7 specific GAPartNet objects. It contains no locomotion data, no whole-body balance information, and no ground-contact dynamics. While the authors correctly note in the Limitations (lines 356-360) that the dataset *could* serve as a prior for whole-body control, presenting it as a resource *for* loco-manipulation implies a completeness it does not possess. The text should be tempered to state the dataset provides a "motion-scale prior" or "upper-body initialization" for such future work, rather than a direct resource.

Second, the claim in the Introduction (lines 58-60) that PICA improves robustness "without requiring additional force sensing" is technically true but risks over-claiming the method's capability. The Limitations section (lines 348-352) explicitly admits that the lack of force/tactile feedback is the primary reason for failure under strong damping (x4). The current phrasing suggests the method has solved the robustness problem without sensors, whereas the data shows it merely mitigates it better than baselines within a specific, limited regime. The claim should be qualified to "improves robustness *relative to baselines* without additional force sensing" or "extends the robustness envelope of kinematic-only policies."

Finally, the Abstract (line 23) states the method maintains "high task success" across damping conditions. Table 1 shows a drop from 89% to 56% success at x4 damping. While 56% is the best among baselines, characterizing a 44% failure rate under OOD conditions as "high task success" is an over-interpretation of the results. It is more accurate to claim the method "maintains superior relative robustness" or "retains non-trivial success" under strong contact-load shifts. These adjustments will align the paper's narrative more strictly with the quantitative evidence.
