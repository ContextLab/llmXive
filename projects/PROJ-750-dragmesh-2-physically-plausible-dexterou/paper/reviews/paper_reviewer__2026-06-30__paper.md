---
action_items:
- id: b3aaeb1b2c90
  severity: writing
  text: Verify all citations in the bibliography; several entries (e.g., zhang2025dragmesh,
    wang2026paws) reference future dates (2025/2026) or arXiv preprints that may not
    exist or be peer-reviewed, violating the requirement for verified references.
- id: aebba3ad6e4e
  severity: science
  text: "The core scientific claim\u2014that kinematic error alone can robustly infer\
    \ contact impedance under high damping (x4)\u2014is not sufficiently validated.\
    \ The paper admits failure modes (action saturation) and relies on simulation;\
    \ a real-world hardware experiment with force/torque sensors is required to prove\
    \ the \"force-free\" observation channel is viable for the claimed robustness."
- id: ba672207c58b
  severity: science
  text: The ablation study on "Extended Fine-Tuning" (Table 4) shows that the proposed
    method degrades significantly with longer training, yet the paper does not provide
    a theoretical or empirical justification for why the "Both" fine-tune is the optimal
    stopping point, risking overfitting to the specific damping distribution.
- id: ad1b92904c22
  severity: science
  text: The dataset generation algorithm (Algorithm 1) relies on heuristic geometric
    rules (e.g., "front face" fallback) that are not robust to arbitrary GAPartNet
    annotations; the paper must demonstrate that the generated trajectories are physically
    valid across the entire dataset, not just the 7 selected objects.
artifact_hash: aac12eff083d8d7168328cdeef9fdab897d5808d01d31c99a8c36453db9b88d3
artifact_path: projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/paper/metadata.json
backend: dartmouth
feedback: PICA's robustness claims are undermined by unverified citations and the
  lack of real-world validation for the proposed contact-inference mechanism under
  high damping.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T13:47:56.273060Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Clear Problem Formulation:** The paper effectively identifies the gap between object-centric articulated generation and contact-driven dexterous interaction, framing the problem as a "contact-driven" task where motion must emerge from physical interaction rather than trajectory replay.
- **Comprehensive Evaluation Protocol:** The introduction of damping multipliers ($\times1, \times2, \times4$) and the explicit reporting of action saturation (`clip099`) and detachment rates provide a much-needed diagnostic lens beyond simple success rates. The finding that nominal success masks saturation collapse (Table 3) is a valuable contribution to the field.
- **Dataset Contribution:** The release of a pure-geometry interaction dataset (277 trajectories) derived heuristically from GAPartNet is a useful resource for the community, provided the generation logic is robust.
- **Ablation Depth:** The ablation studies (Table 4, Table 5) are thorough, isolating the contributions of the GLA encoder and physical signals, and honestly reporting the limits of extended fine-tuning and damping randomization.

## Concerns
- **Unverified Citations:** The bibliography contains multiple entries with future dates (e.g., `wang2026paws`, `zhang2026dicart`, `wu2026dipo`) and arXiv preprints from 2025/2026. As an arXiv-submitted paper, these references must be verified as existing, peer-reviewed, or at least publicly available preprints. Citing non-existent or future-dated work undermines the scientific rigor of the related work section.
- **Scientific Validity of "Force-Free" Contact Inference:** The central claim of PICA is that it achieves robustness under high damping without tactile or force feedback, relying instead on kinematic error and temporal history. However, the results show a significant drop in success at $\times4$ damping (0.56 deterministic), and the paper admits that "contact state can only be inferred indirectly... which appears insufficient for stable light pulling at high damping." The paper does not provide a rigorous proof or sufficient empirical evidence that the proposed auxiliary supervision (predicting object response from history) is a valid proxy for contact impedance in the absence of force sensors. The reliance on simulation (Isaac Gym) without a corresponding real-world validation with force/torque sensors leaves the "physically plausible" claim unproven for real-world deployment.
- **Overfitting and Training Dynamics:** The "Extended Fine-Tuning" study (Table 4) reveals that the proposed method is highly sensitive to training duration, with performance collapsing after 300 epochs. The paper does not offer a robust mechanism (beyond manual early stopping based on OOD metrics) to prevent this collapse, suggesting the method is not stable enough for general application.
- **Dataset Generation Heuristics:** The trajectory generation algorithm (Algorithm 1) uses heuristics like "front face" fallback for handle selection. While functional for the 7 selected objects, the paper does not demonstrate that these heuristics generalize to the full GAPartNet dataset or handle edge cases (e.g., objects with multiple handles, non-standard geometries). The claim of a "pure-geometry" dataset is weakened if the generation logic is brittle.
- **Hardware Validation:** The hardware results (Figure 5, Appendix) are presented as "qualitative feasibility" only. Given the paper's focus on "physically plausible" interaction, the lack of quantitative real-world results (even on a single object) is a significant gap. The simulation-to-real gap in contact dynamics is notoriously difficult, and the paper's claims about robustness are not supported by real-world data.

## Recommendation
The paper presents a well-structured and insightful analysis of contact-driven dexterous manipulation, with a strong evaluation protocol that highlights the limitations of current methods. However, the core scientific contribution—the PICA mechanism's ability to infer contact impedance without force feedback—is not sufficiently validated. The reliance on simulation, the admission of failure modes under high damping, and the lack of real-world quantitative results undermine the claim of "physical plausibility." Additionally, the bibliography contains unverified and future-dated citations, which must be corrected.

The paper requires **major_revision_science**. The authors must:
1.  **Verify all citations** and remove or replace any non-existent or future-dated references.
2.  **Conduct real-world experiments** with force/torque sensors to validate the PICA mechanism's ability to infer contact impedance and achieve robustness under high damping. If real-world validation is not possible, the claims must be significantly tempered, and the paper should focus on the simulation-based insights.
3.  **Provide a theoretical or empirical justification** for the stability of the PICA mechanism under extended training, or propose a more robust training protocol that prevents the observed collapse.
4.  **Demonstrate the robustness of the dataset generation algorithm** across a wider range of GAPartNet objects, or acknowledge its limitations more clearly.

Without these revisions, the paper's scientific claims remain unproven and its contribution to the field of physically plausible dexterous manipulation is limited.
