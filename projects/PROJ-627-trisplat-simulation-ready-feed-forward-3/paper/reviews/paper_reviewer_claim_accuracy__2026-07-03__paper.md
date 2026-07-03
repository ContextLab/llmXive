---
action_items:
- id: f3d2bcda41e1
  severity: writing
  text: Section 4.2 claims Gaussian baselines suffer 'substantial' degradation while
    TriSplat is stable. Table 2 shows MeshSplat (a Gaussian method) has -3.18dB degradation,
    nearly identical to TriSplat's -3.21dB. The claim overgeneralizes; clarify that
    standard TSDF fusion degrades, but optimized variants like MeshSplat do not.
- id: fba949643935
  severity: writing
  text: Section 3.2 states the point map 'may be optionally detached' from the graph.
    It is unclear if this was used in final results. If used, clarify the impact on
    gradient flow; if not, remove 'optionally' to avoid confusion about the reported
    method's architecture.
- id: a1e50c7786c9
  severity: writing
  text: Section 4.2 attributes Gaussian degradation to 'discarding primitives'. However,
    MeshSplat uses TSDF fusion yet matches TriSplat's stability. The text should specify
    that the degradation applies to standard TSDF pipelines, not all Gaussian methods,
    or explain MeshSplat's distinct pipeline.
artifact_hash: 375d837bf9b63242d32116a8a2f6433796abb291136cadef4ae07e469b227763
artifact_path: projects/PROJ-627-trisplat-simulation-ready-feed-forward-3/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:53:31.011705Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with the provided evidence.

**1. Overgeneralization of Baseline Degradation:**
In Section 4.2, the text asserts that "Gaussian baselines incur a substantial quality drop" due to TSDF fusion, contrasting this with TriSplat's stability. While this holds for MVSplat and DepthSplat (Table 2 shows drops of -10.70dB and -5.67dB), it is contradicted by MeshSplat, a Gaussian-based baseline. Table 2 (tab:app_prim_to_mesh) shows MeshSplat has a degradation of -3.18 dB, which is nearly identical to TriSplat's -3.21 dB. The claim that Gaussian methods *inherently* suffer a substantial drop is inaccurate given MeshSplat's performance. The text should clarify that the degradation is specific to standard TSDF fusion of raw Gaussians, not all Gaussian variants, or explain why MeshSplat's pipeline differs.

**2. Ambiguity in Methodological Implementation:**
Section 3.2 mentions that "The point map may be optionally detached from the computation graph." This phrasing introduces ambiguity regarding the final reported results. If this detachment was applied, it implies the normal refinement head does not receive gradients from the point prediction loss, which is a significant architectural choice. If it was not applied, the "optionally" qualifier is misleading in the context of the main method description. The authors must clarify whether this specific implementation detail was used in the experiments reported in Tables 1-3.

**3. Causal Attribution of Quality Drop:**
The text attributes the quality drop in Gaussian baselines to the "discretized volume discarding the very primitives." While valid for standard TSDF, the text fails to account for MeshSplat, which uses a similar TSDF pipeline (Section 4.1) yet achieves stability comparable to TriSplat. The claim that TriSplat's advantage stems from "no information is lost" is technically true for direct export, but the comparison with MeshSplat suggests the "loss" is not inherent to the Gaussian primitive type but to the specific fusion parameters. The text should refine the causal explanation to avoid implying that *all* Gaussian methods suffer this fate.

**4. Numerical Consistency:**
The numerical claims in Section 4.2 regarding improvements over YoNoSplat (CD: 0.077, F1: 0.179, Recall: 0.227) are mathematically consistent with Table 1 (tab:main_re10k). The primary issue lies in the qualitative interpretation of the degradation metrics relative to the full set of baselines.
