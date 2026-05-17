---
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:43:28.228958Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.5
verdict: accept
---

The paper maintains strong internal logical consistency between its stated efficiency goals, proposed architectural mechanisms, and empirical evidence.

**Architecture & Stability:** The premise that standard cumulative linear attention causes drift at minute scales (Sec 3.2) is logically addressed by the Gated DeltaNet (GDN) recurrence. The algebraic derivation for key scaling (Eq 4-5) correctly identifies the $O(S)$ trace risk in spatial token aggregation. This theoretical claim is directly validated by the stability ablation in Fig 5, where unscaled or $L_2$-scaled variants trigger NaNs, while the proposed $1/\sqrt{DS}$ scaling ensures convergence. The causal link between the mathematical stabilization and training success is well-supported.

**Control Mechanism:** The claim that dual-branch conditioning is necessary for precise 6-DoF control (Sec 3.3) is supported by the ablation in Tab 3. The data shows that UCPE alone reduces RotErr but not TransErr as effectively as the combined UCPE+Pl\"ucker approach, validating the hypothesis that coarse global and fine raw-frame branches are complementary. The logic that Pl\"ucker mixing compensates for VAE temporal strides (Sec 3.3) is consistent with the reported improvements in CamMC.

**Efficiency Claims:** The abstract claims $36\times$ higher throughput than scalable baselines. Table 1 shows SANA-WM (24.1 videos/hour) vs. LingBot-World (0.6 videos/hour), which yields $\approx 40\times$. The $36\times$ figure is a conservative estimate consistent with the provided data relative to the industrial baselines cited. The memory scaling argument (Fig 6b) logically supports the single-GPU inference claim, as the recurrent state remains $D\times D$ regardless of sequence length, unlike the all-softmax baseline which OOMs.

**Refinement Pipeline:** The claim that the second-stage refiner improves both visual quality and pose accuracy (Tab 1) is logically consistent with the Appendix description of reference conditioning (App Sec 1), which preserves identity anchors during flow matching. While counter-intuitive that a refiner improves control, the mechanism (reference tokens excluded from loss) explains why the refiner does not drift from the pose conditioning provided in Stage 1.

No internal contradictions or unsupported causal leaps were identified. The conclusions follow directly from the presented mechanisms and data.
