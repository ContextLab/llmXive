---
action_items:
- id: bfc65d1787a4
  severity: science
  text: Clarify the circular validation in Sec 4.3. The idea generator is evaluated
    using the same Intern-Atlas scoring pipeline (Sec 4.2) that relies on the graph
    used for generation. Quantitative scores in Table 4.3 are tautological. Provide
    independent metrics or ablation showing generation quality is not an artifact
    of the shared scoring function.
- id: d014cd907d52
  severity: science
  text: Report statistical significance for all comparative claims. Correlation differences
    (0.81 vs 0.58 in Fig 5a) and win rates (88% in Fig 5b) lack confidence intervals
    or p-values. Perform Fisher's Z tests for correlations and binomial tests for
    win rates to confirm robustness against sampling variance.
- id: 135969a61568
  severity: science
  text: Address the ground truth construction bias in Sec 4.1. The benchmark uses
    LLM extraction + manual audit. If the LLM logic mirrors the graph construction
    model, this risks circular validation. Detail the audit independence and consider
    a subset of purely human-curated chains for validation.
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T07:49:51.756092Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a large-scale methodological graph with strong downstream utility claims, but the scientific evidence requires tightening regarding validation independence and statistical rigor.

First, there is a critical circularity in the evaluation of the idea generator (Sec 4.3). The generator searches the Intern-Atlas graph, and its output quality is quantified using the Intern-Atlas idea evaluator (Sec 4.2), which is itself defined by the same graph topology. While human win-rates (88%) provide independent evidence, the quantitative scores in Table 4.3 (e.g., Overall 7.20) are derived from the system's own scoring function. This creates a self-fulfilling prophecy where the generator is optimized for the specific metrics of the infrastructure it builds on. The authors must clarify that the human win-rate is the primary evidence for generation quality, or provide an ablation using an external scoring metric not dependent on Intern-Atlas.

Second, statistical significance testing is absent for key comparative claims. In Sec 4.2, the correlation improvement (0.81 vs 0.58) is substantial, but without Fisher’s Z transformation or confidence intervals, we cannot rule out that this difference arises from the N=100 sample size. Similarly, the win rates in Sec 4.3 (88%, 82%, 81%) lack binomial confidence intervals. Given the multiple dimensions tested (5 dimensions + overall), there is a risk of multiple comparison inflation. Formal hypothesis testing is required to support the claim of "strong alignment" and "significant improvement."

Third, the ground truth for graph quality (Sec 4.1) relies on 30 survey papers processed by LLM extraction and manual audit. If the LLM extraction logic resembles the production graph construction pipeline, the "ground truth" may be biased toward the system's own extraction patterns. The audit process needs more detail on how human reviewers verified edges independent of the LLM's logic. Additionally, there is a discrepancy in sample size reporting: the Abstract claims 1,030,314 papers, while Appendix C lists 66,431 full texts. Clarifying whether the 1M figure includes stub nodes or references is necessary for reproducibility of the extraction scale.

Finally, the temporal coherence function (App Limitations) is calibrated on post-2015 literature, limiting generalizability to older methodological shifts. A sensitivity analysis on the temporal window would strengthen the robustness of the lineage reconstruction claims.
