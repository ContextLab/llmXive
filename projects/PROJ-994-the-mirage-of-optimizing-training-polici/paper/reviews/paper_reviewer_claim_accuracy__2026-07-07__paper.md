---
action_items:
- id: c91787432368
  severity: writing
  text: 'The paper makes several strong claims regarding the theoretical guarantees
    and empirical metrics that are not fully supported by the provided text or tables.
    First, the Abstract and Introduction repeatedly assert that the proposed method
    ensures "monotonic" improvement of the inference policy. However, Section 3.2
    ("Step 2: Inference-Gap-Aware Update Acceptance") explicitly contradicts this
    by stating: "This mechanism does not provide a formal monotonic-improvement guarantee,
    but it reduces the'
artifact_hash: 532a85457b6c71e1e8174b90594afc6d1be5ab1b35a438039d06e81d212f0a7d
artifact_path: projects/PROJ-994-the-mirage-of-optimizing-training-polici/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:25:25.816424Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the theoretical guarantees and empirical metrics that are not fully supported by the provided text or tables.

First, the Abstract and Introduction repeatedly assert that the proposed method ensures "monotonic" improvement of the inference policy. However, Section 3.2 ("Step 2: Inference-Gap-Aware Update Acceptance") explicitly contradicts this by stating: "This mechanism does not provide a formal monotonic-improvement guarantee, but it reduces the risk of accumulating updates..." This is a significant definitional drift where the term "monotonic" is used in the headline claims to imply a guarantee that the authors themselves admit does not exist. The claims in the Abstract and Introduction must be softened to reflect that the method *aims* for monotonicity or *reduces the risk* of non-monotonicity, rather than ensuring it.

Second, the derivation of the post-update gap proxy $\widehat{T}_{\mathrm{post}}$ in Section 3.2 relies on a "reverse identity" to approximate an expectation under the training policy using samples from the inference policy. The text claims this yields a "stable proxy" but does not cite the specific identity used nor provide any theoretical bound on the variance or bias introduced by the importance weighting $\rho_i$. Without this support, the claim of stability is an overstatement of the evidence provided.

Third, there is a direct contradiction regarding the evaluation metric in Table 1. The table caption explicitly states "Pass@1 accuracy (%)", yet Section 4.1 ("Evaluation") states: "For the small benchmarks AIME24 and AMC23, we use avg@16 to reduce evaluation variance." The table does not indicate which metric is reported for these specific columns. If the table reports Pass@1, the text is misleading; if it reports avg@16, the caption is incorrect. This ambiguity prevents the reader from accurately interpreting the reported gains.

Finally, the specific dataset sizes used for training (5,759 and 1,491 examples) are presented as filtered subsets of larger public datasets (DAPO-Math-17k and DeepMath-103k). The paper claims these subsets were chosen to ensure "meaningful reward variation," but the specific filtering criteria (e.g., success rate thresholds, difficulty filters) are not described. This omission makes the claim that the training set is optimally constructed for the experiment unsupported.
