---
action_items:
- id: 79d8275fcf0c
  severity: science
  text: The claim that 3D points are 'view-stable' (Sec 1) contradicts the methodology
    in Sec 3.1, which anchors the world frame to the camera at t0. If the camera moves,
    coordinates change. Clarify if 'view-stable' refers to relative motion or if the
    frame is truly global (e.g., via SLAM).
- id: c1c11c3ac83a
  severity: writing
  text: The claim of outperforming 'all' baselines (Abstract, Sec 4) is logically
    weakened by excluding PointWorld and MotionForcast from Table 1 due to unreleased
    code. Qualify the claim to 'all evaluated baselines' to avoid overgeneralization.
- id: a9f01bb7e5ca
  severity: science
  text: The dense annotation pipeline (100 points) vs. sparse model input (8 points)
    lacks logical justification. Explain how dense filtering contributes to training
    if the model only sees 8 points, or if the pipeline is merely for data generation
    without direct model impact.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T05:11:21.746897Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent narrative for the MolmoMotion framework, but several logical inconsistencies and overgeneralizations weaken the strength of the conclusions drawn from the premises.

First, there is a fundamental tension between the claimed properties of the representation and the defined coordinate system. In the Introduction, the authors argue that 3D points in world coordinates are "view-stable," implying consistency across different camera viewpoints. However, Section 3.1 ("Problem formulation") explicitly defines the world coordinate frame as "anchored at the camera at time $t_0$." If the camera moves after $t_0$ (which is common in the unconstrained videos used), the coordinates of static background points or even the object itself (relative to the camera origin) will change. The paper does not clarify whether the "world frame" is actually a global SLAM-based frame or a camera-centric frame. If it is the latter, the claim of "view-stability" is logically unsupported, as the representation is inherently tied to the initial camera pose. This ambiguity undermines the argument that the representation is suitable for transfer across different camera settings.

Second, the conclusion that the model "significantly outperforms all existing motion prediction baselines" (Abstract and Section 4) is an overgeneralization. Table 1 explicitly excludes PointWorld and MotionForcast, stating they are excluded because their models "have not yet been released." While it is standard to exclude unavailable code, claiming to outperform "all" baselines is logically flawed when two specific, closely related works are known to exist but were not evaluated. The conclusion should be qualified to "all *evaluated* baselines" or "all *available* baselines" to maintain logical rigor.

Finally, there is a disconnect between the data annotation pipeline and the model input that requires clarification. The pipeline (Sec 3.1) generates dense trajectories (median 88 points, up to 100) and applies complex filtering based on object-level coherence. However, the model is trained on only $N=8$ query points (Sec 4.1). The paper does not logically explain how the dense, filtered data contributes to the training signal if the model only consumes 8 points. If the filtering is only applied to the 8 sampled points, the "dense" nature of the pipeline is irrelevant to the model's learning. If the filtering uses all 100 points to select the best 8, this selection bias should be described. Without this link, the justification for the complex dense pipeline is logically incomplete relative to the sparse model architecture.
