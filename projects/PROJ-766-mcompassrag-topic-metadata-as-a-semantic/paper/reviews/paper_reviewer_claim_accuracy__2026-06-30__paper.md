---
action_items:
- id: 93edfb9eb2b4
  severity: writing
  text: Section 5.1 lists LongBenchV2 as a benchmark but states it is used only for
    downstream evaluation due to lack of retrieval labels. The initial listing implies
    it is a retrieval benchmark, which is factually inaccurate.
- id: 80215b60f3c6
  severity: writing
  text: The abstract claims "over 5x lower latency" than strongest efficient baselines.
    Table 2 shows MCompassRAG (174ms) is only ~4.1x faster than REFRAG (720ms), not
    5x. The claim is overstated for the full set of baselines.
- id: e1469ee21a38
  severity: writing
  text: Section 5.2 claims MCompassRAG "outperforms all baselines." Table 1 shows
    "LLM + 10 Topics" (oracle) outperforms MCompassRAG on DRBench (50.27 vs 47.97).
    The claim is false unless "non-oracle" is specified.
- id: eef92e7731fb
  severity: writing
  text: "Section 5.2 states the gap to the oracle is \"within 2\u20133 points\" on\
    \ remaining benchmarks. For Dragonball and LegalBench, the gaps are ~1.8 points,\
    \ which is under 2. The range \"2\u20133\" is inaccurate; \"under 2\" is correct."
artifact_hash: 5e7163c1713464843d620f2c37705ca96ededa7c235cfa3e5a0986f0a19b0aa7
artifact_path: projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T15:11:34.750554Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper contains several factual inaccuracies regarding performance metrics and benchmark definitions that require correction.

First, in Section 5.1, the text lists seven benchmarks including LongBenchV2, then immediately clarifies it is used "only for downstream evaluation" because it lacks retrieval labels. The initial phrasing implies it is a retrieval benchmark, which contradicts the subsequent clarification. This should be rephrased to explicitly exclude it from the retrieval evaluation set in the primary list.

Second, the Abstract and Introduction claim "over 5x lower latency" compared to the strongest efficient baselines. Table 2 shows MCompassRAG has 174ms latency, while REFRAG (a strong efficient baseline) has 720ms. The ratio is approximately 4.1x, not 5x. The 5x figure only holds against SAKI-RAG (925ms). The claim is factually incorrect for the aggregate of "strongest efficient baselines" and should be qualified (e.g., "up to 5x" or "over 4x").

Third, Section 5.2 asserts that MCompassRAG "consistently outperforms all baselines across every benchmark and metric." However, Table 1 shows that the "LLM + 10 Topics" oracle baseline achieves a higher Information Efficiency (IE) on DRBench (50.27) than MCompassRAG (47.97). While the text later distinguishes the oracle, the absolute claim of outperforming "all baselines" is false. The statement must be restricted to "non-oracle baselines."

Finally, Section 5.2 claims the performance gap to the oracle is "within 2–3 points" on the remaining benchmarks. For Dragonball, the gap is 1.77 points, and for LegalBench-RAG, it is 1.80 points. These values are strictly less than 2, making the "2–3 points" range inaccurate. The text should state the gap is "under 2 points" for these datasets.
