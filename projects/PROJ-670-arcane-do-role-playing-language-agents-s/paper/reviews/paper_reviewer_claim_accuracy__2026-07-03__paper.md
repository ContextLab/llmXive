---
action_items:
- id: ae1cc7fbddfa
  severity: writing
  text: Clarify if the 87.1% human plausibility in Section 5.2 refers to the 2-of-3
    axis acceptance rule in Section 3.1 or a separate probe validation step to avoid
    ambiguity.
- id: 9996a7309cba
  severity: writing
  text: The claim that PTF sensitivity ranges from -8.8 to -23.0 overgeneralizes;
    Table 5 shows DeepSeek-V4-Pro has only -1.3 sensitivity to shuffling, contradicting
    the implied universal range.
- id: ab825dee8091
  severity: writing
  text: Explicitly cite the 'Dir' sub-metric in Table 5 to support the specific claim
    that DPO improves 'trajectory direction' rather than just overall fidelity.
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:14:08.729480Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the validation of its dataset and the sensitivity of its metrics, but the supporting evidence in the text and tables occasionally overgeneralizes or lacks precise alignment.

First, in Section 3.1 ("Character Arc Construction"), the authors claim a rigorous validation process where "three human annotators independently assess axes; only those with a 2-of-3 majority enter the set." Later, in Section 5.2 ("Evaluation validation"), the paper reports "Human plausibility is 87.1%." While these numbers are likely related, the text does not explicitly clarify if the 87.1% refers to the acceptance rate of the *axes* (the 2-of-3 rule) or the *probes* generated from them. The Appendix (Table 6) details a "Human-anchored validation" with 210 binary verdicts, but the link between the 2-of-3 rule in Section 3.1 and the 87.1% figure in Section 5.2 is ambiguous. The claim that the dataset is "validated" relies on this specific 2-of-3 mechanism, but the reported metric (87.1%) appears to be a plausibility score of the *responses* or *judges* rather than the raw acceptance rate of the axes. This conflation weakens the claim of rigorous dataset construction.

Second, the claim in Section 4.2 regarding the Phase Trajectory Fidelity (PTF) metric is slightly overstated. The text states: "PTF is sensitive to phase-order corruption (-8.8 to -23.0 points)." Table 5 ("PTF Metric Validity") supports the -23.0 figure for the \ours{}-32B-DPO model under the "reverse_response" condition. However, for the DeepSeek-V4-Pro model, the drop for "shuffle_response" is only -1.3 points, and for "reverse_response" it is -6.3 points. The range "-8.8 to -23.0" effectively excludes the DeepSeek model's performance, which shows minimal sensitivity to shuffling. By presenting the range as a general property of the metric without qualifying that it applies primarily to the fine-tuned models or specific perturbation types, the claim misrepresents the metric's behavior across the full experimental scope.

Finally, Section 4.3 claims that "DPO improves trajectory direction; SFT often holds a static voice." While the overall scores in Table 3 support the superiority of DPO, the specific claim about "trajectory direction" is not explicitly broken down in the main text. Table 5 does provide "Align" and "Dir" sub-scores, showing a larger drop in "Dir" for the DPO model under perturbation, which supports the claim. However, the text should explicitly reference these sub-metrics to substantiate the specific claim about "direction" rather than relying on the aggregate "Overall" score, which conflates direction with other fidelity aspects.

These issues are primarily matters of precision in reporting rather than fundamental flaws in the science. The data exists to support the claims, but the textual assertions need to be more tightly bound to the specific conditions (e.g., model type, perturbation type) under which the numbers hold.
