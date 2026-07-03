---
action_items:
- id: 77ec64d400ca
  severity: science
  text: The Introduction claims the method provides 'tighter bounds on expert utilization'
    (Section 1, Contributions), yet the paper presents no formal bounds, theorems,
    or proofs regarding utilization rates. This is an unsupported theoretical claim
    that must be removed or substantiated with actual derivations.
- id: a1dbdf453c24
  severity: science
  text: 'The Abstract and Introduction state that the method ''matches or exceeds''
    recent alternatives like Switch Transformer, but the Experiments section (Section
    5) explicitly states: ''We forgo comparisons with other baselines since our design
    conforms to the standard router form.'' The claim of superiority over specific
    named baselines is unsupported by the provided data.'
- id: e0351a934251
  severity: writing
  text: The paper claims 'zero inference overhead' (Section 5, Efficiency Analysis)
    because weights are pre-computed. However, the 'Power-then-Retract' step requires
    matrix-vector products with expert weights ($W_g W_g^T$) during the forward pass
    (Eq. 2) or at load time. If computed at load time, this adds a non-trivial initialization
    cost proportional to expert size, which contradicts the 'zero overhead' absolute
    claim. If computed online, it adds FLOPs. The claim needs qualification.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:59:48.487029Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript exhibits significant overreach in its theoretical and comparative claims relative to the provided evidence.

First, the Introduction explicitly lists as a main contribution: "(2) we provide a theoretical analysis yielding tighter bounds on expert utilization." However, a review of the Methodology and Appendix reveals no such bounds. Section 3.3 derives an update rule approximation and discusses convergence to the principal singular vector, but it never establishes a bound on *expert utilization* (e.g., load balancing metrics or utilization rates) nor proves it is "tighter" than existing methods. This is a clear over-claim of theoretical contribution.

Second, the Abstract and Introduction assert that the approach "matches or exceeds" recent alternatives such as the Switch Transformer. Yet, Section 5.2 ("Comparative Analysis with vanilla MoE") explicitly states: "We forgo comparisons with other baselines since our design conforms to the standard router form and is theoretically orthogonal to these studies." The paper only compares against a "vanilla MoE" baseline (presumably a standard router implementation) and does not include Switch Transformer or other named SOTA routers in the experimental tables. Claiming superiority over specific external baselines without presenting data for them is unsupported.

Finally, the claim of "zero inference overhead" in Section 5.2 is absolute and potentially misleading. While the authors argue weights can be pre-computed, the method requires computing $R_{[i]} W_g^i W_g^{i\top}$ (Eq. 2). If this is done at load time, it incurs a startup cost dependent on the expert matrix size, which is non-zero. If done online, it adds computation. The text should clarify the trade-off rather than asserting zero overhead.

These issues require revision to align the claims strictly with the presented data and derivations.
