---
action_items:
- id: c1dc56cbe8a8
  severity: science
  text: "The scientific evidence supporting the central claims of this paper is currently\
    \ insufficient due to missing statistical controls and potential confounding variables\
    \ in the experimental design. First, the most significant claim\u2014that the\
    \ model generalizes to 256K and 512K contexts without adaptation (Section 6, Table\
    \ 2)\u2014is supported only by point estimates. Long-context performance is notoriously\
    \ unstable and sensitive to positional encoding interpolation and sampling noise.\
    \ The absence of multip"
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:45:43.557402Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the central claims of this paper is currently insufficient due to missing statistical controls and potential confounding variables in the experimental design.

First, the most significant claim—that the model generalizes to 256K and 512K contexts without adaptation (Section 6, Table 2)—is supported only by point estimates. Long-context performance is notoriously unstable and sensitive to positional encoding interpolation and sampling noise. The absence of multiple random seeds, error bars, or confidence intervals makes it impossible to verify if the observed gains over the baseline are robust or artifacts of a specific evaluation run. A single evaluation pass is not scientifically rigorous for such a high-stakes claim.

Second, the ablation study on sequence-length distribution (Section 5.1) suffers from a confounding variable. The 'long-biased' distribution not only changes the length profile but also drastically increases the average sequence length (83.9% of samples > 100K tokens vs. 23.6% in 'pool-native'). This change in distribution likely alters the effective number of gradient updates per epoch and the memory pressure during training, which are known to affect convergence. The paper attributes the performance difference solely to 'length diversity' without controlling for these training dynamics (e.g., by normalizing the number of steps or total tokens processed per epoch).

Third, the comparison between VQA and OCR training tasks (Section 4, Table 1) is methodologically flawed. The authors compare VQA-trained models directly against OCR-trained models that underwent an *additional* 5B-token SFT stage (rows labeled 'SFT'). This introduces a massive confounder: the superior performance of VQA could be due to the task format itself, or simply because the OCR models were not given the same instruction-tuning exposure. To isolate the effect of the pre-training task, the authors must either apply the same SFT stage to the VQA models or remove the SFT stage from the OCR models.

Finally, the claim regarding the preservation of short-context capabilities (Section 5.3) relies on a marginal difference (66.47 vs. 65.48) without reporting variance. Without standard deviations or statistical significance testing, this difference cannot be distinguished from evaluation noise. The paper must provide these statistical details to substantiate the claim that short-context capabilities are 'largely preserved' rather than just 'not catastrophically forgotten.'

These issues require re-running experiments with proper statistical controls and variance reporting before the claims can be considered scientifically valid.
