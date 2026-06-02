---
action_items:
- id: 1c17a6309010
  severity: writing
  text: Section 3.4 claims 'trivial' mesh extraction without post-processing, yet
    describes discarding low-opacity triangles, correcting winding order, and merging
    duplicate vertices. These ARE post-processing steps. Clarify whether 'no post-processing'
    means 'no per-scene optimization' or truly no processing, to avoid logical tension
    between abstract claims and method description.
- id: 789932f5a020
  severity: writing
  text: Appendix Table 6 shows TriSplat has -3.21 PSNR degradation from primitive
    to mesh rendering. If rendering primitives ARE the exported mesh (core claim),
    why does degradation exist? Either explain the source of this gap (e.g., opacity
    thresholding, vertex merging artifacts) or clarify what 'no information loss'
    means quantitatively.
- id: 5de6c512bb3f
  severity: science
  text: Training objective Eq. 11 includes L_normal that directly supervises against
    monocular teacher normals throughout training, not just during bootstrap phase.
    This creates logical tension with Section 3.2's claim that the model 'relies entirely
    on its own geometry' after release phase. Clarify whether teacher supervision
    persists and how this affects the self-contained geometry claim.
- id: b578d806b863
  severity: science
  text: Simulation demonstrations (Appendix 6) show qualitative physics results (ball
    drop, locomotion) but provide no quantitative metrics on collision accuracy, surface
    normal consistency for contact, or simulation stability. For a 'simulation-ready'
    claim, this evidence is insufficient to support the causal link between mesh quality
    and downstream physics utility.
artifact_hash: 375d837bf9b63242d32116a8a2f6433796abb291136cadef4ae07e469b227763
artifact_path: projects/PROJ-627-trisplat-simulation-ready-feed-forward-3/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T07:41:14.462628Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent logical chain from problem (Gaussian primitives require lossy mesh extraction) to solution (triangle-native representation) to evidence (mesh-rendering metrics). However, several logical tensions weaken the consistency of key claims.

**Major Tension 1: Post-Processing Definition (Section 3.4)**
The abstract and introduction claim TriSplat enables mesh export "without any post-processing," yet Section 3.4 describes explicit post-extraction steps: discarding low-opacity triangles (opacity threshold 0.10), correcting winding order by comparing face normals to per-pixel normals, and merging duplicate vertices via quantized position hashing. These operations constitute post-processing even if they're algorithmic rather than optimization-based. The paper should clarify whether "no post-processing" means "no per-scene optimization/TSDF fusion" or truly no processing. This distinction matters for the simulation-ready claim.

**Major Tension 2: Primitive-to-Mesh Degradation (Appendix Table 6)**
If rendering primitives ARE the exported mesh (core contribution), the primitive-to-mesh PSNR gap should theoretically be zero. Yet Table 6 shows -3.21 dB degradation on RE10K. The paper doesn't explain the source of this gap—if triangles are identical between rendering and export, what causes the difference? Possible explanations (opacity thresholding removing low-confidence triangles, vertex merging introducing artifacts) should be explicitly discussed to maintain logical consistency.

**Minor Tension 3: Teacher Normal Supervision (Eq. 11)**
Section 3.2 describes a three-phase bootstrap schedule where the model eventually "relies entirely on its own geometry." However, Eq. 11 shows L_normal supervising against teacher normals throughout training with no schedule decay. This creates a logical gap: if teacher normals provide continuous supervision, the model's geometry isn't fully self-contained after the bootstrap release phase. Clarify whether L_normal persists and how this affects the claim of geometry-anchored triangle orientation.

**Evidence Gap: Simulation Utility**
The simulation demonstrations (Appendix 6) provide qualitative evidence (robot locomotion, ball drop) but no quantitative metrics. For a "simulation-ready" claim, the paper should establish a causal link between mesh quality and physics utility—e.g., collision accuracy, contact normal consistency, or simulation stability metrics. Without this, the simulation-ready claim rests on visual demonstration rather than measurable downstream performance.

**Strengths:**
- The comparison protocol (mesh-rendering evaluation for all methods) is logically appropriate for the simulation-ready claim
- Ablation studies (Appendix 7) correctly isolate contributions of each design component
- The primitive-to-mesh degradation analysis (Table 6) is a logically sound way to quantify the claimed advantage over Gaussian baselines

The paper's core logic is sound but requires clarification on these points to fully support the simulation-ready claim.
