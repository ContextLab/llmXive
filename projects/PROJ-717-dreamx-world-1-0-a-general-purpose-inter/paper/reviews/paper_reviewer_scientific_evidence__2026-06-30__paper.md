---
action_items:
- id: ee7fde2df8c8
  severity: science
  text: "The evaluation section lacks critical statistical rigor. Table 1 and Table\
    \ 2 report single-point scores without standard deviations, confidence intervals,\
    \ or sample sizes (N) for the evaluation sets. Without N and variance, the claimed\
    \ superiority (e.g., 84.76 vs 80.79) cannot be statistically validated. Please\
    \ report N, mean \xB1 std, and p-values for all comparative metrics."
- id: dc1c03f97604
  severity: science
  text: The 'Artifact Detection Metric' relies on a single VLM (Gemini-3.1-Pro) evaluated
    twice per video. This introduces high risk of model-specific bias and hallucination.
    The methodology lacks inter-rater reliability checks (e.g., human-VLM agreement
    or multi-model consensus) and does not define the prompt engineering or temperature
    settings used, making the results irreproducible.
- id: a86efe2f82ec
  severity: science
  text: The memory consistency evaluation (Table 3) reports 'gain-based' scores (revisit
    minus baseline) but fails to specify the baseline distribution size or the statistical
    test used to determine if these gains are significant. The claim of 'stronger
    memory at every level' is unsupported without significance testing against the
    baselines.
- id: 0961da804ff2
  severity: science
  text: The human preference study (Section 4.4) reports percentages (e.g., 57.5%
    win rate) but omits the total number of human judgments (N) and the statistical
    significance of the win rates against the null hypothesis (50%). A win rate of
    57.5% with N=20 is not statistically distinguishable from chance, whereas N=2000
    would be. This data is essential to validate the claim of 'preference'.
artifact_hash: dd358f57d42e68a3445f4b34d5b2202a60d20e2d68878dcf007801dde467660f
artifact_path: projects/PROJ-717-dreamx-world-1-0-a-general-purpose-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T05:19:13.594113Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The paper presents a sophisticated system for interactive world modeling, but the scientific evidence supporting its central claims of superiority is currently insufficient due to a lack of statistical rigor and reproducibility details in the evaluation section.

First, the quantitative results in Tables 1, 2, and 3 are presented as single scalar values without any measure of variance (standard deviation) or sample size (N). In generative modeling, performance can fluctuate significantly based on random seeds, prompt sampling, or specific test set composition. Claiming that DreamX-World (84.76) outperforms HY-WorldPlay (80.79) is statistically meaningless without knowing the variance of these scores or the number of test samples. The authors must report N, mean ± std, and perform significance testing (e.g., t-tests or bootstrap confidence intervals) to substantiate these comparisons.

Second, the "Artifact Detection Metric" relies entirely on a single proprietary VLM (Gemini-3.1-Pro) with a binary pass/fail output. This approach is highly susceptible to model-specific biases and hallucinations. The paper does not provide the prompts used, the temperature settings, or any validation of the VLM's accuracy against human ground truth. Furthermore, evaluating each video only twice is a low sample size for a binary classifier, leading to high variance in the estimated pass rate. A robust evaluation would require multiple VLMs, human verification of a subset, or a more objective, code-based metric for structural artifacts.

Third, the memory consistency evaluation introduces a "gain-based" scoring system but fails to define the baseline distribution or the statistical significance of the reported gains. The claim that the model achieves "stronger memory at every level" is an overstatement without p-values indicating that the observed gains are not due to random chance.

Finally, the human preference study reports win/tie/loss percentages but omits the total number of human judgments (N). Without N, it is impossible to determine if the observed win rates (e.g., 57.5%) are statistically significant or merely noise. The authors must disclose the sample size and the statistical methods used to analyze the human study results.

Until these statistical gaps are addressed, the central claims regarding the model's superior performance and memory capabilities remain unsupported by robust scientific evidence.
