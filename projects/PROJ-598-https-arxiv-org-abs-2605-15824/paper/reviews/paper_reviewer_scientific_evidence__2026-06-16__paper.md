---
action_items:
- id: 1e24b2aa8e44
  severity: science
  text: The manuscript reports quantitative metrics (e.g., Cur., GME, FPS) without
    any measure of variability (standard deviation, confidence intervals) or statistical
    significance testing, making it impossible to assess whether observed differences
    are robust or could arise by chance.
- id: 604adaf7e3d5
  severity: science
  text: "FPS comparisons claim a 30\u2013180\xD7 speedup over baselines, yet the paper\
    \ does not disclose hardware\u2010specific configurations (e.g., batch size, precision\
    \ mode) for the baselines, nor does it provide raw timing logs. Without a controlled\
    \ benchmarking protocol, the speedup claim remains unverified."
- id: 868cd89e564e
  severity: science
  text: "Ablation tables (e.g., Table\u202F2, Table\u202F3) present single scalar\
    \ values per variant, but there is no indication of how many runs were performed\
    \ or whether the results are averaged. Replication details (random seeds, variance)\
    \ are missing, raising concerns about result stability."
- id: d60622129e32
  severity: science
  text: "The user study reports 672 valid responses, yet the demographic breakdown,\
    \ randomization of video presentation order, and statistical analysis (e.g., ANOVA\
    \ or post\u2011hoc tests) are absent. This hampers evaluation of the external\
    \ validity of the subjective findings."
- id: 5e1fac481ba8
  severity: science
  text: "The training dataset size (\u2248\u202F62\u202FK triplets) is mentioned,\
    \ but the paper does not provide a power analysis or justification that this sample\
    \ size is sufficient to support the claimed generalization to diverse garment\
    \ categories. A discussion of potential sampling bias is needed."
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T03:31:39.613536Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper introduces **FashionChameleon**, a real‑time, autoregressive framework for garment‑level video customization, and reports impressive metrics such as 23.8 FPS generation and superior scores on a suite of quality measures (Cur., GME, VQ, etc.). While the quantitative tables (e.g., Table 1) show that the proposed method outperforms several baselines on most metrics, the evidence lacks the statistical rigor needed to substantiate these claims. No standard deviations, confidence intervals, or hypothesis‑testing results accompany the reported numbers, leaving the reader unable to judge whether the improvements are statistically significant or merely within the noise floor of the evaluation pipeline.

The speedup claim (30–180× faster than baselines) is particularly vulnerable because the manuscript does not detail the exact hardware settings, batch sizes, or precision modes used for each baseline during FPS measurement. Without a standardized benchmarking protocol, differences in implementation or optimization could account for much of the observed gap. Providing raw timing logs and ensuring that all methods are evaluated under identical conditions would greatly strengthen this claim.

Ablation studies are presented as single rows of metric values, but the methodology for these experiments is opaque. It is unclear whether each variant was run multiple times with different random seeds, or whether the reported numbers are averages. Replicability would be improved by reporting the number of runs, seed values, and variability metrics. Similarly, the user study, despite a respectable sample size (672 responses), omits crucial details such as participant demographics, randomization of video order, and statistical analyses (e.g., ANOVA). These omissions prevent assessment of potential biases and the generalizability of the subjective findings.

Finally, the training data curation pipeline yields 62 K triplets, yet the paper provides no justification that this volume is sufficient for the diversity of garment types claimed. A power analysis or at least a discussion of sampling bias would help readers evaluate the robustness of the model’s generalization to unseen garments. Addressing these evidential gaps—by adding variability measures, controlled benchmarking details, replication protocols, and statistical analyses—will make the central claims of the work substantially more credible.
