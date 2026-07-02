---
action_items:
- id: 1b348b1a858b
  severity: science
  text: The claim of "verbatim source evidence" for 9.4M edges is over-claimed given
    the 70.4% Phase-1 extraction accuracy (Appendix). A 30% error rate invalidates
    the "causal" certainty implied in the Abstract.
- id: de28396e2485
  severity: science
  text: The Idea Generation evaluation (Sec 4.3) over-attributes win-rate gains to
    the graph. The LLM generates the text; the graph only identifies gaps. The study
    fails to isolate the graph's contribution from the LLM's parametric knowledge.
- id: 1a887d5fc8f0
  severity: writing
  text: The Conclusion claims "faithful" recovery of expert chains, yet Table 1 shows
    ~15-20% Node/Edge Recall loss. Describing this as faithful without quantifying
    the error rate in the main text is an over-interpretation.
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:10:59.472974Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper significantly over-claims the reliability and causal certainty of its core artifact, the Intern-Atlas graph. The Abstract and Introduction repeatedly assert that the graph is "grounded in verbatim source evidence" and forms a "queryable causal network." However, Appendix A.3 reveals that the edge typing accuracy for the production model is only 70.4%, with the audit model reaching 93.0%. Given that the graph contains 9.4 million edges, a 30% error rate in the primary extraction phase means millions of edges are likely misclassified or contain hallucinated bottleneck evidence. Claiming "verbatim" grounding for a system with such a high error rate is scientifically unsound; the text should be revised to reflect that evidence is "LLM-extracted and heuristically validated" rather than strictly grounded.

Furthermore, the evaluation of the Idea Generation module (Section 4.3) over-attributes performance gains to the graph structure. The system uses the graph to identify gaps but relies on an LLM to generate the actual proposal text. The reported 88% win rate against a "No-KB" baseline does not sufficiently isolate the graph's contribution from the LLM's parametric knowledge of the specific research queries. Without a controlled ablation where the LLM is given the same structural hints via a different mechanism (or a strict control on the LLM's context window), the claim that the *graph* is the primary driver of improved idea quality is an over-extrapolation.

Finally, the Conclusion states that the system "recovers expert-curated evolution chains more faithfully." Table 1 shows a Node Recall of 84.8% and Edge Recall of 79.0%. While these are improvements over baselines, they indicate that nearly 20% of the ground-truth lineage is missed. Describing this as "faithful" recovery without explicitly acknowledging the ~20% failure rate in the main text is an over-interpretation of the results. The authors must temper their language to accurately reflect the probabilistic nature of the reconstruction rather than implying near-perfect fidelity.
