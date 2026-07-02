---
action_items:
- id: afba73cc9f4a
  severity: writing
  text: The claim that APPO improves performance by 'nearly 4 points' (Abstract) and
    'approximately 3 points' (Contributions) is inconsistent with Table 1, which shows
    a 2.1 point gain on Qwen2.5-7B and a 2.45 point gain on Llama3.1-8B. The 'nearly
    4 points' figure appears to conflate the 7.9% relative improvement on Llama3.1-8B
    with absolute points, or refers to a specific subset not clearly defined. This
    overstates the generalizable absolute gain.
- id: e60a886ca7ba
  severity: science
  text: Theorem 1 claims variance reduction based on the assumption that conditional
    reward variance is monotone in the Branching Score (BS). The paper provides no
    empirical evidence or theoretical justification for this monotonicity assumption
    in the context of LLM reasoning. Without validating this assumption, the theorem's
    applicability to the proposed method is speculative and overreaches the provided
    data.
- id: f10e60b21ed4
  severity: writing
  text: The abstract states APPO 'consistently improves strong agentic RL baselines
    by nearly 4 points,' yet Table 2 shows APPO improving over ARPO by only 3.0 points
    on GAIA (42.7 vs 39.7 implied, though ARPO is 38.8) and 1.4 points on HLE. The
    'nearly 4 points' claim is an overgeneralization that does not hold across all
    reported benchmarks, particularly the DeepSearch tasks where gains are smaller.
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:34:46.320181Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding the magnitude of performance improvements and the theoretical guarantees of the proposed method that exceed the support provided by the experimental data and theoretical derivations.

First, the Abstract and Contributions section repeatedly claim that APPO improves baselines by "nearly 4 points" or "approximately 3 points." However, a close inspection of Table 1 reveals that the absolute improvements over the strongest agentic baseline (ARPO) are 2.1 points for Qwen2.5-7B and 2.45 points for Llama3.1-8B. The "nearly 4 points" figure likely stems from misinterpreting the relative percentage gain (7.9%) on the Llama3.1-8B backbone as an absolute point gain, or by cherry-picking specific datasets where the gain is higher. This inconsistency constitutes an over-claim regarding the general magnitude of the improvement. Similarly, in Table 2, the gains on DeepSearch tasks are often smaller (e.g., ~1.4 points on HLE), further contradicting the blanket "nearly 4 points" assertion.

Second, Theorem 1 (Variance Reduction) relies on the critical assumption that the conditional reward variance of a decision point is monotone in its Branching Score (BS). The paper asserts this relationship to justify the variance reduction but provides no empirical validation or theoretical proof that this monotonicity holds for the complex, non-stationary reward landscapes of agentic RL tasks. Without establishing this assumption, the theorem's conclusion that APPO strictly reduces variance compared to random branching is not fully supported by the presented evidence. The proof in Appendix A assumes this property rather than deriving it from the properties of the BS metric itself.

Finally, the claim that the method "maintains behavior interpretability" (Abstract) is asserted without quantitative or qualitative metrics defining or measuring interpretability, relying instead on the qualitative word cloud in Figure 4 which shows token selection but does not directly measure the interpretability of the resulting agent behavior.
