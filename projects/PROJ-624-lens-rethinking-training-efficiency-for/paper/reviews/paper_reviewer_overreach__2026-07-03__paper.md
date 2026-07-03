---
action_items:
- id: 214ffa71fb95
  severity: science
  text: The claim that Lens achieves '19.3% of the training compute' of Z-Image (Abstract,
    Intro) conflates GPU-hours with FLOPs without providing the specific FLOP counts
    or hardware efficiency factors for both models. The comparison of 192K A100 hours
    vs. 314K H800 hours is not directly additive without a normalized TFLOP-hour calculation,
    which is currently missing.
- id: acb436093aee
  severity: writing
  text: The statement that the model 'generalizes to aspect ratios 1:2 to 2:1 and
    resolutions up to 1440^2' (Abstract, Intro) implies a hard boundary or guaranteed
    performance at these limits. The text should clarify if 1440^2 is the tested maximum
    or a theoretical extrapolation, and whether performance degrades significantly
    at the edges of this range compared to the training distribution.
- id: 9ebac8c3165c
  severity: writing
  text: The claim that 'Strong language encoders... enable multilingual generalization
    from English-only training' (Intro) is a strong causal assertion. The paper admits
    in limitations that multilingual performance is 'lower than English' and struggles
    with non-English text rendering. The text should be tempered to reflect that the
    encoder aids *comprehension* of multilingual prompts but does not fully solve
    the *generation* of non-English text without specific training data.
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:30:11.398206Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript makes several aggressive claims regarding training efficiency and generalization that slightly exceed the immediate evidence provided in the text.

First, the central efficiency claim in the Abstract and Introduction states that *Lens* requires "only about 19.3% of the training compute used by Z-Image." This figure is derived by comparing 192K A100 GPU hours against 314K H800 GPU hours. However, the paper does not provide the specific FLOP counts per hour for the A100 vs. H800 configurations used, nor does it normalize for the architectural differences (e.g., memory bandwidth, tensor core efficiency) that would affect the actual TFLOP-hours consumed. Without a normalized "compute cost" metric (e.g., total FLOPs), the 19.3% figure is an extrapolation based on raw time rather than a verified computational cost. The authors should either provide the normalized FLOP calculation or qualify the claim to refer specifically to "wall-clock time on the specified hardware" rather than "training compute."

Second, the claim that the model "generalizes to... resolutions up to 1440^2" (Abstract, Section 1) suggests a robust capability at this specific resolution. While the paper mentions training on lower resolutions, it does not explicitly state whether 1440^2 was the upper bound of the *tested* generalization or a theoretical limit. If 1440^2 was the maximum resolution tested, the phrasing "up to" is acceptable but should be supported by a specific benchmark result or qualitative example at that exact resolution in the main text (currently, the teaser figure caption mentions 1440 resolution, but the specific performance metrics at this exact resolution are not detailed in the tables). If the model was not explicitly tested at 1440^2, this is an over-extrapolation.

Finally, the assertion that strong language encoders "enable multilingual generalization from English-only training" (Section 1) is partially contradicted by the "Limitations" section, which admits the model "struggles with visual text rendering in non-English languages" and has lower accuracy. While the encoder may help the model *understand* multilingual prompts, the claim of "generalization" implies a level of output fidelity that the limitations section suggests is not fully achieved. The text should be refined to distinguish between "prompt understanding" (which the encoder aids) and "text rendering" (which remains a limitation).
