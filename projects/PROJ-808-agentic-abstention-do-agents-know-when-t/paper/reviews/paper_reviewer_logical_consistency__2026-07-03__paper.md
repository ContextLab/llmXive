---
action_items:
- id: 97102fa2f10f
  severity: writing
  text: The manuscript presents a coherent argument for the necessity of "Agentic
    Abstention" as a distinct capability from single-turn LLM abstention. The logical
    flow from problem definition to benchmark construction and evaluation is generally
    sound. However, there are specific inconsistencies in the definition and reporting
    of metrics that undermine the internal consistency of the results. First, the
    definition of "Timely Recall" is contradictory. In Section 4.2 (Evaluation Metrics),
    the authors exp
artifact_hash: 38d0e8e4fb458c680aadb1d4bcdffd2c4f641f3bec33db525a174585bed1f06b
artifact_path: projects/PROJ-808-agentic-abstention-do-agents-know-when-t/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:27:46.057235Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a coherent argument for the necessity of "Agentic Abstention" as a distinct capability from single-turn LLM abstention. The logical flow from problem definition to benchmark construction and evaluation is generally sound. However, there are specific inconsistencies in the definition and reporting of metrics that undermine the internal consistency of the results.

First, the definition of "Timely Recall" is contradictory. In Section 4.2 (Evaluation Metrics), the authors explicitly define Timely Recall as AbsRec@1 for request-based tasks and AbsRec@2 for environment-based tasks, acknowledging that the "warranted step" ($w_i$) differs (immediate vs. after one interaction). However, in Section 5.1 (Results) and Table 1, the authors report a single "Timely Recall" value for the WebShop benchmark (26.7% for Llama-3.3-70B). Since WebShop contains 251 environment-based tasks (Missing Target), the reported metric should logically be AbsRec@2 if the definition in Section 4.2 is strictly followed. Reporting AbsRec@1 for these tasks would penalize agents for not abstaining *before* the environment reveals the impossibility, which contradicts the definition of $w_i$ for environment-based tasks. This inconsistency makes it impossible to verify if the reported "Timely Recall" figures are comparable across the different task categories.

Second, the causal claim regarding model scale is not fully supported by the presented evidence. The Introduction states that "larger or more capable models sometimes perform worse at timely abstention." While the paper notes that scaling improves overall recall, the evidence for the negative impact on *timely* recall is mixed and confounded by the benchmark. For instance, in the QA scenario, the largest model (Qwen3-235B) achieves the highest timely recall (0.59), whereas in WebShop, the smaller Llama-8B has a lower timely recall than Llama-70B. The claim that larger models perform *worse* is not consistently demonstrated across the reported data points; rather, the data suggests that performance is highly dependent on the specific task category (e.g., Missing Target vs. False Premise) rather than a simple inverse relationship with model scale. A more nuanced discussion or a controlled comparison is needed to support this specific causal assertion.

Finally, there is a slight logical tension between the treatment of "clarification" as "abstention" and the dataset construction. The authors define clarification requests as instances of ABSTAIN (Section 2). However, in the Interactive QA setup (Section 3), they explicitly exclude datasets like MuSiQue and SQuAD 2.0, which often require clarification or multi-hop reasoning where the answer is not immediately obvious. By removing these cases, the evaluation set may bias the results towards scenarios where abstention is the *only* valid stop signal, potentially inflating the perceived difficulty of "timely" abstention or masking the agent's ability to distinguish between "I need more info" (clarify) and "I cannot solve this" (abstain). This limits the generalizability of the conclusion that agents struggle to know *when* to stop, as the "stop" signal in the remaining data is binary and absolute.
