---
action_items:
- id: 12fd305b2693
  severity: science
  text: The claim of "substantial" cost reduction is unsupported. Table 2 shows MRAgent
    runtime (586s) exceeds Mem0 (533s). The paper fails to isolate construction vs.
    retrieval token costs to justify the efficiency claim.
- id: 3818acd09e27
  severity: science
  text: Theorem 1's claim that active retrieval is "strictly more powerful" overreaches.
    The proof relies on a synthetic "Binary-Tree" distribution not shown to exist
    in real benchmarks (LoCoMo/LongMemEval).
- id: 1ce2fa790f1c
  severity: writing
  text: The abstract claims "substantially reducing token and runtime cost," but Table
    2 shows MRAgent is slower than Mem0. This overstatement contradicts the data and
    must be toned down.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:25:46.629497Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: major_revision_science
---

The paper exhibits significant overreach in its claims regarding efficiency and theoretical expressivity, which are not fully supported by the presented data or the scope of the theoretical proof.

First, the claim of "substantially reducing token and runtime cost" (Abstract, Contributions) is an overstatement. While Table 2 shows MRAgent uses fewer tokens than A-Mem and LangMem, it does not outperform Mem0 in runtime (586s vs 533s). The text in Section 5.2 attributes this efficiency to "deferring complex relation-building," yet the paper aggregates construction and retrieval costs. It fails to provide a breakdown of the token cost specifically for the *reconstruction* phase versus the *construction* phase. Without isolating these costs, the claim that the *method* is more efficient is not empirically justified.

Second, the theoretical contribution in Section 4.3 overreaches by generalizing a synthetic result to real-world tasks. Theorem 1 asserts that active retrieval is "strictly more powerful" than passive retrieval. The proof (Appendix C.5) relies entirely on a constructed "Binary-Tree Needle-in-a-Haystack" distribution where the answer is encoded in a hidden path bit. This is an artificial worst-case scenario. The paper does not demonstrate that the LoCoMo or LongMemEval benchmarks possess these specific structural properties required for this strict separation to hold. Generalizing a separation result from a synthetic counter-example to general LLM agent memory tasks is a logical leap not supported by the data.

Finally, the motivation section presents a dichotomy between "passive" and "active" that exaggerates the rigidity of existing methods. Some baselines (like A-Mem) perform multi-hop expansion, which is a form of limited adaptivity. The paper's narrative overstates the limitations of baselines to elevate the novelty of its own approach without sufficient comparative analysis of failure modes in the baselines.
