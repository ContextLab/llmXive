---
action_items:
- id: 9e2a8748f3f2
  severity: science
  text: The claim of zero-shot generalization from 2 to 4 agents (Sec 4.2, Fig 4)
    lacks quantitative metrics. Provide FVD/FID scores for the 4-agent setting to
    substantiate the visual evidence and rule out overfitting to the 2-agent training
    distribution.
- id: 395aef7c7422
  severity: science
  text: The efficiency comparison in Fig 3 and Sec 4.2 reports latency and FLOPs but
    omits the actual generation quality (FVD/FID) for the 4 and 8 agent configurations.
    Without these metrics, the trade-off between the claimed linear scaling and potential
    quality degradation remains unverified.
- id: d8f28a74452c
  severity: science
  text: The ablation study in Table 2 (Hub Token count) shows diminishing returns
    for K > 8, yet the main model uses K=8. The text does not explicitly justify why
    K=8 was chosen over K=32 or K=128 given the marginal quality gains, nor does it
    report the inference latency impact of increasing K.
artifact_hash: 23197b85ae0bafaaddd0cb8ec8c0f5430ac77fd724ba8930f4eb33d7998307b0
artifact_path: projects/PROJ-641-https-arxiv-org-abs-2605-28816/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T23:22:12.070617Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling architectural approach to multi-agent world modeling, specifically addressing the quadratic scaling of attention and the symmetry requirements of agent identities. The mathematical derivation of the Simplex Rotary Agent Encoding (Appendix) is sound and provides a rigorous basis for the permutation-symmetric claim. The ablation studies in Table 2 effectively isolate the contributions of the proposed components, showing that the combination of Simplex Encoding and Sparse Hub Attention yields the best performance.

However, the scientific evidence supporting the central claim of "scaling beyond two players" is currently incomplete. While the qualitative results in Figure 4 (4-agent rollouts) are visually convincing, the quantitative evidence is missing. The text states the model generalizes from two to four players without additional training, but Table 1 and Table 2 only report metrics for the 2-agent setting (implied by the training data description). To validate the zero-shot generalization claim, the authors must report FVD and FID scores for the 4-agent test set. Without these numbers, it is impossible to rule out the possibility that the model is merely generating plausible-looking but inconsistent videos when the agent count increases.

Furthermore, the efficiency analysis in Section 4.2 and Figure 3 focuses heavily on latency and FLOPs. While the reduction in computational cost is theoretically sound, the paper does not present a Pareto frontier analysis showing how generation quality degrades (if at all) as the number of agents increases under the Sparse Hub Attention regime. The ablation on hub token count (Table 4) suggests that increasing K improves quality slightly, but the authors do not discuss the computational cost of this increase in the context of the 4/8 agent scenarios. The claim of "real-time" performance at 24 FPS needs to be contextualized with the specific hardware used and the resolution, which is mentioned as 320x480 in the appendix but not explicitly linked to the FPS claim in the main text.

Finally, the comparison with Solaris is limited to the 2-agent setting in Table 1. A direct comparison of the 4-agent performance between Gamma-World and Solaris (or a theoretical extrapolation of Solaris's cost) would strengthen the argument for the proposed architecture's scalability. The current evidence supports the method's validity in the 2-agent setting but leaves the "beyond two players" claim reliant on qualitative inspection.
