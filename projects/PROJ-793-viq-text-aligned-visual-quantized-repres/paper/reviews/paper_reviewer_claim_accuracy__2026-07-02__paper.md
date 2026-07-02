---
action_items:
- id: 1dc6cce86755
  severity: science
  text: Claim in 'Image Reconstruction' that ViQ 'ranks first among mainstream discrete
    visual autoencoders' is false. Table 2 shows UniTok has higher PSNR (25.32 vs
    22.73) and lower rFID (0.37 vs 0.62). Correct the ranking claim.
- id: d2046fa5b6a5
  severity: writing
  text: "Claim that JPEG requires Q\u22480.08 to match ViQ's compression ratio is\
    \ unsupported. No citation or data validates this specific quality factor. Remove\
    \ the specific number or provide evidence."
- id: eac060e7482e
  severity: writing
  text: Ablation text claims Case B has 'unsatisfactory performance on OCR/Chart'
    but Table 5 only shows aggregate scores. Clarify that this observation comes from
    full benchmark results (Table 1), not the ablation table alone.
artifact_hash: b0d13f79598805d86a50b3ae742d6ff735642238ad128fe0a6c96ca6ef0ec5e0
artifact_path: projects/PROJ-793-viq-text-aligned-visual-quantized-repres/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:07:38.228149Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their support by the provided evidence.

**Factual Error in Reconstruction Ranking:**
In the "Image Reconstruction Experiments" section (sec/4-Experiments.tex), the authors state: "ViQ... achieves a PSNR of 22.73 and an rFID score of 0.62, **ranking first among mainstream discrete visual autoencoders**."
This claim is directly contradicted by **Table 2** in the same section. The table lists **UniTok** (a discrete tokenizer) with a PSNR of **25.32** and an rFID of **0.37**. Both metrics are superior to ViQ's results. Therefore, ViQ does *not* rank first; it ranks second in rFID and third in PSNR among the listed discrete tokenizers. The claim of "ranking first" is factually incorrect based on the paper's own data.

**Unsupported Numerical Assertion:**
In the "Storing Any Image as Discrete Codes" subsection, the authors claim: "matching the same compression ratio with JPEG would require an aggressive quality setting (e.g., $Q\approx0.08$) that noticeably degrades image quality."
While the compression ratio calculation (1/96) is mathematically consistent with the provided bit-depth assumptions, the specific assertion that JPEG requires a quality factor of approximately 0.08 to achieve this ratio is **unsupported**. No citation or empirical data is provided to validate this specific $Q$ value. This is a precise numerical claim that requires evidence.

**Logical Gap in Ablation Interpretation:**
In the "Ablation Studies" section, the text states that Case B (Text + Distill) has "unsatisfactory performance on tasks such as OCR and Chart." However, **Table 5** only reports an aggregate score (avg.(2-2)). The specific performance on OCR and Chart is not broken down in this table. While this observation is likely derived from the full results in Table 1, the text presents it as a direct conclusion from the ablation table without explicitly referencing the full benchmark breakdown, creating a minor logical gap in the immediate support for the claim.

**Conclusion:**
The paper contains a significant factual error regarding the ranking of ViQ in reconstruction metrics compared to other discrete tokenizers (specifically UniTok). Additionally, a specific numerical claim about JPEG quality settings lacks support. These issues require correction to ensure the accuracy of the claims.
