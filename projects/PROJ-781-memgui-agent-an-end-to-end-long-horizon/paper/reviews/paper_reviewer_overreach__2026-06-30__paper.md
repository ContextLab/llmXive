---
action_items:
- id: e78c2ef8a83e
  severity: science
  text: The claim that MemGUI-8B-SFT sets the 'best open-data 8B performance' on MemGUI-Bench
    (Abstract, Sec 5.2) is overreaching. Table 2 shows GUI-Owl-1.5-32B (32B) achieving
    43.9% SR on MobileWorld, but the paper does not explicitly compare MemGUI-8B-SFT
    against other open 8B models (e.g., Qwen-VL-8B variants with different memory
    modules) on the *same* benchmark to justify the superlative 'best'.
- id: b5c1cf689b21
  severity: science
  text: The assertion that ReAct-style prompting causes 'information loss' of critical
    UI facts (Abstract, Intro) is a causal claim not directly supported by the provided
    data. The paper shows performance drops but does not present an ablation or analysis
    isolating 'information loss' from other ReAct failure modes (e.g., reasoning errors,
    action hallucination) as the primary cause.
- id: c1e3c65a5146
  severity: writing
  text: The claim that ConAct 'saves ~1.5k input tokens by step 150' (Fig 1 caption)
    lacks a clear baseline definition. Is this compared to a naive ReAct baseline
    with no truncation? If the baseline is truncated, the comparison is invalid. The
    methodology for this token count calculation is not detailed in the text.
- id: 59d9084f33b7
  severity: science
  text: The paper states MemGUI-8B-SFT 'generalizes to MobileWorld' (Abstract, Conclusion)
    based on a 17.9% SR. However, Table 3 shows GUI-Owl-1.5-32B achieving 43.9% on
    the same benchmark. Claiming 'generalization' as a primary contribution without
    addressing the significant performance gap with larger open models or explaining
    why 17.9% constitutes a successful generalization is an overstatement of the result's
    significance.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T19:24:18.515887Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the immediate evidence provided in the text and tables, specifically regarding the uniqueness of the results and the causal mechanisms of failure.

First, the Abstract and Conclusion claim that MemGUI-8B-SFT achieves the "best open-data 8B performance" on MemGUI-Bench and generalizes to MobileWorld. While Table 2 shows MemGUI-8B-SFT outperforming the base Qwen3-VL-8B-Instruct, the paper fails to compare against other open-source 8B models that might employ different memory strategies or architectures. Furthermore, on MobileWorld (Table 3), the 17.9% success rate is significantly lower than the 43.9% achieved by GUI-Owl-1.5-32B. Labeling the 8B result as "best" without a comprehensive sweep of the 8B landscape or a discussion on why the 32B model is not considered in the "open-data 8B" category (if it is not 8B, the comparison is apples-to-oranges, but the claim needs to be precise) is an overreach. The term "best" implies a definitive ranking that the current experimental setup does not fully support.

Second, the paper attributes the performance drop in long-horizon tasks to "prompt explosion" and "information loss" caused by ReAct-style prompting (Abstract, Introduction). While the performance drop is evident, the paper does not provide a direct analysis isolating "information loss" as the specific failure mode. The failure analysis (Fig 5) categorizes errors into process/output hallucination, knowledge deficiency, etc., but does not explicitly link these to the *loss* of specific UI facts due to context length. Without an ablation showing that preserving facts (without the other ConAct components) solves the problem, the causal claim that ReAct causes "information loss" is an extrapolation.

Finally, the token savings claim in Figure 1 caption ("saves ~1.5k input tokens by step 150") is ambiguous. It is unclear if this is compared to a ReAct baseline that appends *all* history without truncation, or a baseline that also truncates. If the baseline is truncated, the savings might be negligible. The methodology for calculating this specific number is not detailed in the text, making the claim difficult to verify and potentially misleading.

To address these overreaches, the authors should: (1) Clarify the comparison set for the "best 8B" claim, explicitly stating if other 8B models were tested and why they were excluded or outperformed; (2) Provide evidence or a more nuanced discussion linking the specific failure modes to "information loss" rather than just general performance degradation; (3) Explicitly define the baseline for the token savings calculation.
