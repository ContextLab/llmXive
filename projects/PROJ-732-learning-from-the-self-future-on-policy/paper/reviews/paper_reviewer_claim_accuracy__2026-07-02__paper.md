---
action_items:
- id: 0e821beb9d9c
  severity: writing
  text: In Section 4.3, the claim that AR-style OPSD 'fails to bring new knowledge'
    relies on an 'Overlap Top-K' metric near 1.0. Explicitly state the theoretical
    baseline or random overlap value to contextualize why this metric implies a lack
    of new information transfer.
- id: 8dc0369f7492
  severity: writing
  text: Section 4.2 claims d-OPSD uses 'around 10%' of RLVR steps. Table 3 shows a
    range from ~5.5% (GSM8K) to ~11% (Sudoku). Refine the phrasing to '5-11%' or 'approximately
    10%' to accurately reflect the data variance across tasks.
- id: 029c9f5b865e
  severity: writing
  text: The claim of being the 'first OPSD framework for dLLMs' (Abstract, Sec 3.3)
    distinguishes d-OPSD from d3LLM and Cd4lm based on 'on-policy' vs 'off-policy'
    nature. Ensure the citations clearly support this specific distinction and that
    the definition of 'on-policy' excludes the cited methods' approaches.
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T04:39:47.066503Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the support provided by citations and data within the manuscript.

The paper makes several strong claims regarding the novelty and performance of the proposed d-OPSD framework. The claim that d-OPSD is the "first OPSD framework tailored for dLLMs" (Abstract, Section 3.3) is supported by a clear distinction from existing works like d3LLM and Cd4lm, which are characterized as off-policy or SFT-like. The citations provided (qian2026d3llm, liang2026cd4lm) appear to support this distinction in the text, though the reader must accept the authors' definition of "on-policy" in the diffusion context as the differentiating factor.

The performance claims in Section 4.2 and Table 3 state that d-OPSD requires "only around 10% of the optimization steps" compared to RLVR. The data in Table 3 supports a significant reduction, but the specific percentages vary by task (e.g., GSM8K: 425/7700 ≈ 5.5%; Sudoku: 425/3800 ≈ 11.2%). While "around 10%" is a reasonable summary, the phrasing could be slightly more precise to reflect the range observed in the data, ensuring the claim is not perceived as an exact average when the variance is notable.

In Section 4.3, the authors claim that the AR-style OPSD baseline "fails to bring new knowledge" based on an "Overlap Top-K" metric approaching 1.0. While the metric is defined, the claim of "failure" relies on the implicit assumption that an overlap of ~1.0 indicates no new information transfer. The text would benefit from explicitly stating the theoretical maximum overlap or a baseline (e.g., random chance) to contextualize why a value near 1.0 is detrimental, thereby strengthening the causal link between the metric and the claim of "no new knowledge."

Overall, the claims are generally well-supported by the provided tables and figures, but minor clarifications on the interpretation of specific metrics and the precision of summary statistics would enhance the accuracy and robustness of the assertions.
