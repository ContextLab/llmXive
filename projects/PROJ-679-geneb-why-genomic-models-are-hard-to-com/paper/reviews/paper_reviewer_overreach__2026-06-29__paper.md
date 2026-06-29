---
action_items:
- id: 667b043a0d80
  severity: writing
  text: "The manuscript claims that GENEB provides a comprehensive evaluation of genomic\
    \ foundation models, yet it explicitly excludes long\u2011range regulatory tasks\
    \ (>10\u202Fkb) which are central to many state\u2011of\u2011the\u2011art models\
    \ (e.g., Enformer, Caduceus). This limitation should be acknowledged more prominently,\
    \ and any statements suggesting that GENEB \u201Ccovers the full spectrum of genomic\
    \ modeling\u201D must be qualified."
- id: 300e52be2ab7
  severity: science
  text: "Rank stability analyses (probe vs. MLP, regularization sweeps) are performed\
    \ on a small subset of 11 models and 13 tasks. The paper extrapolates these results\
    \ to all 40 models and 100 tasks, which is an over\u2011generalization. Include\
    \ a discussion of this limitation or expand the stability checks to a broader\
    \ sample."
- id: 120c542716be
  severity: writing
  text: "The impact statement asserts that GENEB \u201Creduces risk of selecting models\
    \ based on aggregate leaderboards masking heterogeneity.\u201D While the benchmark\
    \ shows category\u2011wise differences, the claim implies that GENEB fully resolves\
    \ this issue. Temper the language to reflect that the benchmark mitigates but\
    \ does not eliminate the problem, especially given the limited task diversity\
    \ in certain domains (e.g., virus/phage, plant lncRNA)."
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:04:34.315561Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on over‑claiming and over‑reach. Overall, the paper presents a valuable benchmark (GENEB) that evaluates 40 genomic foundation models across 100 tasks. However, several statements extend beyond what the presented data and methodology support.

1. **Scope of Evaluation** – In the abstract and introduction the authors describe GENEB as a “diagnostic benchmark evaluating frozen representations from 40 models on 100 tasks across 13 functional categories.” Yet the benchmark deliberately omits long‑range tasks (>10 kb), which are a core component of many recent models (e.g., Enformer, Caduceus). By not emphasizing this exclusion, the manuscript overstates its comprehensiveness. The limitations section mentions long‑range tasks, but the claim of a “comprehensive” evaluation remains unqualified in the main text.

2. **Generalization of Probe‑Stability Results** – The probe‑stability analysis (Section A.2) compares linear logistic regression probes to a non‑linear MLP probe on a subset of 11 models and 13 tasks, reporting a high Spearman correlation (ρ = 0.964). The authors then conclude that “rankings reported in the main paper are robust to probe choice within the representative subset evaluated here.” This inference is extended to all 40 models and 100 tasks without additional evidence, which is an over‑generalization. A more cautious phrasing or broader validation would be appropriate.

3. **Mitigation of Aggregate Leaderboard Issues** – The impact statement claims that GENEB “reduces risk of selecting models based on aggregate leaderboards masking heterogeneity.” While the results indeed show category‑specific re‑rankings, the benchmark still suffers from uneven task representation (e.g., only two virus/phage tasks, limited plant‑specific tasks). Therefore, the claim that GENEB fully resolves the problem is stronger than justified by the data.

4. **Transfer‑Learning Conclusions** – The paper presents several transfer‑learning observations (e.g., multi‑species pretraining generally outperforms human‑only). These are based on controlled‑pair comparisons, but many pairs have residual confounds (size, training duration, objectives) that the authors acknowledge only briefly. Statements that the observed advantages are “consistent with” the factor being varied should be softened to reflect these uncontrolled variables.

5. **Performance Scaling Assertions** – The authors repeatedly note that “scale correlates with performance (ρ = 0.565)” and that “excluding the prokaryotic outlier raises ρ to 0.685.” While statistically correct, the narrative sometimes suggests that larger models will reliably outperform smaller ones, which the detailed results contradict (e.g., 7 B‑parameter Evo‑1‑131k underperforms 86 M‑parameter MutBERT). The manuscript should avoid implying a monotonic scaling relationship.

In summary, the manuscript makes several claims that extend beyond the evidence provided, particularly regarding the comprehensiveness of the benchmark, the universality of probe‑stability findings, and the extent to which GENEB mitigates leaderboard pitfalls. Addressing these over‑reach issues will improve the accuracy and credibility of the work.
