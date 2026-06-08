---
action_items:
- id: 3844287e820f
  severity: science
  text: The claim that unified-representation methods have a 'fundamental limit' is
    based on a constrained baseline that is not comparable to full-scale unified methods.
    The paper acknowledges this setup is 'non-comparable' (Table 2) yet draws general
    conclusions. Either remove this claim or provide a fair comparison.
- id: 77a36298681a
  severity: science
  text: The 'Retrieval Accuracy' metric macro-averages NDCG@10 (ranking quality, continuous)
    with Execution Match (binary correctness). These measure fundamentally different
    aspects of retrieval. The paper should clarify this distinction or use separate
    metrics for each paradigm.
- id: 5d34e256a3fd
  severity: writing
  text: The claim that evidence selection 'recovers' semantically equivalent answers
    from alternative KBs relies on the LLM-as-a-Judge accepting alternative KBs as
    correct. This is a design choice for the judge metric, not a general retrieval
    property. Clarify this distinction to avoid conflating metric definition with
    task objective.
artifact_hash: f1ba0d06b47034bb9ae781a67854dde745b8b5c42ceeefcb523795f3179180a0
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T07:44:16.582602Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: full_revision
---

The paper's core logical argument—that keeping sources on their own terms with a unifying access layer is superior to collapsing them into a shared representation—is internally consistent. The problem formulation (Section 2) establishes the premises clearly, and the method (Section 4) follows logically from those premises.

However, several logical gaps weaken the evidentiary support for key conclusions:

1. **Unsupported causal claim about unified methods**: The paper concludes that "atomic-unit retrieval cannot capture the structural composition" of native queries (Section 6, Analysis on Native vs Unified Retrieval). This conclusion is drawn from a constrained baseline that sub-samples the knowledge bases to a scale where unified methods can index them. The paper acknowledges this setup is "non-comparable" (Table 2 footnote) yet still draws general conclusions about "fundamental limits." This is a logical leap: the constrained setup does not faithfully represent full-scale unified methods, so the causal claim is not well-supported. Either remove this conclusion or provide a fair comparison that matches the scale of the native method benchmark.

2. **Metric mixing in Retrieval Accuracy**: The paper macro-averages NDCG@10 (for document search) with Execution Match (for structured backends). While both are normalized to [0,1], they measure different properties: NDCG@10 is a ranking quality metric sensitive to result order, while Execution Match is a binary correctness metric. The claim that "Retrieval Accuracy" is a unified measure across paradigms is weakened by this conflation. The paper should either use separate metrics per paradigm or justify why these can be meaningfully averaged.

3. **Evidence selection recovery claim**: The paper claims evidence selection "recovers" semantically equivalent answers even when source selection misses (Section 6, Main Results). This relies on the LLM-as-a-Judge metric accepting "faithful implementation on a different KB" as correct. While internally consistent with the metric definition, this conflates a design choice for the judge with a general retrieval property. The task objective (retrieve from the correct KB) differs from the judge's tolerance for alternative KBs. Clarify this distinction to avoid misleading claims about retrieval task performance.

The top-k analysis (Section 6, Analysis on Source Candidate Size) is logically sound despite the apparent contradiction that source selection accuracy drops as k increases while overall retrieval accuracy improves. The paper correctly explains this via gold inclusion rate vs. top-1 accuracy, and the evidence selection step compensates for lower top-1 accuracy. This is a strength of the argument.

Overall, the paper's logical structure is coherent, but the unsupported claims about unified methods and the metric conflation require revision before the conclusions can be fully accepted.
