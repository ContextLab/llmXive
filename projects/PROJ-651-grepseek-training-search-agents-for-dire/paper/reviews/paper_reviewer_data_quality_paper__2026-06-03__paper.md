---
action_items:
- id: 5ca275328cf8
  severity: writing
  text: Explicitly state data licenses for Wikipedia (CC-BY-SA) and QA benchmarks
    (e.g., NQ non-commercial) in Section 4.1 and Appendix A.
- id: 52ce1309fab2
  severity: writing
  text: Specify exact Wikipedia snapshot revision ID or date (e.g., 2018-01-01) instead
    of generic '2018 dump' in Section 4.1.
- id: e06387772c18
  severity: writing
  text: Archive code and dataset URLs (e.g., GitHub, HuggingFace) via Zenodo or similar
    and include persistent DOIs to prevent link rot.
artifact_hash: 5d85c06c69d8e12a9cf2281b0d8f94964a15c102cc7625c442c21ea4362e7831
artifact_path: projects/PROJ-651-grepseek-training-search-agents-for-dire/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T19:45:49.587016Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript lacks critical data provenance and licensing details required for reproducibility and legal compliance. Specifically, Section 4.1 ("Experimental Setup") and Appendix A ("Datasets") enumerate resources like the 2018 Wikipedia dump, NQ, and TriviaQA but omit license terms. Wikipedia content is typically CC-BY-SA, while QA benchmarks often have non-commercial research restrictions. Explicitly stating these licenses is mandatory for any redistribution or derivative work claims. Without this, the legal status of the released code and synthetic data is ambiguous.

Secondly, the "2018 Wikipedia dump" (Section 4.1) is too vague for exact reproducibility. Provide the specific snapshot date (e.g., `2018-01-01`) or revision hash. Small changes in Wikipedia over time can significantly impact retrieval performance metrics, making version specificity essential for scientific rigor. The current citation to `karpukhin2020dense` does not guarantee the exact corpus state used.

Thirdly, external URLs (e.g., `https://github.com/alirezasalemi7/grepseek` in the Introduction; HuggingFace links in Section 4.1) are prone to link rot. Recommend archiving these artifacts via Zenodo or similar services and including persistent DOIs in the bibliography. Reliance on volatile URLs risks the paper becoming unreplicable within a few years.

Finally, the cold-start trajectory generation pipeline (Section 3.1.1) creates synthetic data using Tutor and Planner models. A schema definition or "datasheet" for this synthetic data is missing. Describing the distribution, filtering criteria (e.g., $F_1 > 0$), and potential biases of this synthetic corpus is necessary to evaluate the robustness of the RL training. These issues are fixable via text updates but are critical for a data-centric contribution.
