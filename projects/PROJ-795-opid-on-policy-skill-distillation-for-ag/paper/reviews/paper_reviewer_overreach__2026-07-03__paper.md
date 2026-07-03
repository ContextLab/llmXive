---
action_items:
- id: 25d6fb6a314b
  severity: writing
  text: Abstract claims 'generalizes' broadly, but evidence is only ALFWorld 'unseen'
    split (Sec 3.4). Scope claim to 'unseen splits within same environment' or add
    cross-domain tests.
- id: 1a7129db7f5f
  severity: writing
  text: Conclusion states 'consistent improvements' but Table 1 shows OPID loses on
    specific tasks (e.g., ALFWorld Clean on 3B, NQ on 1.7B). Qualify 'consistent'
    to 'generally' and acknowledge variance.
- id: 664b22a179c1
  severity: writing
  text: Qualitative analysis (Fig 3) presents one success case as evidence for 'reduced
    invalid behaviors' without statistical backing. Clarify this is illustrative,
    not a quantitative proof of reduced hallucination.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T20:04:49.783183Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding the scope of its results that slightly exceed the demonstrated evidence, primarily in the areas of generalization and consistency.

First, the **Abstract** and **Introduction** assert that OPID improves "robustness" and "generalizes" to broader settings. The only evidence provided for generalization is the "ALFWorld Unseen" split (Section 3.4, Figure 4). While this is a valid test of distribution shift within a single environment, the paper does not demonstrate cross-domain generalization (e.g., training on ALFWorld and testing on WebShop) or robustness to entirely different task families. The claim of generalization should be scoped to "unseen splits within the same environment" or supported by cross-domain experiments.

Second, the **Conclusion** and **Main Results** (Section 3.2) describe the improvements as "consistent." While the *average* performance improves, Table 1 reveals specific instances where OPID underperforms the GRPO baseline. For example, on the Qwen2.5-3B model, OPID scores 88.9 on ALFWorld "Clean" compared to GRPO's 96.2. Similarly, on Qwen3-1.7B, OPID scores lower than GRPO on NQ (38.1 vs 40.0) and TriviaQA (58.1 vs 58.9). The narrative frames the method as uniformly superior, omitting these specific failure modes. A more accurate claim would acknowledge that improvements are "generally observed" or "on average," while noting that performance varies by task type and model size.

Finally, the **Qualitative Analysis** (Section 3.5) presents a single case study (Figure 3) where OPID succeeds and GRPO fails. While illustrative, presenting this as the primary evidence for "reduced invalid behaviors" without quantifying the frequency of such failures across the test set risks cherry-picking. The text should clarify that this is an *illustrative* example of the mechanism, not a statistical proof of reduced hallucination rates, unless such a metric is explicitly reported in the tables.

These are primarily rhetorical overreaches that can be fixed by tightening the language in the abstract and conclusion to match the specific boundaries of the experimental data.
