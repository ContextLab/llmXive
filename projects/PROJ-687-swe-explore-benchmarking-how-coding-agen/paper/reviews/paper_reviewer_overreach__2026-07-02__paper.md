---
action_items:
- id: 7e47736beb3d
  severity: science
  text: The claim that 'agentic explorers form a clear tier above classical retrieval'
    overgeneralizes. Table 2 shows dense retriever 'Potion' fails like random, while
    only lexical baselines fail. The paper must clarify that the advantage is specific
    to agentic/interactive methods over lexical search, not all non-agentic methods.
- id: d503ab38191f
  severity: science
  text: The paper claims to 'isolate' exploration, yet ground truth is derived only
    from successful repair trajectories. This biases the benchmark toward solvable
    issues. The authors admit this in the abstract but then claim to measure general
    'repository understanding.' Claims should be narrowed to 'exploration for successful
    repair' to avoid overreach.
- id: cdacc7b4598d
  severity: writing
  text: The statement that high correlation (r=0.950) is 'expected' because metrics
    measure the 'same underlying capability' is an over-interpretation. The correlation
    is specific to the fixed downstream agent (Mini-SWE-Agent) and budget. The paper
    should clarify that metrics predict repair only within this specific protocol,
    not universally.
artifact_hash: d01bf725e90093797f2151085112b0bd34f0dac442648b3b22aae07b0ee791b3
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:44:40.803275Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the immediate evidence provided by the benchmark design and experimental results, specifically regarding the generalizability of the "agentic" advantage and the independence of the exploration metric from the repair outcome.

First, the abstract and introduction assert that "agentic explorers form a clear tier above classical retrieval." While Table 2 confirms that agentic agents (e.g., AweAgent, LocAgent) significantly outperform lexical baselines (BM25, TF-IDF), the paper groups "classical retrieval" broadly. However, the dense retriever "Potion" (a non-agentic method) performs almost indistinguishably from the Random baseline (Rec_l 0.025 vs 0.004). By grouping Potion with the successful agentic tier or failing to explicitly distinguish the failure of *dense* retrieval from *lexical* retrieval, the paper overstates the necessity of "agentic" behavior. The data supports that *interactive* or *reasoning-based* agents are superior to *lexical* search, but not necessarily that all non-agentic methods (like dense retrieval) are ineffective. This distinction is crucial for the field's direction.

Second, the paper claims to "isolate repository exploration" from patch generation. However, the ground truth is constructed entirely from trajectories of agents that *successfully solved* the issue. This introduces a fundamental selection bias: the benchmark only measures exploration for problems that are solvable by current strong models. It cannot evaluate exploration for unsolvable issues or issues where the agent fails due to poor exploration but the code is actually present. The authors acknowledge this in the "Selection Bias Limitation" in the abstract but then proceed to claim the benchmark evaluates "repository understanding" and "bug diagnosis" in a general sense. The scope of these claims should be restricted to "exploration for successful repair" to avoid overclaiming the benchmark's ability to diagnose general agent capabilities on the full spectrum of software issues.

Finally, the interpretation of the high correlation (r=0.950) between exploration metrics and downstream repair rates (Table 3) is slightly overreached. The authors state, "This high correlation is expected: exploration metrics and downstream repair behavior both measure the same underlying capability." This phrasing suggests a tautological relationship or a universal truth. However, the downstream validation uses a *specific* fixed agent (Mini-SWE-Agent) and a *specific* context budget. The high correlation likely reflects the sensitivity of *that specific agent* to the provided context, rather than a universal property of exploration metrics. The paper should clarify that the metrics are predictive of repair *for the specific downstream protocol used*, rather than implying they measure a universal "repair capability" independent of the downstream agent's architecture.
