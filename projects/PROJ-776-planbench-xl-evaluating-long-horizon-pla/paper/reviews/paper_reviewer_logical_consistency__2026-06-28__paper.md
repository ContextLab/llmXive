---
action_items: []
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T21:23:59.118278Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.5
verdict: accept
---

The manuscript presents **PlanBench‑XL**, an interactive benchmark for evaluating long‑horizon planning of LLM agents in large‑scale tool ecosystems. Across the paper, the logical flow from problem motivation to experimental conclusions is coherent and free of internal contradictions.

1. **Problem Definition and Scope (Section *Abstract* and Appendix *Long‑Horizon*).** The authors define “long‑horizon” in two complementary ways: (i) ≥ 5 dependent tool invocations (Appendix *Tool Construction Details*), and (ii) ≈ 25 interaction turns (Appendix *Long‑Horizon*). These criteria are consistent because the former guarantees a minimum depth of reasoning, while the latter captures the overall interaction budget; no conflict arises between the two definitions.

2. **Benchmark Construction (Section *Data Construction* and Appendix *State Graph*).** The formalism of the state graph (Appendix *State Graph*) logically guarantees that a task is solvable iff the target datatype set is reachable from the initial datatype set via a sequence of tool edges. The algorithmic description (Algorithm 1) correctly derives inclusion‑minimal tool sets, ensuring that the ground‑truth paths used for evaluation are well‑defined. No circular dependencies or unreachable states are introduced, preserving logical soundness.

3. **Metrics (Appendix *Metric Details*).** All seven metrics are mathematically defined in terms of quantities introduced earlier (e.g., \(T_i\), \(S_i\), \(C_i\)). The illustrative example (Figure *metric‑illustrative‑example*) demonstrates that each metric’s computation follows directly from the definitions, confirming internal consistency.

4. **Experimental Claims (Section *Results* and Figures *accuracy‑under‑blocking*, *mechanistic_navigation_breakdown*).** The central claim—GPT‑5.4 drops from 51.90 % to 11.36 % accuracy under severe blocking—is supported by the reported numbers in the abstract and Figure *noise_combined*. The subsequent analysis (Section *Error Analysis*) explains this drop via “Irrecoverable Drift,” which is quantitatively shown to dominate failures (≈ 45 % aggregated, ≈ 72 % for GPT‑5.4). The apparent discrepancy between the aggregated 45 % and the per‑model 72 % is clarified by the authors: the former aggregates across all models, while the latter isolates GPT‑5.4, so the statements are logically compatible.

5. **Causal Explanations.** The paper attributes performance degradation to three mechanisms: (a) retrieval of unreliable tools, (b) implicit failure signals contaminating the reasoning chain, and (c) limited recovery when alternative paths are longer. Each mechanism is linked to empirical observations (e.g., Figure *noisy_tool_behavior_inner* shows high “Value Reused” after implicit failures). The causal chain is explicitly traced, and no unsupported leaps are made.

6. **Limitations and Future Work (Section *Limitations* and Appendix *Discussion*).** The authors acknowledge that the benchmark is retail‑specific and that the self‑defined retriever may differ from real‑world noisy retrievers. This self‑critique aligns with the earlier claim that “blocking approximates realistic failure modes,” preserving logical honesty.

Overall, the manuscript’s conclusions follow rigorously from its premises, the formal definitions are internally consistent, and the empirical evidence presented substantiates the causal claims. No logical contradictions or unsupported inferences were detected.
