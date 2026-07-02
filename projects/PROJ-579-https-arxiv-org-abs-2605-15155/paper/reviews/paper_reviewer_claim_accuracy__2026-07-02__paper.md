---
action_items:
- id: 0bbb16ae8e17
  severity: writing
  text: Abstract claims +10.2% WebShop-Acc gain but omits model size. Table 1 shows
    this gain applies only to 7B (3B is +4.7%). Specify '7B' in Abstract to prevent
    misattribution.
- id: 7f201792dcd6
  severity: writing
  text: Section 3.1 claims OPSD collapses to 'near-zero' on Search-QA. Table 1 shows
    0.0 for 3B but 6.2 for 7B. Qualify claim to specify '3B model' or 'smaller models'
    for accuracy.
- id: 843a1cad2017
  severity: science
  text: Abstract claims SDAR 'consistently outperforms' baselines across all scales.
    Table 1 shows SDAR (41.9) < GRPO+OPSD (42.2) on Qwen3-1.7B Search-QA. Correct
    claim or data.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:50:54.695868Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with the provided data in Table 1 (tables/experiment.tex).

**1. Inconsistent Performance Claims in Abstract vs. Table 1**
The Abstract claims that SDAR "consistently outperforms hybrid RL–OPSD baselines across all model scales."
- **Fact Check:** In Table 1, under the **Qwen3-1.7B** model section, the **Search-QA** benchmark (Avg column) shows:
  - SDAR: **41.9**
  - GRPO+OPSD: **42.2**
- **Discrepancy:** SDAR (41.9) is strictly lower than GRPO+OPSD (42.2) on this specific benchmark and model scale. The claim of "consistent" outperformance across *all* scales is therefore factually unsupported by the provided data. The authors should either qualify the claim (e.g., "outperforms on most benchmarks") or correct the data if the table is erroneous.

**2. Ambiguity in Reported Gains**
The Abstract states: "achieves substantial improvements over GRPO (+9.4% on ALFWorld, +7.0% on Search-QA, +10.2% on WebShop-Acc)".
- **Fact Check:**
  - **WebShop-Acc (3B):** 68.0 (SDAR) - 63.3 (GRPO) = +4.7%.
  - **WebShop-Acc (7B):** 82.8 (SDAR) - 72.6 (GRPO) = +10.2%.
- **Discrepancy:** The Abstract lists "+10.2% on WebShop-Acc" without specifying the model size. However, the text in Section 3.1 clarifies this gain is for the **7B** model. The Abstract's phrasing could mislead a reader into thinking the 3B model achieved this gain. The Abstract should explicitly state "+10.2% on WebShop-Acc (7B)" to ensure accuracy.

**3. Precision of "Catastrophic Collapse" Claims**
Section 3.1 states: "standalone OPSD collapses catastrophically (near-zero on Search-QA)".
- **Fact Check:** Table 1 shows OPSD on Search-QA for **Qwen2.5-3B** is **0.0** (Avg). For **Qwen2.5-7B**, it is **6.2**.
- **Discrepancy:** While "near-zero" is accurate for the 3B model, it is an overstatement for the 7B model (6.2 is low but not zero). The claim should be qualified to specify that the collapse is observed in the 3B model.

**Recommendation:**
The paper requires minor revisions to correct the overgeneralized claim about consistent outperformance on Qwen3-1.7B Search-QA and to clarify the model-specific nature of the reported percentage gains in the Abstract. The core methodology appears sound, but the textual claims must strictly align with the tabular data.
