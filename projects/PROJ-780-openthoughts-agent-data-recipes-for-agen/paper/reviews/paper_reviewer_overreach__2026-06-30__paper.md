---
action_items:
- id: 6dfa5d483b1b
  severity: writing
  text: The paper frequently extrapolates beyond the strict bounds of its empirical
    evidence, particularly regarding scaling claims and model dominance. First, the
    Abstract and Introduction assert that the dataset "beats alternatives at every
    size." This is factually unsupported by the provided data. The footnote to Figure
    1 explicitly notes that the SERA dataset "contains at most 47 K examples, so its
    scaling curve stops at 47 K." Consequently, the claim of beating alternatives
    "at every size" is impos
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T18:22:28.967257Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper frequently extrapolates beyond the strict bounds of its empirical evidence, particularly regarding scaling claims and model dominance.

First, the Abstract and Introduction assert that the dataset "beats alternatives at every size." This is factually unsupported by the provided data. The footnote to Figure 1 explicitly notes that the SERA dataset "contains at most 47 K examples, so its scaling curve stops at 47 K." Consequently, the claim of beating alternatives "at every size" is impossible to verify for the 47K–100K range. The authors must qualify this claim to state that the model outperforms alternatives *within the overlapping evaluation range* or *up to the maximum size of competing datasets*.

Second, the Conclusion claims the resulting model is the "strongest open-data ≤32B agentic model." While the average score (44.8%) is the highest, the breakdown in Table 1 reveals significant weaknesses in specific out-of-distribution (OOD) benchmarks. Specifically, the model scores 47.8% on MedAgentBench, significantly trailing the Nemotron-Terminal-32B baseline at 62.6%. Claiming "strongest" status based on an average that masks a ~15pp deficit in a major benchmark category is an over-interpretation of the results. The claim should be restricted to "highest average performance" or "strongest on core software engineering benchmarks."

Third, the Introduction lists "Instruction choice is a dominant factor" as a key finding, citing a ~30pp difference. While the range from the best to the worst strategy is indeed large, the data in Table 1 (Task Generation Strategies) shows that the top 5 strategies are relatively close to each other (e.g., 32.33% vs 24.00%), while the drop-off occurs at the very bottom of the 95 strategies. Framing this as a "dominant factor" for the *optimal* pipeline design is slightly misleading; the data suggests that *avoiding poor strategies* is critical, but the choice among the top-tier strategies yields diminishing returns (as seen in the mixing ablation). The text should be refined to reflect that "avoiding low-quality task sources is critical" rather than implying a high-sensitivity optimization problem for the top choices.

Finally, the claim that "Filtering for longer execution traces improves downstream performance" (Introduction) is supported by Table 2, but the magnitude is overstated in the narrative. The table shows a +3pp gain on average, which is statistically significant but not transformative in the context of the 30pp swings seen in task sourcing. The narrative should avoid equating the impact of filtering with the impact of task sourcing.
