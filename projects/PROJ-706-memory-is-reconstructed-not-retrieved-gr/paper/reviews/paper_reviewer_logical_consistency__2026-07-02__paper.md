---
action_items:
- id: 100cfbf09cd6
  severity: science
  text: Theorem 1 assumes the active agent can perfectly read path bits in a binary-tree
    task. The paper fails to justify that the proposed LLM routing mechanism ($f_{select}$)
    can reliably perform this bit-extraction in noisy, real-world data, creating a
    gap between the theoretical proof and the practical claim of superiority.
- id: 47a7dabebc7e
  severity: science
  text: The claim that active reconstruction reduces token costs (Section 5.2) lacks
    a breakdown of reasoning vs. retrieval tokens. The algorithm requires multiple
    LLM calls per step; without evidence that pruning savings outweigh this overhead,
    the causal link between the active mechanism and lower cost is unsupported.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:11:35.481793Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper is generally strong in its problem formulation and the distinction between passive and active retrieval. The definition of active reconstruction as a stateful policy conditioned on accumulated evidence (Eq. 2) logically follows the motivation that static similarity scoring fails for complex, multi-hop queries. The proposed Cue-Tag-Content architecture provides a coherent mechanism for the "associative" aspect of the claim.

However, there are two significant gaps in the logical chain between the proposed mechanisms and the final conclusions:

1.  **Theoretical Validity vs. Practical Implementation:** Theorem 1 (Section 3.3) asserts a strict separation between active and passive hypothesis classes. The proof constructs a "Binary-Tree Needle-in-a-Haystack" task where the active agent succeeds by following path bits. The logic holds *if* the active agent can perfectly identify and traverse these bits. However, the paper's proposed mechanism relies on an LLM to perform this selection ($f_{select}$). The paper does not provide a logical argument or empirical evidence that the LLM can reliably extract these specific "path bits" (which may be semantically ambiguous or noisy in real data) better than a passive similarity search. The theoretical advantage assumes an idealized active agent, while the experimental agent is a specific LLM implementation. The conclusion that "Active reconstruction is strictly more powerful" is logically sound in the abstract, but the leap to "MRAgent (the specific LLM implementation) achieves this power" is not fully bridged by the provided evidence.

2.  **Causal Claim on Efficiency:** The conclusion that MRAgent reduces token costs (Section 5.2) relies on the premise that "on-demand" access is more efficient than "repeated summarization." While the ablation study (Figure 4) shows that active reasoning improves accuracy, the cost analysis (Table 2) presents a net reduction in tokens. The logical gap lies in the accounting of the *overhead* of the active process. The algorithm (Algorithm 1) requires multiple LLM calls per step (selection, routing, stopping criteria). The paper does not explicitly demonstrate that the reduction in retrieved context tokens outweighs the increase in reasoning tokens. Without a breakdown of tokens spent on the "reasoning loop" versus the "retrieved content," the causal claim that the *active mechanism* causes the *cost reduction* is not fully supported; it is possible the cost reduction comes from a smaller graph size or different baseline configurations rather than the active logic itself.

The paper would benefit from clarifying the assumptions in the theoretical proof regarding the LLM's capability to execute the active policy, and providing a more granular cost breakdown to support the efficiency claim.
