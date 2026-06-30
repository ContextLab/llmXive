---
action_items:
- id: 384ca4bae8f2
  severity: science
  text: Theorem 1 proof assumes the query x reveals no path info. If x can encode
    the path, passive policies could win. The separation requires stricter query space
    constraints to be logically sound.
- id: 817ca9208217
  severity: writing
  text: Table 1 shows MRAgent has lower Multi-hop F1 (43.69) than Mem0 (45.17) despite
    claiming active reconstruction solves multi-hop issues. The text fails to reconcile
    this contradiction or explain the metric divergence.
- id: a7a8c1de84a1
  severity: writing
  text: Section 3.1 defines the graph M=(C,V,R) but Section 3.2 introduces Topic nodes
    and edges not present in the formal definition of V or R. The architecture description
    exceeds the formal model.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:23:44.478714Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent argument for shifting from passive to active memory reconstruction, supported by a clear problem formulation in Section 2 and a detailed methodology in Sections 3 and 4. The logical flow from the limitations of static retrieval to the proposed Cue-Tag-Content graph and active traversal is consistent.

However, there are specific logical gaps in the theoretical and empirical claims:

1.  **Theoretical Separation (Section 4.3 & Appendix C):** Theorem 1 asserts that active retrieval is strictly more powerful than passive retrieval. The proof constructs a "Binary-Tree Needle-in-a-Haystack" task where the target path is hidden in node payloads. The logical consistency of this separation relies on the assumption that the query $x$ provides *no* information about the target path other than the root. The definition of the passive policy allows it to be a function of $x$. If the query space $\mathcal{X}$ is not strictly constrained to exclude the path information (e.g., if $x$ could implicitly encode the path via a complex embedding), a passive policy could theoretically achieve zero error. The proof would be logically tighter if it explicitly defined the query distribution to ensure the target path is independent of $x$ given the memory structure, or if it demonstrated that the passive policy cannot "guess" the path without the adaptive feedback loop.

2.  **Empirical Contradiction (Section 5.2):** The paper claims MRAgent outperforms baselines due to active reconstruction. Table 1 shows MRAgent achieves the highest *Overall* LLM-Judge score (84.21) but a lower *Multi-hop* F1 score (43.69) compared to Mem0 (45.17). The text attributes the success to the ability to handle complex multi-hop queries. The logical inconsistency lies in the fact that the specific metric (F1) for the most complex query type (Multi-hop) is worse than a baseline, while the aggregate score is better. The authors do not explain this discrepancy or provide a logical argument for why the "active" mechanism fails to improve F1 on multi-hop tasks despite improving the overall judge score. This weakens the causal claim that the proposed mechanism is the sole driver of performance gains across all dimensions.

3.  **Formal Definition Gap (Section 3):** The formal definition of the memory graph in Section 3.1 ($\mathcal{M} = (\mathcal{C}, \mathcal{V}, \mathcal{R})$) does not account for the "Topic" nodes introduced in Section 3.2. The text describes Topics as a distinct layer connected to episodes, but the mathematical definition of $\mathcal{V}$ and $\mathcal{R}$ does not include these elements or their specific relations. This creates a disconnect between the formal model and the described system architecture.
