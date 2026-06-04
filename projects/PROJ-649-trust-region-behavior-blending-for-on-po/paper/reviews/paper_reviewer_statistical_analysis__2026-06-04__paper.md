---
action_items:
- id: 2d8787e007a4
  severity: science
  text: Clarify the number of random seeds used for training runs. Appendix A does
    not specify if results are averaged over seeds, which is critical for statistical
    validity.
- id: 72196be2a5b4
  severity: science
  text: Report variance (standard deviation) or confidence intervals for benchmark
    scores in Table 1. Point estimates alone do not support claims of statistical
    superiority.
- id: e6bd79f920e6
  severity: science
  text: Address checkpoint selection bias in Section 5.1. Selecting the best checkpoint
    per method inflates performance; compare at fixed steps or use a held-out validation
    set.
- id: 8518dc497df1
  severity: science
  text: Justify evaluation sample sizes (e.g., n=32 for GSM8K). Smaller sample sizes
    increase variance in pass@1 estimates; ensure sufficient power for comparisons.
artifact_hash: a0fcc4014c0149719a56a0fd8c9438fb07408db2050a8ea923c6bb42f703660e
artifact_path: projects/PROJ-649-trust-region-behavior-blending-for-on-po/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T21:39:11.257154Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

## Statistical Analysis Re-Review

None of the four prior action items from my previous review have been addressed in the current revision.

**1. Random Seeds (ID: 2d8787e007a4)**
Appendix A (Experimental Details, lines 275-310) lists hyperparameters but does not specify the number of random seeds used for training runs. The paper reports single point estimates without indicating whether results are averaged across multiple seeds. This is critical for statistical validity in deep learning experiments where training stochasticity can significantly affect outcomes.

**2. Variance Reporting (ID: 72196be2a5b4)**
Table 1 (lines 174-191) reports pass@1 scores as single values (e.g., "33.2", "69.7") without any measure of variance (standard deviation, standard error, or confidence intervals). Without variance estimates, claims of statistical superiority between methods cannot be validated. The differences between TRB (33.2) and Vanilla OPD (32.3) on the 1.7B-8B setup may not be statistically significant.

**3. Checkpoint Selection Bias (ID: e6bd79f920e6)**
Section 5.1 (lines 158-160) explicitly states: "report the checkpoint with the highest setup-specific mean score." This selection protocol inflates performance estimates and introduces bias. The paper should either compare methods at fixed training steps or use a held-out validation set for checkpoint selection.

**4. Sample Size Justification (ID: 8518dc497df1)**
Appendix A (lines 323-327) specifies evaluation sample sizes (32 for GSM8K, 64 for MATH500, 512 for AIME) but provides no power analysis or justification for these choices. With n=32 on GSM8K, pass@1 estimates have substantial variance that could obscure meaningful differences between methods.

These issues remain unaddressed and must be resolved before the statistical claims can be considered valid.
