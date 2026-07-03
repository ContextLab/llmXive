---
action_items:
- id: 1b3fbf5d6aee
  severity: science
  text: The 19.3% compute cost claim compares 192K A100 hours to 314K H800 hours using
    peak TFLOPS (312 vs 989.5) without explicitly stating this calculation or accounting
    for utilization differences. Clarify the metric used to derive this percentage.
- id: 2417641b4995
  severity: writing
  text: The paper cites "GPT-4.1" and "GPT-5.5" for captioning and reasoning but provides
    no bibliography entries for these specific model versions. Add citations or clarify
    if these are internal/unreleased models to ensure verifiability.
- id: 4c2e0b7449a7
  severity: science
  text: The "Lens-800M" dataset claim (800M pairs) lacks a specific data card or repository
    link in the text. Provide a citation or link detailing the dataset construction
    and captioning source to validate the scale claim.
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:29:49.836765Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several strong factual claims regarding model performance, compute efficiency, and dataset scale that require tighter alignment with provided evidence and citations.

First, the central efficiency claim in the Abstract and Introduction states that Lens requires "only about 19.3% of the training compute used by Z-Image." The text supports this by comparing "192K A100 GPU hours" to "314K H800 GPU hours" and listing peak TFLOPS (312 vs 989.5). However, the calculation `192 * 312 / (314 * 989.5)` yields approximately 19.3%, but the paper does not explicitly state that it is using peak TFLOPS as the proxy for actual training compute, nor does it account for potential differences in GPU utilization rates or memory bandwidth bottlenecks between A100 and H800 clusters. While the math holds for peak theoretical throughput, presenting this as a definitive "compute cost" without clarifying the metric (peak FLOPS vs. actual measured FLOPS) is slightly overstated.

Second, there are significant citation gaps regarding the specific LLM versions used. The text repeatedly references "GPT-4.1" for data captioning and rubric generation, and "GPT-5.5" for the reasoner module and prompt search. The bibliography (`references.bib`) includes `openai2025gptoss120bgptoss20bmodel` but lacks any entry for GPT-4.1 or GPT-5.5. If these are proprietary models not yet publicly documented with a technical report, the claim that they were used is unverifiable by the reader. If they are hypothetical or internal versions, the paper should clarify their status or provide a citation to the specific model card. The use of "GPT-5.5" as a default reasoner is particularly notable given the lack of a corresponding reference.

Third, the "Lens-800M" dataset is described as containing 800M pairs with GPT-4.1 captions. While the paper describes the cleaning pipeline (referencing EVA, SigLIP2, etc.), it does not provide a specific citation for the dataset itself or the captioning results. For a dataset of this magnitude, a data card or a specific repository link detailing the 800M count and the exact prompt engineering used for GPT-4.1 is essential to validate the "data information density" claim.

Finally, the claim that the model generalizes to aspect ratios 1:2 to 2:1 and resolutions up to 1440^2 "without explicit training" (Section 3.3) is supported by the architecture description (RoPE, mixed-resolution training), but the specific ablation or test set results demonstrating this generalization to *unseen* ratios are only referenced as figures. The claim is plausible but relies heavily on the visual evidence in the figures which cannot be numerically verified in this text-only review.

Overall, the paper's core scientific claims are plausible but suffer from missing citations for key components (GPT-4.1, GPT-5.5) and a lack of explicit calculation details for the compute efficiency metric.
