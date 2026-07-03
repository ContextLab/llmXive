---
action_items:
- id: a56473a33ae6
  severity: science
  text: The scaling law analysis in Sec. 5.1 lacks statistical rigor. The text claims
    'marginal gains decrease' but provides no confidence intervals, standard errors,
    or p-values for the differences between the 200M and 2B token runs. Without error
    bars or multiple seeds, the observed trend could be noise. Please report variance
    across seeds or statistical significance tests.
- id: 8caf910e91d7
  severity: science
  text: The real-world evaluation in Sec. 4.3 relies on only four specific dance motions
    for quantitative metrics. This sample size is insufficient to support the broad
    claim of 'unprecedented zero-shot generalization' to 'diverse, complex' motions.
    Please expand the test set to include a statistically significant number of unseen
    motion categories or provide a power analysis justifying the current sample size.
- id: 6be7d9954df7
  severity: science
  text: The comparison with baselines in Table 2 is confounded by data scale. Baselines
    are trained on ~6-9M frames, while Humanoid-GPT uses 2B frames. The paper attributes
    gains to architecture but does not isolate the effect by comparing a Transformer
    trained on 9M frames against an MLP trained on 9M frames. The claim that 'Transformers
    offer superior tracking precision' is not fully supported without this controlled
    ablation.
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:28:35.965354Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling narrative on scaling data and model capacity for humanoid motion tracking, supported by extensive engineering and a large-scale dataset. However, from a strict scientific evidence perspective, the statistical robustness of the central claims requires strengthening.

First, the **scaling law analysis** (Sec. 5.1, lines 430-445) presents a clear trend in performance metrics (MPJPE, SR) as data increases from 2M to 2B tokens. However, the evidence is purely point-estimate based. There is no mention of the number of random seeds used for training, nor are there error bars, standard deviations, or confidence intervals reported in Table 2 or Fig. 4. In deep learning, performance can vary significantly between seeds, especially at the extremes of the scaling curve. Without reporting variance or conducting statistical significance tests (e.g., t-tests) between the 200M and 2B token configurations, the claim that the marginal gains are "real" rather than stochastic noise is weak. The authors must provide variance metrics or re-run experiments with multiple seeds to substantiate the scaling law.

Second, the **real-world generalization claim** relies on a very small test set. Table 3 (lines 280-310) reports quantitative metrics for only four specific dance sequences. While the qualitative videos (Fig. 3, Fig. 5) show a variety of motions, the quantitative evidence for "zero-shot generalization" is limited to these four clips. A sample size of four is statistically insufficient to claim robust generalization across "diverse, complex" unseen motions. The authors should either expand the real-world test set to include a larger, diverse collection of unseen motions (e.g., 20-50 clips across different categories) or explicitly frame the quantitative results as preliminary case studies rather than definitive proof of generalization.

Third, the **attribution of performance gains** to the Transformer architecture is confounded by the massive difference in training data. The baselines (GMT, TWIST, Any2Track) are trained on ~6-9M frames, whereas Humanoid-GPT is trained on 2B frames (Table 1, lines 130-150). The paper argues that the Transformer scales better than MLPs, but the primary comparison is between a 2B-frame Transformer and a 9M-frame MLP. To isolate the architectural contribution, the authors need an ablation study comparing a Transformer and an MLP trained on the *same* amount of data (e.g., both on 9M frames, or both on 2B frames if feasible). Without this, the claim that the Transformer is the primary driver of the performance leap, rather than the sheer volume of data, remains an unproven hypothesis.

Finally, the **diversity metrics** (Sec. 4.2, lines 230-260) rely on HME embeddings and covariance volume. While the methodology is sound, the paper does not provide a baseline for what constitutes a "good" log-volume or gstd, nor does it correlate these specific diversity metrics directly with the final tracking success rate in a regression analysis. The claim that "diversity and balance are both necessary" is qualitative; a quantitative correlation would strengthen the evidence.

In summary, while the engineering achievement is significant, the scientific evidence supporting the specific claims about scaling laws, architectural superiority, and generalization robustness needs more statistical depth and controlled ablations.
