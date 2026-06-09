---
action_items:
- id: f8a0e8b10c77
  severity: science
  text: Figure 1 aggregates incompatible metrics (In-Acc, F1, R-Acc) without normalization.
    Please normalize per-benchmark scores or replace with a radar chart using consistent
    scales.
- id: 40bf44cd4748
  severity: science
  text: Baseline sampling parameters vary by model recommendation. Please report results
    using a uniform decoding strategy (e.g., greedy) to control for inference variance.
- id: 4f467090c662
  severity: science
  text: LLM-as-judge filtering may introduce bias in reasoning traces. Consider evaluating
    a subset against human-annotated traces to validate reasoning quality.
artifact_hash: cde4b9ecefed3e22d66582b046d0b2e0b9bfea0dae2b1d5734c4f1cf81056f73
artifact_path: projects/PROJ-661-https-arxiv-org-abs-2606-00683/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T00:42:34.593152Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents strong empirical results on standard benchmarks (Table 2, `tables/results.tex`), demonstrating clear performance gains for OCC-RAG over same-scale baselines. The training corpus size (3.25M examples) and evaluation sample sizes (e.g., 7,405 for HotpotQA) are sufficient for statistical significance. However, the scientific evidence is weakened by methodological inconsistencies in the summary visualization and baseline control.

First, Figure 1 (`images/main.tex`) plots an "Average score (%)" on the y-axis. This metric aggregates In-Acc (HotpotQA, MuSiQue, ConFiQA), F1 (TAT-QA), and R-Acc (MuSiQue-Un). These metrics are not commensurable; for instance, a 50% F1 on TAT-QA is not equivalent to a 50% In-Acc on HotpotQA. Without normalization (e.g., per-benchmark Z-scores), this aggregate score is statistically invalid and misleads the efficiency claim. This must be corrected to ensure the trade-off curve reflects valid evidence.

Second, baseline sampling parameters are not controlled. Section 5.1 states, "For all of these models, we use sampling parameters as recommended in the corresponding technical reports." This introduces variance; some baselines may use greedy decoding while others use sampling (e.g., temperature 0.7), confounding the performance comparison. To strengthen the evidence, the authors should report results using a uniform decoding strategy (e.g., greedy or fixed temperature) across all baselines to isolate model capability from inference hyperparameters.

Third, the training data filtering relies on an LLM-as-a-judge (`Qwen3.5-27B` in Section 3.3) in addition to exact match checks. This risks optimizing the model for the judge's specific biases rather than ground truth, potentially inflating synthetic data quality. While the exact match check mitigates this, the reasoning traces themselves are judge-generated. Reporting a subset evaluation against human-annotated reasoning traces would strengthen the claim of improved reasoning structure.

Finally, the exclusion of TAT-QA arithmetic/counting questions (Section 5.1) is noted but should be explicitly framed as a limitation to avoid overclaiming general multi-hop reasoning capabilities. Addressing these points will ensure the central claims are robust to alternative explanations regarding metric validity and inference variance.
