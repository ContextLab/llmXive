---
action_items:
- id: 5a3062277130
  severity: science
  text: Replace all 2025/2026 citations (e.g., Omni-WorldBench, HY-WorldPlay 1.5)
    with verified, publicly available references or provide the raw data and code
    to reproduce the benchmark results immediately.
- id: 5acd6c9eea94
  severity: science
  text: 'Provide a detailed breakdown of the 16 FPS claim: specify the exact batch
    size, resolution, and whether the 8 RTX 5090s are used for model parallelism or
    pipeline parallelism, and include the latency distribution (p50, p99).'
- id: 36ea3c402e6e
  severity: science
  text: 'Clarify the ''geometry-based retrieval'' mechanism in Section 5.2: specify
    the exact algorithm for matching camera poses to history frames and the threshold
    parameters used, as the current description is too high-level for reproduction.'
- id: 2f1121b3afa8
  severity: science
  text: Address the conflict between the 'Event Instruction Tuning' claims and the
    'Limitations' section regarding control signal conflicts; provide a concrete example
    or ablation study showing how the model resolves incompatible prompts.
artifact_hash: dd358f57d42e68a3445f4b34d5b2202a60d20e2d68878dcf007801dde467660f
artifact_path: projects/PROJ-717-dreamx-world-1-0-a-general-purpose-inter/paper/metadata.json
backend: dartmouth
feedback: Evaluation metrics rely on unverified future-dated citations and self-referential
  benchmarks; reproducibility of the 16 FPS claim and memory retrieval logic is insufficiently
  detailed.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T05:16:02.037986Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Comprehensive System Design**: The paper presents a well-structured, full-stack approach to interactive world modeling, integrating data curation, training pipelines, and inference optimization. The progressive training strategy (camera control -> memory -> events -> distillation -> RL) is logical and addresses key challenges in the field.
- **Innovative Camera Control**: The introduction of E-PRoPE (Efficient PRoPE) is a strong contribution, offering a computationally efficient alternative to full PRoPE while maintaining high trajectory-following precision. The ablation study in Table 1 supports this claim.
- **Novel Evaluation Protocol**: The "Memory Evaluation via Revisit Consistency" section introduces a valuable metric suite (pixel, perceptual, semantic, place recognition, geometric) that goes beyond standard video quality metrics to specifically test long-horizon consistency, a critical gap in current benchmarks.
- **Strong Performance Claims**: The reported results on basic and long-horizon evaluations show significant improvements over baselines (HY-WorldPlay 1.5, LingBot-World) in camera control and artifact detection, particularly for a 5B parameter model.

## Concerns
- **Unverified and Future-Dated Citations**: The bibliography contains numerous citations dated 2025 and 2026 (e.g., `omniworldbench`, `hyworld2025`, `lingbotworld`, `megasam`). As this is a review of an arXiv-submitted paper, these references appear to be either pre-prints not yet publicly available, internal reports, or potentially hallucinated/future-dated entries. The evaluation results (Table 2, Table 3) rely heavily on these unverified benchmarks. Without access to the code or data for these benchmarks, the claims of outperforming them cannot be independently verified. This is a fundamental scientific flaw in the current state of the paper.
- **Reproducibility of Inference Speed**: The claim of "up to 16 FPS on eight RTX 5090 GPUs" is impressive but lacks necessary details. The paper does not specify the batch size, the exact resolution of the generated video (e.g., 720p, 1080p), or the specific parallelism strategy (tensor vs. pipeline) used to achieve this. The RTX 5090 is a future hardware model (as of the current date), making the claim difficult to contextualize or reproduce without further clarification on the hardware configuration and software stack.
- **Ambiguity in Memory Retrieval**: Section 5.2 describes "geometry-based retrieval" but lacks the algorithmic details required for reproduction. How are camera poses matched to history frames? What is the specific metric for "view overlap"? The mention of "RoPE embedding" for memory frames is vague. Without a clear algorithm or pseudo-code, the "Memory-Conditioned Scene Persistence" contribution is not fully reproducible.
- **Control Signal Conflicts**: The "Limitations" section acknowledges that "control signals like caption, camera and event may conflict," but the paper does not provide a mechanism or strategy for resolving these conflicts during generation. This is a significant gap in a system claiming "composable event control."
- **Self-Referential Benchmarks**: The evaluation relies on "Omni-WorldBench" and "WorldScore," which are cited as 2025/2026 papers. If these benchmarks were developed by the same team or are not yet public, the evaluation lacks external validity. The paper needs to either use established, public benchmarks or provide a fully open-source evaluation suite.

## Recommendation
The paper presents a compelling and technically sophisticated system for interactive world modeling. However, the scientific validity of the evaluation is currently compromised by the reliance on unverified, future-dated, or potentially self-referential benchmarks. The claims of outperforming state-of-the-art models cannot be substantiated without access to the underlying data and code for these benchmarks. Additionally, the reproducibility of the inference speed and memory retrieval mechanisms is insufficient.

I recommend **major_revision_science**. The authors must:
1.  Replace or verify all 2025/2026 citations with publicly available, peer-reviewed, or pre-print references.
2.  Provide a fully open-source evaluation suite or detailed instructions to reproduce the benchmark results.
3.  Clarify the hardware and software configuration for the 16 FPS claim.
4.  Detail the algorithm for geometry-based memory retrieval.
5.  Address the control signal conflict issue with a concrete solution or ablation study.

Once these scientific and reproducibility issues are resolved, the paper will be much stronger and ready for publication.
