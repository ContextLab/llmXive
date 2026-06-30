---
action_items:
- id: fa7d2e8e12a1
  severity: science
  text: The scientific evidence supporting the central claims of MRAgent is currently
    insufficient to warrant acceptance. While the experimental results on LoCoMo and
    LongMemEval are promising, the theoretical and methodological foundations contain
    significant gaps that undermine the robustness of the conclusions. First, the
    theoretical claim that "active retrieval is strictly more powerful than passive
    retrieval" (Theorem 1, Section 4.3) is not proven for the general case. The proof
    in Appendix C relie
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:27:06.678144Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the central claims of MRAgent is currently insufficient to warrant acceptance. While the experimental results on LoCoMo and LongMemEval are promising, the theoretical and methodological foundations contain significant gaps that undermine the robustness of the conclusions.

First, the theoretical claim that "active retrieval is strictly more powerful than passive retrieval" (Theorem 1, Section 4.3) is not proven for the general case. The proof in Appendix C relies on a specific, contrived "Binary-Tree Needle-in-a-Haystack" distribution where the answer is encoded in a leaf node that is only discoverable by following a specific path of bits. In this artificial setting, passive retrieval fails because it cannot guess the correct leaf without the path information. However, this does not generalize to real-world memory graphs where relevant information is often distributed and accessible via multiple paths or similarity. The proof demonstrates a separation for a specific, adversarial task, not a general property of memory systems. The authors must either provide a more general proof or significantly temper the claim to reflect the specific conditions under which the separation holds.

Second, the evidence for "significant improvements" in computational cost (Table 2) is ambiguous. The table reports total token consumption including memory construction. MRAgent's construction phase is described as a simple LLM extraction, whereas baselines like A-Mem and LangMem may involve more complex graph construction or summarization steps. If the baselines' construction costs are inflated by their own design choices, the comparison is unfair. To support the claim of efficiency, the authors must isolate the retrieval costs or demonstrate that the construction overhead is comparable across methods. Without this, the claim that MRAgent is "substantially reducing token and runtime cost" is not fully supported.

Third, the ablation study (Figure 3) does not cleanly isolate the contribution of the "active" mechanism. The "no-reasoning" variants still utilize the full Cue-Tag-Content (CTC) graph structure. The performance gap between the "no-reasoning" and "reasoning" variants could be attributed to the graph structure itself rather than the active traversal. A more rigorous ablation would compare MRAgent against a baseline that uses the same CTC graph but employs a fixed, non-adaptive traversal policy (e.g., breadth-first search) to determine if the *active* nature of the retrieval is the primary driver of performance.

Finally, the reliance on an LLM-based judge (GPT-4o-mini) as the primary evaluation metric introduces potential bias. The paper does not report any validation of the judge's reliability, such as human evaluation correlation or inter-rater agreement. Given the large performance margins reported, it is crucial to ensure that the judge is not favoring the specific output style or verbosity of MRAgent over the baselines. Without this validation, the magnitude of the reported improvements is uncertain.

In summary, while the proposed method shows empirical promise, the theoretical justification is too narrow, the cost analysis is potentially confounded, and the ablation study lacks necessary controls. A full revision is required to address these evidentiary gaps.
