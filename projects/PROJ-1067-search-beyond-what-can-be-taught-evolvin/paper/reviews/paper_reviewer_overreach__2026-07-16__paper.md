---
action_items:
- id: 6dc5c174e3fc
  severity: writing
  text: Abstract claims 'recursive self-improvement' but experiments (Sec 5) show
    only one DPO/RFT pass. Appendix admits multi-round is future work. Change 'recursive'
    to 'single-step' or add multi-iteration results.
- id: 8221d6b1a9ec
  severity: writing
  text: Conclusion claims 'No model, regardless of scale, can internalize knowledge'
    universally. Experiments test only 4B/7B models. Narrow to 'within tested scales'
    or cite scaling law literature to support the universal claim.
- id: c5470d505370
  severity: writing
  text: Finding 1 calls the bottleneck 'universal' across all generators. Data covers
    only a subset of models. Rephrase as 'observed across all tested generators' to
    avoid overgeneralizing beyond the empirical scope.
artifact_hash: acdadb0a7d8b66991ef14c7c4247fe346cb02f508281ed63c55a7e05db3f0d02
artifact_path: projects/PROJ-1067-search-beyond-what-can-be-taught-evolvin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-16T02:54:46.186567Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims about the universality and recursive nature of its proposed "knowledge boundary" and co-training framework that exceed the empirical scope of the provided experiments.

First, the **Abstract** and **Conclusion** frame the work as establishing a foundation for "recursive self-improvement" and claim that the knowledge boundary is "discoverable" and "cannot disappear" regardless of scale. However, the experimental section (Section 5) and Table 1 present results from a **single iteration** of the co-training loop (one DPO pass followed by one RFT pass). The authors explicitly state in the **Appendix (Limitations)** that "multi-round co-training... could progressively sharpen this boundary," admitting that the current results do not demonstrate recursion or convergence. The rhetoric of "recursive self-improvement" and the definitive claim that the boundary "cannot disappear" are not supported by the single-step evidence provided. To fix this, the authors should either narrow the claim to "a single-step co-training protocol" or provide empirical results from at least two or three iterative cycles to substantiate the "recursive" nature of the improvement.

Second, the **Conclusion** makes a universal claim about the limits of scaling: "No model, regardless of scale, can internalize knowledge... The knowledge boundary... cannot disappear." This is a broad theoretical assertion about the fundamental limits of large language and vision models. The paper's empirical evidence is limited to two open-weight generators (4B and 7B parameters) and a few commercial APIs. There is no data presented for larger models (e.g., 70B+ or frontier-scale models) where the proportion of "internalizable" knowledge might significantly increase, potentially challenging the claim that the boundary "cannot disappear." While the intuition is plausible, the paper presents it as a demonstrated fact rather than a hypothesis. The authors should qualify this claim to reflect the tested scale range (e.g., "within the scales we tested") or cite external literature on scaling laws for knowledge retention to support the universal generalization.

Finally, **Finding 1** describes the performance collapse on search-intensive prompts as "universal" and the bottleneck as "structural" across all generators. While the data shows a consistent drop for the tested models, the term "universal" implies a property that holds for *any* possible model architecture or training regime. The study tests a specific subset of models. While the trend is strong, the absolute claim of universality is slightly overreaching given the limited sample of architectures. A more precise phrasing would be "observed across all tested generators" or "robust across diverse architectures," reserving "universal" for a theoretical proof or a much broader empirical sweep.

These issues are primarily matters of **writing** and **framing**. The core contribution—a method to improve search-augmented generation via co-training—is well-supported by the single-step results. However, the paper's rhetoric inflates the scope of these results to imply a solved, recursive, and universal phenomenon that the current data does not yet prove. Narrowing the claims to match the single-iteration, limited-scale evidence will align the paper's confidence with its demonstrated scope.
