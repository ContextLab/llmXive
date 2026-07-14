---
action_items:
- id: 9e9371e61c1f
  severity: writing
  text: Section 2 claims VP uses 'only 25% of the token budget' compared to TP. However,
    Section 4 clarifies total CPT budgets are 180B (TP) vs 120B (VP). The 25% figure
    applies only to the scientific-PDF subset (20B vs 80B), not the total budget.
    The Results phrasing misleadingly implies a total budget reduction. Clarify that
    the efficiency gain applies specifically to the PDF corpus representation, not
    the aggregate token count.
- id: 8236a62a5d79
  severity: writing
  text: Section 2 states VP trains on 20B visual tokens vs TP's 80B text tokens to
    support efficiency. But Section 4 shows total CPT budgets are 120B (VP) vs 180B
    (TP). The argument conflates subset efficiency with total training scale, implying
    a 75% cost reduction when it was only ~33%. Distinguish between the efficiency
    of the PDF representation and the total training budget to avoid logical overreach.
artifact_hash: 819c8b5fd062f0531cdf830c89d642bcd4d25ad03c275f7103c9aac8218dec1b
artifact_path: projects/PROJ-1048-scalable-visual-pretraining-for-language/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T02:57:12.293751Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent argument that visual pretraining (VP) on raw scientific documents improves reasoning compared to text-only pretraining (TP) on extracted text, supported by a matched-corpus experimental design. The logical flow from the problem (information loss in text extraction) to the solution (VP) and evidence (benchmark gains) is generally sound.

However, there is a logical inconsistency regarding the "efficiency" claim in the Results section versus the Methods section. In Section 2, the authors state: "VP surpasses TP while consuming only 25% of the token budget." This phrasing implies the *total* training token budget for VP was 25% of TP. Yet, Section 4 ("Training setup") clarifies that total CPT budgets were 180B tokens for TP and 120B for VP. The 25% figure (20B visual vs 80B text) applies *only* to the scientific-PDF subset, not the entire corpus.

This creates a gap where the conclusion in Section 2 (total budget efficiency) does not strictly follow from the premises in Section 4 (subset efficiency). The argument overgeneralizes the efficiency gain to the total training cost, which is not supported by the numbers. The text must clarify that the 25% figure refers specifically to the scientific-PDF representation efficiency, not the aggregate training budget, to ensure the conclusion logically follows from the stated premises.
