---
action_items:
- id: a5f0595b355e
  severity: science
  text: Re-run all benchmarks (WorldModelBench, LIBERO-Plus, RoboTwin 2.0) with identical
    seeds, hardware specs, and evaluation scripts as baselines; report standard deviations
    over 5+ runs and perform paired t-tests to validate claimed SOTA margins.
- id: f73ff95e63c5
  severity: science
  text: Provide a detailed ablation study isolating the contribution of the Hybrid
    Linear Temporal Attention (GLA/SWA/DSWA) versus standard attention baselines on
    long-horizon tasks; current results conflate architecture gains with data scaling
    effects.
- id: b5a3682112f6
  severity: science
  text: 'Clarify the ''real-time'' claim on consumer hardware (RTX 5090): specify
    the exact inference loop latency (preprocessing + model + postprocessing) and
    control frequency (Hz) achieved in a closed-loop robotic task, not just raw generation
    latency.'
- id: 69ecc0a430ba
  severity: science
  text: 'Reconcile the theoretical ''necessity of persistent state'' (Theorem 1) with
    the empirical architecture: demonstrate how the specific GLA implementation satisfies
    the contraction condition (rho < 1) in practice, including empirical measurement
    of the spectral radius.'
- id: 1e2b6f206b47
  severity: writing
  text: 'Address the discrepancy in data engineering metrics: Table 1 claims a 34x
    speedup for captioning but lists ''hours/day'' as the unit; clarify if this is
    throughput (clips/hour) or processing time reduction, and provide the absolute
    clip counts processed.'
artifact_hash: 926e7dfe86ab0c8e4b8d20a90a842eec681ad7b82ae76075a7b3082533c6260d
artifact_path: projects/PROJ-740-kairos-a-native-world-model-stack-for-ph/paper/metadata.json
backend: dartmouth
feedback: Claims of SOTA performance and real-time edge deployment lack reproducible
  experimental protocols, baseline normalization, and statistical significance testing;
  theoretical bounds are disconnected from empirical architecture.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T11:48:00.545520Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Ambitious Scope:** The paper proposes a comprehensive "Native World Model Stack" that unifies understanding, generation, and prediction, addressing a critical fragmentation in current Physical AI research.
- **Theoretical Grounding:** The inclusion of a formal theoretical analysis (Section 6) regarding the necessity of persistent latent states and the sufficiency of hybrid memory is a strong addition, providing a mathematical justification for the architectural choices.
- **Data Engineering:** The detailed breakdown of the data engineering infrastructure (Shot Detection, Frame Filtering, Captioning) and the claimed throughput improvements demonstrate significant engineering effort in curating the massive datasets required for such models.
- **Architecture Innovation:** The proposed Mixture-of-Transformers (MoT) stack with Hybrid Linear Temporal Attention (combining GLA, SWA, and DSWA) is a novel approach to balancing long-horizon consistency with computational efficiency.

## Concerns
- **Reproducibility and Baseline Fairness:** The evaluation section (Section 5) presents impressive SOTA numbers (e.g., 96.1% on RoboTwin 2.0, 9.30 on WorldModelBench) but lacks critical details for reproducibility.
    - **Missing Statistical Rigor:** Results are presented as single-point estimates without standard deviations or confidence intervals. Given the stochastic nature of diffusion models and RL, claims of "outperforming" baselines by small margins (e.g., 96.1% vs 96.0%) are statistically insignificant without multiple runs.
    - **Baseline Discrepancies:** The comparison with models like Cosmos-Predict2.5-14B and Wan2.2-5B does not explicitly state if the baselines were re-trained, fine-tuned, or evaluated with their official checkpoints under identical conditions. The massive speedup claims (28x-85x) suggest a potential mismatch in evaluation protocols (e.g., different resolutions, frame rates, or hardware).
    - **Hardware Ambiguity:** The "real-time" claim on consumer hardware (RTX 5090) is based on raw generation latency (43s for 5s video). This does not equate to real-time *control* (which requires <100ms latency for a 10Hz control loop). The paper conflates generation speed with closed-loop inference capability.

- **Theoretical-Empirical Gap:** While the theoretical section (Section 6) is mathematically sound, the connection to the empirical implementation is weak.
    - The paper proves the *necessity* of persistent states but does not empirically demonstrate that the specific GLA implementation used in Kairos satisfies the contraction condition ($\rho < 1$) required for the sufficiency proof.
    - The "Hybrid Multi-Scale Temporal Memory" is described theoretically, but the ablation studies do not isolate the contribution of each attention mechanism (GLA vs. SWA vs. DSWA) to the final performance, making it unclear which component drives the success.

- **Data and Training Transparency:**
    - The "Cross-Embodiment Data Curriculum" (CEDC) is described conceptually, but the exact composition of the datasets (percentages of open-source vs. proprietary, specific robot models used) is vague.
    - The "Self-Evolution" and "Prompt Self-alignment" sections describe future work or high-level concepts without providing concrete results or metrics on how these mechanisms improved the final model performance.

- **Writing and Structure:**
    - The paper is dense and occasionally repetitive (e.g., the theoretical results are summarized twice in slightly different forms).
    - Some tables (e.g., Table 1 on Data Engineering) have confusing units ("hours/day" for speedup), which obscures the actual throughput gains.

## Recommendation
The paper presents a compelling vision and a sophisticated architecture for Physical AI, but the current empirical evidence is insufficient to support the strong claims of SOTA performance and real-time deployment. The lack of statistical rigor, unclear baseline comparisons, and the disconnect between theoretical guarantees and empirical implementation prevent this from being publication-ready.

The verdict is **major_revision_science**. The authors must re-run the experiments with rigorous statistical analysis, clarify the evaluation protocols to ensure fair baseline comparisons, and provide empirical evidence linking the theoretical properties of their architecture to the observed performance gains. Specifically, they need to demonstrate that the "real-time" claim holds for closed-loop control, not just video generation, and isolate the contributions of their novel attention mechanisms. Without these revisions, the scientific validity of the claims remains unproven.
