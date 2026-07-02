---
action_items:
- id: 8571e2559612
  severity: science
  text: The scientific evidence supporting the core claims of Intern-Atlas is currently
    insufficient to warrant acceptance. While the system architecture is sophisticated,
    the empirical validation relies heavily on proxies and lacks rigorous statistical
    grounding. First, the evaluation of the SGT-MCTS algorithm (Section 4.1, Table
    1) presents point estimates (e.g., Node Recall 84.8%) without any measure of variance,
    confidence intervals, or statistical significance testing. Given that MCTS is
    a stochast
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:11:47.000992Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the core claims of Intern-Atlas is currently insufficient to warrant acceptance. While the system architecture is sophisticated, the empirical validation relies heavily on proxies and lacks rigorous statistical grounding.

First, the evaluation of the SGT-MCTS algorithm (Section 4.1, Table 1) presents point estimates (e.g., Node Recall 84.8%) without any measure of variance, confidence intervals, or statistical significance testing. Given that MCTS is a stochastic algorithm and the benchmark is derived from survey papers (which may have subjective interpretations of "evolution"), the observed improvements over Beam Search could be due to random variance or specific benchmark artifacts rather than a robust algorithmic advantage. The authors must report results over multiple random seeds and provide statistical tests (e.g., t-tests or bootstrap confidence intervals) to substantiate the claim of "much closer" recovery.

Second, the evaluation of the idea evaluator (Section 4.2) suffers from a fundamental circularity. The system is trained on a corpus of published papers, and its performance is validated against a "Strata Dataset" where the ground truth is the *publication venue* of the paper. Since the graph is constructed from these same venues, the system is effectively being tested on whether it can recognize the patterns of the data it was built from. This does not prove the system can evaluate the *quality* of an idea; it only proves it can identify papers that look like previously accepted papers. The claim that the graph provides a "more reliable basis" than LLMs is not supported by an independent ground truth (e.g., future citation impact or blind expert evaluation of the *idea* stripped of its publication context).

Third, the human evaluation for idea generation (Section 4.3) reports high win rates (88% vs No-KB) but lacks necessary statistical details. The sample size (100 queries) and the specific blinding protocol are not fully transparent. If experts could infer the source of the idea based on writing style or specific formatting, the "blind" nature of the evaluation is compromised. Additionally, the comparison against BM25 RAG (81% win rate) is less dramatic, suggesting the advantage may be marginal in realistic retrieval scenarios.

Finally, the reliance on LLMs for the core graph construction (edge typing, bottleneck extraction) introduces a significant source of noise. The paper acknowledges a 70.4% accuracy for the production model in edge classification but fails to perform an error propagation analysis. It is unclear how a 30% error rate in identifying causal relationships impacts the downstream lineage reconstruction and idea generation. Without quantifying the sensitivity of the final results to these extraction errors, the robustness of the "causal network" claim remains unproven. The authors must address these methodological gaps by providing statistical rigor, independent ground-truth evaluations, and error analysis.
