---
action_items:
- id: e4fdb9751c6f
  severity: science
  text: The claim that OPD 'rapidly enters' a locked subspace (Sec 5.2) relies on
    subspace similarity metrics computed at discrete checkpoints (63, 127, 191 steps).
    The evidence does not rule out that the lock emerges between these checkpoints
    or that the 'early' alignment is an artifact of the specific 20% projection start
    point. Provide a finer-grained trajectory analysis or sensitivity analysis of
    the projection start time to confirm the 'rapid' nature of the lock.
- id: bd381673e4a9
  severity: science
  text: The functional sufficiency claim (Sec 5.2) is based on a single projection
    dimension (K=16). While the text notes this is 'close to' the observed stable
    rank, the evidence does not demonstrate that the result is robust to small variations
    in K (e.g., K=12 or K=20). A sensitivity analysis of the rank-constrained training
    results is required to ensure the 'sufficiency' is not an artifact of the specific
    K=16 choice.
- id: 24cfd0a344b2
  severity: science
  text: The control experiment mixing OPD and RLVR objectives (Sec 6.2) uses a linear
    interpolation of advantage signals. The claim that this isolates 'objective composition'
    as the driver assumes the mixing does not introduce confounding variance in gradient
    magnitudes or optimization dynamics. The paper should report whether the mixed
    objectives were normalized or if gradient norms were controlled to ensure the
    spectral shift is due to direction, not scale.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:32:56.208764Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling empirical characterization of On-Policy Distillation (OPD) update geometry, supported by a suite of parameter-space diagnostics (update sparsity, principal-angle rotation, spectral drift). The evidence for OPD occupying a "relaxed off-principal regime" is robust, with consistent results across multiple model scales, teacher configurations, and data domains (Table 1, Fig 1). The use of bf16-aware sparsity is a methodological strength, addressing the quantization artifacts common in large model analysis.

However, the evidence for the central claim of "subspace locking" (Sec 5) requires further validation to rule out alternative explanations. The claim that OPD "rapidly enters" a low-dimensional channel relies on subspace similarity metrics computed at relatively sparse checkpoints (e.g., steps 63, 127, 191). Without finer-grained trajectory data, it is difficult to distinguish a true "rapid lock" from a gradual convergence that happens to appear early due to the sampling interval. Furthermore, the functional sufficiency experiment (rank-16 projection) uses a single fixed dimension (K=16). While justified as being near the observed stable rank, the lack of a sensitivity analysis (e.g., varying K) leaves open the possibility that the observed robustness is specific to that exact dimension rather than a general property of the subspace.

Finally, the control experiments in Section 6, particularly the objective mixing, assume that linear interpolation of advantage signals isolates the objective composition without introducing confounding changes in gradient scale or optimization dynamics. The paper should clarify if gradient norms were monitored or normalized in these mixed-objective runs to ensure the observed spectral shifts are purely directional. Addressing these points would significantly strengthen the causal claims regarding the mechanism of subspace locking.
