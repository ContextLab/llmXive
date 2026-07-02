---
action_items:
- id: 4e1b7de42463
  severity: writing
  text: The paper makes several strong claims regarding the superiority and practicality
    of Direct Corpus Interaction (DCI) that slightly overreach the presented evidence,
    particularly regarding the trade-offs between latency, surface-form robustness,
    and the definition of "indexing." First, the narrative in Section 3.2 ("Main Findings")
    claims the method "outperforms all baselines on 4/7 datasets" and frames the performance
    on PopQA as a "minor degradation." However, Table 1 explicitly marks the PopQA
artifact_hash: 5d85c06c69d8e12a9cf2281b0d8f94964a15c102cc7625c442c21ea4362e7831
artifact_path: projects/PROJ-651-grepseek-training-search-agents-for-dire/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:07:59.448543Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the superiority and practicality of Direct Corpus Interaction (DCI) that slightly overreach the presented evidence, particularly regarding the trade-offs between latency, surface-form robustness, and the definition of "indexing."

First, the narrative in Section 3.2 ("Main Findings") claims the method "outperforms all baselines on 4/7 datasets" and frames the performance on PopQA as a "minor degradation." However, Table 1 explicitly marks the PopQA result (0.4861) with a down-arrow ($\downarrow$), indicating a statistically significant drop compared to Search-R1 (0.5101). Given that the paper's core argument relies on the agent's ability to handle complex retrieval, a significant failure on a standard benchmark due to diacritic sensitivity (as admitted in the text) suggests the method is not a universal replacement for dense retrieval. The conclusion should more honestly frame this as a trade-off: superior precision on exact matches at the cost of robustness to surface variations, rather than a general "outperformance."

Second, the efficiency claim of "zero offline indexing time" (Section 3.2) is technically accurate regarding the *retrieval index* but misleading in the broader context of the system's cost. The "Cold-Start Data Generation" phase (Section 2.1) involves a computationally expensive process: using a 27B Tutor model and a Planner to generate 10,000 verified trajectories. This pre-computation is a form of heavy lifting that replaces the traditional index build. While the authors correctly note they avoid building a vector database, characterizing the entire pipeline as having "zero offline" costs ignores the substantial compute required to synthesize the training data. The claim should be refined to "zero offline *retrieval* indexing" to avoid implying the method is computationally free to deploy.

Finally, the conclusion asserts the method is a "practical alternative" (Section 5). While the memory savings (14GB vs 221GB) are impressive, the latency is significantly higher (8.67s vs 4.77s for E5). For many real-time search applications, a near-doubling of latency is a critical barrier. The paper overreaches by presenting the method as broadly practical without explicitly qualifying that its practicality is contingent on specific constraints (e.g., memory-limited environments or scenarios where exact string matching is paramount over speed). The discussion should more clearly delineate the specific use-cases where this latency penalty is acceptable.
