---
action_items:
- id: 120bbfac2965
  severity: writing
  text: In Section 3.2 (Stage 2 option b), the paper claims causal CD is 'theoretically
    equivalent' to causal ODE distillation citing Zhao et al. (2026). This equivalence
    typically holds only under specific assumptions (e.g., linear ODEs or specific
    noise schedules) which are not stated. The claim should be qualified to avoid
    implying universal equivalence.
- id: 07626bb1e4a3
  severity: writing
  text: Table 1 reports a 223.75x speedup for HY1.5. The calculation (771.041 / 3.446)
    is correct, but the text claims this is a 'reduction' in latency. While colloquially
    acceptable, 'speedup factor' is the precise term for the ratio, whereas 'reduction'
    implies a subtraction (e.g., 99.5% reduction). Clarify terminology to ensure precision.
- id: a6a4e6c69e9e
  severity: writing
  text: The paper cites 'li2026cameras' (PRoPE) for camera injection. As this is a
    2026 citation, verify that the method described (GTA form injection with block-diagonal
    projective matrices) is accurately attributed to that specific preprint and not
    a conflation with other camera-conditioning methods (e.g., ControlNet-style or
    standard cross-attention).
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:44:11.607261Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the fidelity of citations to the attributed evidence.

**Citation and Equivalence Claims:**
In Section 3.2, under "Stage 2 (option b): causal CD initialization," the authors state that Causal Forcing++ replaces ODE distillation with causal consistency distillation (CD), claiming the two are "theoretically equivalent" and citing `zhao2026causal`. While consistency distillation is often derived as a limit or alternative formulation of ODE distillation, strict theoretical equivalence usually requires specific conditions (e.g., the teacher model being a perfect ODE solver or specific noise schedules). Without these caveats, the claim of absolute equivalence is slightly overstated. The text should qualify this as "equivalent under standard consistency training assumptions" or similar to maintain scientific precision.

**Terminology Precision:**
In Section 4.2, the text states the model achieves a "$223.75\times$ first-frame latency reduction." Mathematically, a "reduction" usually refers to the difference ($L_{old} - L_{new}$) or the percentage decrease. The value $223.75$ is the *speedup factor* (ratio $L_{old} / L_{new}$). While the table correctly labels the column "Speedup," the prose conflates the ratio with the concept of reduction. This is a minor semantic inaccuracy that should be corrected to "speedup of" or "latency reduction of 99.5%."

**Attribution of Methodology:**
The paper relies heavily on `li2026cameras` (PRoPE) for the camera injection mechanism described in Section 3.1. The mathematical formulation provided (block-diagonal transformation $D_t^{\mathrm{PRoPE}}$ injected into self-attention via GTA form) is highly specific. Given that `li2026cameras` is a future-dated citation (2026), it is critical to ensure that this specific architectural modification is indeed the core contribution of that work and not a novel combination by the current authors. If PRoPE is a standard method in that preprint, the citation is accurate; if the authors modified the standard PRoPE injection, the claim that they "adopt PRoPE" without noting modifications is misleading.

**Data Claims:**
The ablation studies (Section 4.3) make qualitative claims about "uncontrollable" vs. "strong controllability" based on visual inspection of figures (e.g., Fig. 4, 5, 6). Since the figures are not rendered in the text, the claim that the model is "completely uncontrollable" at 1-2k steps is an interpretation of visual data. This is acceptable as a qualitative report, provided the authors do not claim quantitative metrics (like a specific controllability score) that are not present in the text or tables. The current text avoids specific numbers for these qualitative claims, which is appropriate.

Overall, the claims are largely supported, but the "theoretical equivalence" and "latency reduction" phrasing require minor tightening to be rigorously accurate.
