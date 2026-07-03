---
action_items:
- id: 404d91ee16c5
  severity: science
  text: The claim that 'clean accuracy vastly overestimates epistemic resilience'
    relies on a comparison between clean accuracy (71.1%) and Type 1 ASR (51.5%).
    These are not directly comparable metrics (accuracy vs. attack success rate).
    The paper should explicitly compare clean accuracy to Type 1 accuracy (38.0%)
    to logically support the 'overestimation' claim, or clarify the metric relationship.
- id: 1409581069ee
  severity: writing
  text: In Section 3.4, the paper states Type 2 accuracy 'returns to 70.5% without
    eliminating ASR failures.' However, Table 2 shows Type 2 ASR is 18.7%. The text
    implies a contradiction between high accuracy and high failure rate, but the numbers
    show a significant drop in failure rate. The narrative needs to reconcile the
    high accuracy with the remaining ASR to avoid logical confusion.
- id: 9929edc855eb
  severity: writing
  text: The conclusion states 'Formal rule-like injections cause the most failures,'
    citing authority framing (69.5% ASR) and exception poisoning (64.1% ASR). However,
    Table 3 shows 'Threshold/Reference Corruption' has a mean ASR of 60.9%, which
    is close to exception poisoning. The text should clarify if 'rule-like' encompasses
    both or if the distinction is statistically significant, as the current phrasing
    implies a clear hierarchy that the data only partially supports.
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:51:35.843031Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent logical framework for defining and measuring "epistemic resilience," but there are minor inconsistencies in how specific metrics are compared and interpreted in the text versus the data tables.

First, the central claim in the Introduction and Conclusion—that clean accuracy "vastly overestimates" resilience—is logically supported by the drop in performance under attack, but the specific metrics cited in the text create a slight logical friction. The authors compare Clean Accuracy (71.1%) directly to Attack Success Rate (ASR, 51.5%) to illustrate the gap. Logically, a more direct comparison would be Clean Accuracy (71.1%) versus Type 1 Accuracy (38.0%). While the ASR metric is valid for measuring the attack's success, equating the "overestimation" gap to the difference between accuracy and ASR (which are different scales) is slightly imprecise. The argument would be tighter if the text explicitly contrasted the 71.1% clean success rate against the 38.0% success rate under Type 1 attacks.

Second, in Section 3.4 (Delivery Protocols), the text states that Type 2 accuracy "returns to 70.5% without eliminating ASR failures." The data shows Type 2 ASR is 18.7%. While 18.7% is non-zero, the phrasing "without eliminating" combined with the high accuracy figure (70.5%) creates a slight narrative tension. The logic holds that failures exist, but the text could be clearer that the *rate* of failure drops significantly (from 51.5% to 18.7%) rather than implying a persistent high level of failure that contradicts the high accuracy.

Finally, the taxonomy analysis claims "Formal, rule-like falsehoods are most damaging," citing Authority framing (69.5%) and Exception Poisoning (64.1%). The data in Table 3 shows Threshold/Reference Corruption at 60.9%, which is statistically close to Exception Poisoning. The text treats Exception Poisoning as the distinct peak, but the data suggests a cluster of high-risk categories. While not a fatal flaw, the conclusion would be more logically robust if it acknowledged this cluster of "rule-like" failures rather than singling out one specific type as the sole maximum, or if it provided a statistical justification for the distinction.

Overall, the causal mechanisms (misleading context -> reduced accuracy) are well-supported, and the internal logic of the benchmark design is sound. These are primarily issues of precise metric comparison and narrative framing rather than fundamental logical contradictions.
