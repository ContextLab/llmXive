---
action_items:
- id: 00e52dcdfc76
  severity: science
  text: Table 5 claims MRAgent uses 118k tokens vs A-Mem's 632k including construction.
    However, MRAgent's construction is described as lightweight while baselines perform
    intricate analysis. The paper fails to clarify if baseline construction costs
    are amortized or per-query, making the direct comparison potentially unfair.
- id: 3570583523bf
  severity: science
  text: Theorem 1 claims active retrieval is strictly more expressive, proven via
    a synthetic "Binary-Tree Needle" task. The paper does not show real-world tasks
    (LoCoMo/LongMemEval) share the specific structural properties (hidden path bits)
    required for this separation, overgeneralizing from a synthetic worst-case.
- id: d1ef95ac4397
  severity: writing
  text: The claim that cues propagate through intermediate representations (Section
    1) cites rugg2025cognitive and frankland2019neurobiological. The text should verify
    these specific sources explicitly support the "intermediate representation" mechanism
    proposed, rather than just general memory theory, to avoid conflation.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:24:44.772317Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the validity of citations supporting them.

**1. Cost Efficiency Claims (Section 5.2, Table 5):**
The paper claims MRAgent reduces token consumption to 118k compared to A-Mem's 632k, stating these figures include "memory construction and retrieval." However, the methodology for MRAgent describes a "lightweight construction phase" where complex relation building is deferred to retrieval. In contrast, baselines like A-Mem are described as performing "intricate dependency analysis" during construction. The paper fails to clarify if the baseline construction costs are amortized over a session or calculated per-query. If the baselines' construction is a one-time cost for a long conversation and MRAgent's is per-query (or vice versa), the direct comparison of "per-sample" costs in Table 5 may be methodologically flawed. The claim of "significant decrease" is not fully supported without a clear definition of the cost accounting boundary for the baselines.

**2. Theoretical Expressivity Claim (Section 4.3, Appendix C):**
The paper asserts that "active retrieval policies are strictly more expressive than passive retrieval" (Theorem 1). The proof relies on a specific synthetic distribution: the "Binary-Tree Needle-in-a-Haystack" task where the answer is encoded in a leaf node and the path is determined by bits in internal node payloads. While the mathematical separation holds for this specific distribution, the paper does not demonstrate that real-world memory tasks (LoCoMo, LongMemEval) possess these specific structural properties (i.e., that the correct retrieval path is hidden in node payloads and requires sequential bit-extraction). The claim overgeneralizes a theoretical worst-case separation to the general domain of LLM agent memory without empirical evidence that the baselines fail on tasks with this specific structure.

**3. Cognitive Neuroscience Citations (Section 1, Section 8):**
The paper cites `rugg2025cognitive` to support the claim that memory retrieval is an "active and associative reconstruction process" where cues propagate through intermediate representations. While this aligns with general cognitive theory, the specific mechanism described (cues -> intermediate representations -> reconstruction) should be verified against the 2025 source to ensure it is not a conflation of older theories (e.g., Tulving 1972, which is cited but not linked to this specific "propagation" mechanism in the text). Additionally, the citation `frankland2019neurobiological` is used to support the "propagation" claim; the paper should ensure the 2019 source explicitly supports the "intermediate representation" aspect of the proposed Cue-Tag-Content architecture, rather than just general memory consolidation.

**4. Baseline Characterization (Section 2, Appendix A):**
The paper characterizes A-Mem, MemoryOS, and others as "passive" because their traversal operators are "predefined and fixed." However, A-Mem uses LLM-assisted relation extraction during construction. The claim that these systems "fail to infer new retrieval cues" is accurate for the *retrieval* phase, but the paper should be precise that the "passivity" refers to the *inference-time* traversal policy, not the entire system lifecycle. The current phrasing risks misrepresenting the capabilities of the baselines during the construction phase.
