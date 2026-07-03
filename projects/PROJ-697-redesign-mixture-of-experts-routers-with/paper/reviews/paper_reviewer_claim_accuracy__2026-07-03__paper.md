---
action_items:
- id: 5ba32625d534
  severity: writing
  text: In Section 1 (Introduction), the claim that the method 'provides a theoretical
    analysis yielding tighter bounds on expert utilization' is unsupported. The paper
    derives an optimization interpretation (Eq. 10) and convergence intuition but
    presents no formal bounds on utilization metrics (e.g., load variance or collision
    rates) compared to baselines. This overstates the theoretical contribution.
- id: a3d4f474b86c
  severity: writing
  text: In Section 3.2 (Eq. 10) and Appendix A, the derivation claims the update rule
    is an 'approximation' of steepest ascent. However, the text asserts 'striking
    structural alignment' and 'equivalence' without quantifying the error term or
    proving the approximation holds under the specific non-stationary conditions of
    online training. The claim of equivalence is too strong given the lack of error
    bounds.
- id: ec38750f5307
  severity: writing
  text: In Section 4.1, the claim that the method is 'agnostic to shifts in model
    features across optimizers' is based on 1B parameter experiments. Extrapolating
    this to claim fundamental agnosticism for 11B+ models without explicit theoretical
    justification or larger-scale ablation is an overgeneralization of the evidence
    provided.
- id: ce0407856e2b
  severity: writing
  text: "In Section 4.2, the claim that the 0.2% slowdown is 'negligible' and 'does\
    \ not exceed that of N extra tokens' lacks a rigorous breakdown. The power iteration\
    \ involves matrix-matrix multiplications ($R \times W \times W^T$) which are computationally\
    \ heavier than simple token additions. The specific arithmetic justification for\
    \ this claim is missing from the text."
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:59:29.955055Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several strong claims regarding theoretical guarantees and empirical generalization that are not fully supported by the provided evidence or derivations.

First, the Introduction explicitly lists "providing a theoretical analysis yielding tighter bounds on expert utilization" as a main contribution. However, the "Methodology" and "Method Analysis" sections focus on deriving an optimization interpretation (Eq. 10) and demonstrating empirical alignment (Table 1). There are no formal mathematical bounds presented that quantify expert utilization (e.g., variance in expert load or collision probability) relative to standard routers. The claim of "tighter bounds" is therefore unsupported by the text.

Second, the theoretical derivation in Section 3.2 (Eq. 10) and Appendix A asserts that the proposed update rule is an "approximation" of steepest ascent on the manifold. While the structural similarity is noted, the paper claims a "striking structural alignment" and implies equivalence without deriving the error term of the approximation or proving that the approximation error vanishes under the non-stationary dynamics of online training. The claim that the method is "equivalent to a steepest ascent optimization" (Introduction) is too strong given the lack of a rigorous error analysis.

Third, the claim in Section 4.1 that the design is "agnostic to shifts in model features across optimizers" is based solely on 1B parameter experiments. While the results are promising at this scale, asserting fundamental agnosticism for larger scales (11B+) without theoretical justification or larger-scale ablation studies constitutes an overgeneralization of the empirical evidence.

Finally, the efficiency claim in Section 4.2 states the overhead is "negligible" and "does not exceed that of N extra tokens." The power iteration step involves computing $R \times W \times W^T$, which is a matrix-matrix operation significantly more expensive than the vector-matrix operations in standard routing. The text lacks a specific arithmetic breakdown or complexity analysis to substantiate the claim that this cost is equivalent to adding $N$ tokens, making the "negligible" assertion difficult to verify.
