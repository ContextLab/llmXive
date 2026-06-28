---
action_items:
- id: 84c61431242b
  severity: science
  text: Revise Abstract and Section 5.3 claims regarding 'other role-playing model
    families'. Appendix Table tab:main_results_added shows HER-32B performs better
    with RAG than Arc on Overall (47.0 vs 46.4) and In-Scenario metrics, contradicting
    the claim that the Arc pattern carries over universally.
- id: 1ce980d5b523
  severity: writing
  text: Qualify the Conclusion's statement about low-popularity novels. Section 3.3
    labels this slice 'unvalidated' (no human annotation), yet the Conclusion presents
    it as a robust carry-over of the benchmark's success without this caveat.
- id: c6dd9fd9349e
  severity: writing
  text: Correct the numerical range in the Conclusion. The text claims a lift of '+4.1
    to +15.3', but Appendix Table tab:main_results_extra3 shows ArcANE-32B achieves
    a lift of 16.2 (65.5 - 49.3) on the low-popularity slice.
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T09:50:59.171794Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

This review focuses on over-claiming and extrapolation beyond the provided evidence. While the core contribution of ArcANE is well-motivated, several claims in the Abstract and Conclusion overstate the generalizability and robustness of the findings based on the provided data.

**1. Overgeneralization to Other Model Families**
The Abstract states: "The same pattern carries over to other role-playing model families." Section 5.3 reinforces this, claiming "Every entry has a non-negative lift on In-World and Out-of-World." However, Appendix Table `tab:main_results_added` contradicts this for the HER-32B model.
- **Overall:** HER-32B achieves 47.0 with RAG vs. 46.4 with Arc. Arc does *not* top every strategy here.
- **In-World:** HER-32B achieves 34.9 with LifeChoice vs. 34.6 with Arc. The lift is negative (-0.3), contradicting the "non-negative lift" claim.
This is a significant overreach. The claim should be restricted to the six primary models evaluated in Section 5.1, or the text must acknowledge exceptions in the added baselines.

**2. Validation Status of Low-Popularity Slice**
The Conclusion states: "The lift carries to two held-out low-popularity novels...". This implies the robustness of the main findings extends to this slice. However, Section 3.3 explicitly defines this slice as "unvalidated" (no human annotation, only automatic filtering). Presenting these results in the Conclusion without qualifying their "unvalidated" status overstates the reliability of the benchmark's performance on this specific subset.

**3. Numerical Inaccuracy**
The Conclusion claims the lift on low-popularity novels ranges from "+4.1 to +15.3". Appendix Table `tab:main_results_extra3` shows ArcANE-32B achieves an Overall score of 65.5 (Arc) vs. 49.3 (RAG), a lift of 16.2. This exceeds the claimed maximum, suggesting a minor data reporting error.

**Recommendation**
The paper requires minor revisions to align claims with the data. Specifically, temper the generalization claims regarding "other model families" in the Abstract and Section 5.3, and add a caveat in the Conclusion regarding the validation status of the low-popularity slice. Correcting the numerical range is also necessary for accuracy.
