---
action_items:
- id: '552103110470'
  severity: writing
  text: The claim that OLoRA-tail maintains a consistent ~+20% gain at rank r=1 across
    all batch sizes (Section 3.2.1, Fig 4 caption) appears to overstate the evidence.
    The text notes LoRA degrades to -18% at bs=128, but the 'consistent' gain claim
    implies stability that the data (showing variance in Fig 4d) may not fully support
    without explicit confidence intervals or a definition of 'consistent' in the presence
    of seed sensitivity.
- id: 3c9d591036ce
  severity: science
  text: The extrapolation from a controlled model-count experiment (k=198) to a 'million
    personal models' architecture (Title, Abstract) is a significant leap. While the
    ln(k) fit is provided, the paper does not sufficiently discuss the non-linear
    system costs (e.g., routing overhead, memory bandwidth saturation) that would
    likely dominate at k=1,000,000, potentially invalidating the linear scaling assumption
    for the 'Scale Out' axis.
- id: fac4de411d37
  severity: writing
  text: The assertion that 'Router Replay R3' reduces the semantic gap in MoE models
    (Section 2.4) is supported by probability difference metrics, but the paper overclaims
    the resolution of 'adapter-semantics failures' and 'lifecycle failures' generally.
    The evidence shows R3 helps with routing mismatch, but does not prove it solves
    the broader class of semantic mismatches in checkpoint conversion or serving runtimes
    mentioned in the taxonomy.
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T08:39:56.169345Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents an ambitious framework for scaling PEFT, but several claims extrapolate beyond the immediate empirical evidence provided, particularly regarding the stability of extreme compression and the system-level feasibility of the proposed "million model" architecture.

First, in Section 3.2.1 (Rank Reduction), the authors claim that OLoRA-tail maintains a "consistent ~+20% gain" at rank r=1 across batch sizes. While the data shows a significant improvement over standard LoRA (which degrades to -18%), the term "consistent" glosses over the high seed sensitivity and variance explicitly highlighted in Figure 4d and the surrounding text. The text admits that low-rank regimes are "sharply batch- and seed-sensitive." Claiming a consistent gain without quantifying the variance or providing confidence intervals for the r=1 regime overstates the reliability of the method for production use. The evidence supports that OLoRA-tail *enables* learning at r=1 where LoRA fails, but not that it does so with the stability implied by "consistent."

Second, the "Scale Out" axis relies heavily on an extrapolation from a controlled experiment with k=198 models to a vision of "million personal models" (Title, Abstract, Conclusion). The paper fits a linear curve to accuracy vs. ln(k) for k up to 198 and assumes this trend holds for k=1,000,000. This ignores the likely non-linear system costs associated with managing a million distinct adapters, such as routing overhead, memory bandwidth saturation, and the "cold load" penalties described in Section 6.3. While the authors mention "bounded residency," the claim that diversity scales predictably to a million models without a corresponding analysis of the system-level bottlenecks (beyond simple load times) is an overreach. The data supports the *principle* of diversity, but not the specific *scale* of the proposed architecture.

Finally, the taxonomy of "Scale-Induced Failure Modes" in Section 2.4 lists four categories, including "adapter-semantics failures" and "lifecycle failures." The paper then presents Router Replay R3 as a solution that "substantially reduces TIM" (Training-Inference Mismatch). However, the evidence provided (probability difference metrics) only addresses the algorithmic mismatch (TIM). It does not provide evidence that R3 resolves the broader semantic failures related to checkpoint conversion, quantization, or serving runtime interpretation mentioned in the taxonomy. The paper conflates solving one specific failure mode (routing mismatch) with resolving the entire class of scale-induced failures, which is an unjustified generalization.

To address these overreaches, the authors should temper the language regarding the stability of r=1 adapters, explicitly discuss the system-level scaling limits that challenge the "million model" extrapolation, and clarify that R3 addresses routing mismatch specifically rather than the entire taxonomy of failure modes.
