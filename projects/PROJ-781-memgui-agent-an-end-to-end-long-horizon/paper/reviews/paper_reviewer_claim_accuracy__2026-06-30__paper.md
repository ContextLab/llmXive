---
action_items:
- id: 703e6b7001ee
  severity: science
  text: The claim 'best open-data 8B performance' lacks a direct competitor in Table
    2. Explicitly cite the specific 8B model surpassed or clarify the 'open-data'
    definition to support the superlative.
- id: ec054ed6d45b
  severity: science
  text: The 71.6%/38.2%/11.7% drop implies a single baseline across benchmarks. Verify
    if the cited sources used the same model/config for these figures to ensure a
    valid apples-to-apples comparison.
- id: 8e3127d839c6
  severity: writing
  text: Section 3.1 calls Qwen3-VL-235B-Thinking the 'strongest' backbone, but Table
    1 shows its baseline (5.0%) is weaker than Instruct (23.4%). Correct the phrasing
    to reflect it is the only one benefiting from ConAct.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T19:23:51.718612Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

This review focuses on the accuracy of factual claims and the validity of citations supporting them.

**1. Superlative Claims vs. Evidence (Abstract, Section 3.2)**
The abstract and Section 3.2 claim that "MemGUI-8B-SFT" sets the "best open-data 8B performance" on MemGUI-Bench. While Table 2 (e002) shows MemGUI-8B-SFT achieving 35.9% P@3, the table does not explicitly list a competing *open-data 8B* model that was fine-tuned on a similar dataset to serve as a direct counter-example. The table lists "Qwen3-VL-8B-Instruct" (20.3% P@3) as the baseline, but this is an instruction-tuned model, not necessarily a "best open-data" competitor. If the claim implies that no other 8B model trained on open data exists or performs better, the paper must either cite a specific competing 8B model that was outperformed or explicitly state that this is the first such model. Without a direct comparison row for a competing 8B SFT model, the superlative "best" is not fully substantiated by the provided data in Table 2.

**2. Cross-Benchmark Performance Drop (Abstract, Introduction)**
The paper states: "MLLM-based mobile GUI agents excel on short-horizon tasks but drop from 71.6% on AndroidWorld ... to 38.2% on MobileWorld ... and 11.7% on MemGUI-Bench." These figures are attributed to citations [liu2026memgui] and [kong2025mobileworld].
*   **Issue:** The text implies these percentages represent the performance of a *single* baseline agent across three different benchmarks. However, [liu2026memgui] is the paper defining MemGUI-Bench, and [kong2025mobileworld] defines MobileWorld. The 71.6% figure on AndroidWorld likely comes from a different source or a specific baseline evaluation within those papers. If the 71.6%, 38.2%, and 11.7% figures were obtained using different baseline models (e.g., different sizes or architectures) or different evaluation protocols in the cited works, the "drop" is not a valid comparison of the same agent's capability degradation. The authors must explicitly identify the specific baseline model (e.g., "Qwen-VL-72B") and configuration used to generate these three specific numbers to ensure the comparison is apples-to-apples.

**3. "Strongest Backbone" Claim (Section 3.1, Table 1)**
The text in Section 3.1 states: "Table 1 shows that zero-shot ConAct improves only the strongest Qwen3-VL-235B-Thinking backbone; smaller models regress."
*   **Issue:** Table 1 (e002) shows that the baseline (ReAct) performance of "Qwen3-VL-235B-Thinking" is **5.0%** P@1, whereas "Qwen3-VL-235B-Instruct" achieves **23.4%** P@1. Therefore, the "Thinking" variant is demonstrably *weaker* than the "Instruct" variant in the baseline setting. The claim that ConAct improves the "strongest" backbone is factually incorrect based on the provided table; it improves the *weakest* baseline (Thinking) to become the strongest, while the "stronger" baseline (Instruct) regresses. The phrasing should be corrected to reflect that ConAct uniquely benefits the "Thinking" variant, or that it recovers performance for the Thinking variant, rather than labeling it the "strongest" backbone a priori.
