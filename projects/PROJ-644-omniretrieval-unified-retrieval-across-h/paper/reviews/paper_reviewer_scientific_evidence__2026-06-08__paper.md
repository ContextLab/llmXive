---
action_items:
- id: 5360f539f94b
  severity: science
  text: Re-run experiments with multiple random seeds to report standard deviation
    or confidence intervals for all main metrics in Table 1. Single-run results (Section
    5.3) do not support statistical claims.
- id: 2866fd9c238e
  severity: science
  text: Perform statistical significance testing (e.g., t-test or permutation test)
    on the reported gains over baselines to validate that improvements are not due
    to random variance.
- id: 3453773c9c12
  severity: science
  text: Address potential evaluation bias in the LLM-as-a-Judge metric (Section 5.3).
    Using GPT-5.4-mini to judge GPT-5.4 outputs may introduce family bias; consider
    using an independent judge model.
artifact_hash: f1ba0d06b47034bb9ae781a67854dde745b8b5c42ceeefcb523795f3179180a0
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T07:48:36.663193Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The manuscript presents OmniRetrieval with empirical results on a 13-dataset benchmark (Section 5.1). While the sample size of ~3,900 questions is substantial, the scientific evidence supporting the performance claims is weakened by critical methodological limitations regarding reproducibility and statistical rigor.

First, Section 5.3 ("Implementation Details") explicitly states: "We use a sampling temperature of 0.0... so all reported numbers come from a single run per configuration." For empirical ML research, single-run reporting is insufficient to establish the reliability of effect sizes. Table 1 presents precise accuracy differences (e.g., 68.58% vs 64.88% Source Selection for GPT-5.4), but without variance estimates (standard deviation, confidence intervals), these margins cannot be assessed for statistical significance. The gains could easily fall within the noise floor of the evaluation pipeline.

Second, the comparison against "Unified-Representation" baselines is acknowledged as "non-comparable" due to scale constraints (Section 5.2). While practical, this limits the evidence for the central claim that native-query approaches are superior to homogenization. A constrained benchmark (sub-sampled KBs) may not reflect the true difficulty of unified retrieval at scale, potentially inflating the perceived gap.

Third, the "LLM-as-a-Judge" metric (Section 5.3) relies on GPT-5.4-mini to evaluate GPT-5.4 outputs. This introduces a risk of model family bias, where the judge may favor outputs from its own lineage. This confounds the "Judge" accuracy metric in Table 1.

To salvage the scientific validity of the claims, the authors must provide variance estimates across multiple runs and clarify the independence of the evaluation metrics.
