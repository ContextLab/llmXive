---
action_items:
- id: bac7e03ebf07
  severity: writing
  text: The manuscript makes several claims that extend beyond the evidence provided
    in the text, particularly regarding the nature of the retrieval algorithm and
    the comparative benefits of the system. First, the Abstract and Conclusion repeatedly
    describe the retrieval pipeline as achieving "deterministic association discovery."
    This is a significant overreach. The core algorithm employed is Random Walk with
    Restart (RWR), which is inherently a stochastic process. While the implementation
    yields repro
artifact_hash: f3ce028cf68a2eb124d9418ea236e7f52f710c30a6edb26c69bffcf6c534c941
artifact_path: projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T07:05:33.458574Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript makes several claims that extend beyond the evidence provided in the text, particularly regarding the nature of the retrieval algorithm and the comparative benefits of the system.

First, the Abstract and Conclusion repeatedly describe the retrieval pipeline as achieving "deterministic association discovery." This is a significant overreach. The core algorithm employed is Random Walk with Restart (RWR), which is inherently a stochastic process. While the implementation yields reproducible results for fixed inputs, characterizing the discovery mechanism as "deterministic" misrepresents the probabilistic nature of graph diffusion and suggests a level of logical certainty that the method does not possess. This phrasing should be corrected to "probabilistic topological reasoning" or "stochastic association discovery" to maintain scientific accuracy.

Second, the paper asserts that SciAtlas "reduces reasoning costs" (Abstract, Conclusion) compared to existing agentic frameworks. However, the manuscript provides no empirical data to support this. While a runtime of "≈2 minutes" is mentioned, there is no baseline comparison against standard vector retrieval or multi-hop agentic search in terms of token consumption, API latency, or computational overhead. Without a controlled experiment or at least a theoretical breakdown of cost savings, this claim remains an unsupported extrapolation.

Third, the Limitations section makes the absolute claim that "KG is indispensable for scientific discovery." This is a philosophical stance rather than a conclusion drawn from the paper's data. The authors demonstrate that their KG is *useful*, but they have not conducted a study proving that non-KG approaches are fundamentally incapable of scientific discovery. This absolute language should be tempered to reflect the paper's actual contribution, such as "KGs provide a structured substrate that enhances..."

Finally, the claim that the system "dismantles disciplinary barriers" (Abstract, Introduction) is contradicted by the provided statistics. The graph is heavily dominated by Medicine (18.56%) and Social Sciences (10.70%), while Computer Science represents only 6.29% of the corpus. This distribution suggests the system may currently reflect existing publication biases rather than effectively dismantling them. The claim should be qualified to acknowledge the current data distribution or removed until a more balanced corpus is demonstrated.
