---
action_items:
- id: 960d9bdc1c48
  severity: science
  text: In Table 1 (ASR results), report confidence intervals or standard deviations
    for the error rates (CER/WER) across the 100+ test clips. Point estimates alone
    do not convey the statistical significance of the marginal improvements (e.g.,
    0.06 absolute points) claimed to be 'essentially unchanged'.
- id: f06246c1af51
  severity: science
  text: The TTS evaluation (content/tts.tex) relies on an 'arena-style' win rate of
    67.6% against three baselines. The text mentions 774 prompts but omits the sample
    size per model pair, the specific statistical test used (e.g., binomial test,
    Bradley-Terry), and the resulting p-values or confidence intervals to support
    the claim of 'consistent gains'.
- id: 777435f29c1a
  severity: science
  text: In the Realtime evaluation (content/realtime.tex), the subjective human evaluation
    score (80.41) is compared to baselines without reporting the number of human raters,
    the inter-rater reliability (e.g., Krippendorff's alpha), or the statistical significance
    of the reported +10.0 margin.
artifact_hash: 88c34566a338d5ce01bdd1f1a7a5589647e4fe5286433548c997e1603e2b9886
artifact_path: projects/PROJ-622-https-arxiv-org-abs-2605-23463/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:27:05.037896Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive technical report on the StepAudio 2.5 model family, but the statistical rigor of the evaluation sections requires strengthening to support the claims of state-of-the-art performance.

In the ASR section (content/asr.tex), Table 1 presents point estimates for Character Error Rate (CER) and Word Error Rate (WER) across multiple benchmarks. While the authors note that MTP training leaves accuracy "essentially unchanged" with fluctuations "within 0.06 absolute points," no measure of variance (standard deviation) or confidence intervals is provided. Given the high stakes of these marginal differences, the absence of statistical significance testing (e.g., paired t-tests or bootstrap confidence intervals) makes it difficult to distinguish genuine stability from random noise. The claim that the model "outperforms competitive baselines" on specific subsets (e.g., LibriSpeech clean) lacks the necessary statistical context to confirm these are not outliers.

The TTS evaluation (content/tts.tex) relies heavily on an arena-style pairwise comparison, reporting a 67.6% win rate. However, the text fails to specify the statistical methodology used to aggregate these results. It is unclear if the 774 prompts were distributed equally across all model pairs, nor is there a mention of the statistical test (e.g., binomial test against a null hypothesis of 50%) or the resulting p-value. Without confidence intervals for the win rate, the claim of "consistent gains" remains descriptive rather than statistically validated.

Similarly, the Realtime evaluation (content/realtime.tex) reports a subjective human evaluation score of 80.41, claiming a +10.0 margin over the next-best system. The review lacks critical metadata regarding the human evaluation protocol: the number of independent raters, the method for calculating the final score (mean, median?), and measures of inter-rater reliability. Without these details, the statistical robustness of the subjective claims cannot be assessed.

To meet the standards of a technical report, the authors should supplement point estimates with confidence intervals, report p-values for key comparisons, and explicitly state the statistical tests and sample sizes used in the evaluation protocols.
