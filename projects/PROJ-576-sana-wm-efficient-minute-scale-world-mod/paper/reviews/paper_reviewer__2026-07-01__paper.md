---
action_items:
- id: be8b8f17c6d6
  severity: writing
  text: Clarify the derivation and intuition behind the 1/sqrt(D*S) key scaling factor
    in the GDN section to improve reproducibility.
- id: 452eb54ec71c
  severity: writing
  text: Expand the description of the two-stage refiner's training procedure, specifically
    the loss function formulation and reference conditioning mechanism.
- id: b8c14dc08e28
  severity: writing
  text: Elaborate on the limitations section to explicitly discuss failure modes in
    highly dynamic scenes or rare viewpoints as mentioned in the conclusion.
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: Minor revisions needed for clarity in GDN scaling explanation, refiner details,
  and limitations discussion.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:42:32.917710Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths
This paper presents a significant and timely contribution to the field of world modeling, specifically addressing the challenge of efficient minute-scale video generation. The proposed SANA-WM architecture effectively combines hybrid linear attention (GDN + softmax) with dual-branch camera control to achieve high-fidelity, 720p video generation with precise 6-DoF trajectory adherence. The empirical results are impressive, demonstrating superior action-following accuracy compared to open-source baselines while maintaining competitive visual quality at a fraction of the computational cost. The introduction of a robust annotation pipeline for metric-scale pose extraction and a dedicated long-video refiner are notable methodological advancements. The comprehensive ablation studies and the construction of a new benchmark for minute-scale world modeling further strengthen the paper's contribution to the community.

## Concerns
While the paper is technically sound and well-structured, there are a few areas where clarity and completeness could be improved:
1.  **GDN Key Scaling:** The explanation of the algebraic stabilization for spatial explosion, particularly the derivation of the $1/\sqrt{D \cdot S}$ scaling factor, is somewhat dense. A more intuitive explanation or a step-by-step derivation would make this critical stability mechanism more accessible to readers.
2.  **Refiner Implementation Details:** The description of the second-stage refiner, while mentioning truncated-$\sigma$ flow matching, lacks specific details on the exact loss function formulation and the precise mechanism of reference conditioning (e.g., how the reference tokens are masked and integrated). More details here would aid reproducibility.
3.  **Limitations Discussion:** The limitations section is relatively brief. Given the paper's focus on efficiency and specific architectural choices, a more detailed discussion of potential failure modes (e.g., in highly dynamic scenes, rare viewpoints, or under extreme camera motions) would provide a more balanced view of the system's capabilities and boundaries.

## Recommendation
This paper presents a strong, innovative, and well-executed approach to minute-scale world modeling. The results are compelling, and the methodological contributions are significant. The identified concerns are minor and primarily relate to clarity and completeness of exposition rather than fundamental flaws in the science or methodology. I recommend a **minor_revision**. The authors should address the points above to enhance the paper's clarity and reproducibility. Once these revisions are incorporated, the paper will be well-suited for publication.
