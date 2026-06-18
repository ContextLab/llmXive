---
action_items:
- id: 1a96c36ff586
  severity: science
  text: "Clarify the relationship between total model parameters (12\u202FB), expert\
    \ size, and the stated 2.5\u202FB active parameters per token. The current numbers\
    \ (64 experts, 8 active) imply a different active\u2011parameter count."
- id: 588315e48df0
  severity: science
  text: "Resolve the contradictory statements about safety performance: the 'Overall\
    \ profile' claims the model is competitive on safety benchmarks, yet the safety\
    \ results show a regression after RL (HarmBench rises from 8.4\u202F% to 23.1\u202F\
    %). Align the narrative with the data."
- id: e6276f4b7de3
  severity: writing
  text: "Ensure that all performance claims are supported by the presented tables.\
    \ For example, the claim that the model 'matches or exceeds 4\u20137\u202FB dense\
    \ baselines on safety' is not reflected in the safety scores shown."
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:35:56.168317Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a detailed description of Mellum 2, a 12 B‑parameter Mixture‑of‑Experts (MoE) model with a long‑context extension and post‑training pipelines. While most sections are internally coherent, several logical inconsistencies undermine the credibility of the conclusions.

1. **Parameter Count vs. Active‑Parameter Claim (Section 2)**  
   The paper states that the model has 12 B total parameters, arranged as 64 experts with 8 active per token, yielding “2.5 B active parameters per token.” Simple arithmetic (12 B ÷ 64 ≈ 0.1875 B per expert; 0.1875 B × 8 ≈ 1.5 B) does not reconcile with the 2.5 B figure. If additional dense layers are intended to bridge the gap, this must be explicitly quantified; otherwise the claim is contradictory.

2. **Safety Benchmark Narrative (Section 7 & Conclusion)**  
   The “Overall profile” paragraph asserts that Mellum 2 is “competitive … on safety benchmarks,” yet the detailed safety results (Table \ref{tab:posttrain-eval-instruct} and Table \ref{tab:posttrain-eval-thinking}) show a clear degradation after reinforcement learning (HarmBench error rate rises from 8.4 % to 23.1 %). Moreover, the concluding statement that the model is “competitive … on safety” conflicts with these numbers. The narrative should either acknowledge the regression and discuss mitigation strategies or adjust the claim to reflect the actual performance.

3. **Performance Claims vs. Reported Data**  
   The abstract and conclusion claim “matching or exceeding 4–7 B dense baselines on safety.” The provided safety scores, however, place Mellum 2 behind several baselines (e.g., Qwen3.5‑9B’s 20.9 % vs. Mellum 2‑RL‑Instruct’s 23.1 %). This mismatch suggests an overstatement that is not logically supported by the evidence.

4. **Consistency of Ablation Results**  
   The long‑context ablation (Figure \ref{fig:long-context-ablation}) reports RULER scores of 0.64, 0.52, and 0.33 for three recipes. The text correctly interprets the ranking, but the “gap widens” claim would benefit from a quantitative statement (e.g., “a 23 pp advantage over the uniform bump at 64 K”). Minor phrasing improvements would tighten the logical flow.

5. **Training Token Counts**  
   The pre‑training token count is cited as “∼10.65 T tokens,” yet the long‑context extension mentions “∼117 B tokens” and later “3 500 iterations (∼117 B tokens)”. The relationship between these stages (pre‑training vs. extension) is not explicitly linked, leaving the reader uncertain whether the total token budget is additive or overlapping.

Overall, the paper’s methodology and experimental design are sound, but the above logical gaps need resolution before the work can be accepted. Addressing the parameter arithmetic, aligning safety claims with the data, and clarifying token‑budget accounting will substantially improve the logical consistency of the manuscript.
