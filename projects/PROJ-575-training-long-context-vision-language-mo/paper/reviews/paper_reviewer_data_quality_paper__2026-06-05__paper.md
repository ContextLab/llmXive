---
action_items:
- id: 9761681d5981
  severity: science
  text: Specify the license and source of the 1.5M PDF document pool (Sec 4.1).
- id: ae7a9a693dea
  severity: science
  text: Clarify handling of 3% noisy QA pairs from human verification (Appx A.3).
- id: 97c065b3a45d
  severity: writing
  text: Provide data release link or reconstruction instructions for synthetic data.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T10:59:13.238350Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a systematic study of long-context continued pre-training (LongPT) for vision-language models. From a data quality perspective, the data curation methodology is detailed, but critical provenance and compliance information is missing.

**Data Provenance and Licensing (Section 4.1):**
The authors state they constructed a pool of over 1.5 million PDF documents (Section 4.1, Appendix A.1). However, the source of these documents and their associated licenses are not specified. For reproducibility and legal compliance, the paper must explicitly state whether this corpus is from public repositories (e.g., arXiv, CommonCrawl) or proprietary sources. If copyrighted material was used, the paper needs to justify the legal basis for training and potential model release. The short-context data (LLaVA-OneVision) is properly cited with Hugging Face links (Appendix A.5), but the primary long-context corpus lacks this transparency.

**Data Quality and Noise (Appendix A.3):**
Human verification of 100 generated QA pairs revealed a 3% error rate (2 incorrect answers, 1 inaccurate evidence annotation). While the paper acknowledges this noise, it does not specify how this imperfect supervision is handled during training. Was the noisy data filtered? Was a robust loss function used? Without this information, it is unclear if the 3% noise impacts model convergence or generalization. This is a data quality control gap.

**Reproducibility and Link Rot:**
The synthetic data generation pipeline is described with prompt templates (Appendix A.3), but the raw document pool is not released. If the pool cannot be shared due to copyright, the authors should provide a script or detailed instructions for reconstructing a similar corpus from public sources. Currently, the "constructed pool" acts as a black box, hindering independent verification of the data distribution claims.

To meet data quality standards for publication, the authors must address the licensing of the document pool, clarify the treatment of noisy training examples, and ensure external data links are versioned to prevent link rot.
