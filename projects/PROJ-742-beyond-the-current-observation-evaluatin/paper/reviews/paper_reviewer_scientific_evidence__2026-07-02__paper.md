---
action_items:
- id: 655732d0dbab
  severity: science
  text: The 'Duel Protocol' results (Tab. 2) claim Gemini-3.1-Pro won all 16 matchups
    against GPT-5.4 and Qwen3.5-397B. However, the table lists GPT-5.4 with 7 wins
    and 7 losses (50% win rate) and Qwen3.5-397B with 7 wins and 8 losses. This is
    a direct contradiction between the narrative text and the data table that must
    be resolved to validate the claim of total dominance.
- id: f9299053460f
  severity: science
  text: The Memory Gap metric (Eq. 2) relies on an oracle score $S^*(m)$. The paper
    states the oracle injects 'true hidden state,' but does not specify if the oracle
    is a perfect solver (100% success) or a model with perfect memory but limited
    reasoning. If the oracle is not perfect, the denominator $S^*(m)$ is ambiguous,
    making the 'gap' a measure of both memory and reasoning deficits rather than pure
    forgetting.
- id: 3a58edf2648f
  severity: science
  text: The fine-tuning study (Sec. 5, Tab. 4) reports a single run for Qwen3.5-9B
    with 'rmix32k' data. No standard deviation or confidence intervals are provided
    for the 29.5% score or the 10.0% success rate. Given the stochastic nature of
    RLHF/SFT and the small sample size of the evaluation (implied by the integer success
    counts in other tables), the statistical significance of the transfer claim is
    unverified.
artifact_hash: 2dace62b4db749210548d655003e141d33d2469d6916df6eba8fda5f05abc5c8
artifact_path: projects/PROJ-742-beyond-the-current-observation-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:46:09.089010Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel benchmark for non-Markov games, but the scientific evidence supporting the central claims requires clarification on statistical rigor and data consistency.

First, there is a critical contradiction in the **Duel Protocol** results. The narrative in Section 4.1 states, "Gemini-3.1-Pro wins all 16 matchups." However, Table 2 explicitly lists GPT-5.4 with 7 wins and 7 losses (50% win rate) and Qwen3.5-397B with 7 wins and 8 losses. If Gemini won *all* 16, the opponents should have 0 wins. This discrepancy undermines the claim of total dominance and suggests a potential error in either the data aggregation or the textual summary.

Second, the **Memory Gap** metric (Eq. 2) is central to the claim that "most errors are due to forgetting." The metric is defined as $1 - S(m)/S^*(m)$. The paper describes $S^*(m)$ as the score with "oracle hidden state injected." It is unclear if this oracle is a perfect solver (achieving 100% score) or a model with perfect memory but the same reasoning limitations as the baseline. If the oracle is not a perfect solver, $S^*(m) < 100\%$, and the "gap" conflates memory failure with reasoning failure. Without defining the oracle's upper bound, the attribution of errors solely to "forgetting" is not fully supported.

Third, the **fine-tuning results** (Section 5, Table 4) lack statistical robustness. The improvement from 0.0% to 29.5% on Matching Pairs and 0.0% to 10.0% on 3D Maze is reported for a single training run. The paper mentions evaluation aggregates over 5 environment seeds, but it does not report the variance or standard deviation of the fine-tuned model's performance across these seeds. Given the high variance often seen in LLM evaluation, a single point estimate is insufficient to claim a robust transfer of capability.

Finally, the **sample sizes** for the 3D Maze success rates are extremely low (e.g., "1/5", "2/5" in Appendix tables). While the paper acknowledges this in the "Limitations" section, the main text presents these low-probability events as definitive performance metrics (e.g., "0.0% SR"). The evidence for the "bottleneck" being visual recognition (Section 4.2) is strong, but the evidence for the specific efficacy of the fine-tuning strategy is weak due to the lack of error bars and the small number of successful episodes.
