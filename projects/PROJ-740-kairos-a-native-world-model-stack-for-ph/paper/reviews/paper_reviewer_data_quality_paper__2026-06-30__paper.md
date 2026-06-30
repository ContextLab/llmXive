---
action_items:
- id: 35e0a3b19349
  severity: fatal
  text: The 'Data Collection' section (e001) claims to use 'internet-crawled videos'
    and 'proprietary data' but fails to specify the legal basis for processing, the
    specific licenses of the open-source datasets (e.g., Koala-36M, AgiBotWorld-Beta),
    or the terms of service for the crawled content. Without explicit license declarations
    and provenance documentation, the dataset's reproducibility and legal compliance
    cannot be verified.
- id: b55a115219ee
  severity: science
  text: The paper references external URLs for datasets and models (e.g., https://github.com/kairos-agi/kairos-sensenova,
    https://huggingface.co/kairos-agi) in the summary and text. There is no evidence
    of version pinning (e.g., commit hashes, specific release tags) or a manifest
    file listing the exact data versions used. This creates a high risk of link rot
    and non-reproducibility as these resources may change or disappear.
- id: b93f0a1cac03
  severity: science
  text: The 'Data Curation' section (e001) describes a complex filtering pipeline
    (Aesthetic, Motion, NSFW, etc.) but does not provide the specific threshold values,
    model versions, or configuration files used for these filters. The 'Shot Detection'
    table (e000) lists a recall rate of 77.44% but does not define the ground truth
    used to calculate this metric, making the data quality claims unverifiable.
- id: eb9718882d6c
  severity: writing
  text: The paper mentions 'hundreds of millions of standardized video clips' and
    'millions of hours' of data but lacks a detailed schema or data card describing
    the distribution, missing data handling strategies, or the exact composition of
    the training set (e.g., split ratios between open-source and proprietary data).
artifact_hash: 926e7dfe86ab0c8e4b8d20a90a842eec681ad7b82ae76075a7b3082533c6260d
artifact_path: projects/PROJ-740-kairos-a-native-world-model-stack-for-ph/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T11:53:35.722875Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The review focuses strictly on data quality, provenance, licensing, and reproducibility.

**Data Provenance and Licensing (Fatal):**
The manuscript fails to meet basic standards for data provenance. In the "Data Collection" section (e001), the authors state they use "internet-crawled videos" and "proprietary data" alongside open-source datasets like Koala-36M and AgiBotWorld-Beta. However, the paper provides no information regarding the licenses of these datasets, the specific terms of service for the crawled content, or the legal basis for processing this data. For a paper claiming to establish a "foundational infrastructure," the absence of a clear license declaration (e.g., CC-BY, Apache 2.0, or specific proprietary restrictions) and a detailed data card is a critical failure. Without this, the dataset cannot be legally or ethically reproduced or audited.

**Version Control and Link Rot (Science):**
The paper relies heavily on external resources, citing URLs such as `https://github.com/kairos-agi/kairos-sensenova` and `https://huggingface.co/kairos-agi` without any version pinning. There are no commit hashes, release tags, or snapshot dates provided. In the rapidly evolving field of AI, these links are highly susceptible to "link rot" or content drift. If the repositories are updated or deleted, the specific data and code required to reproduce the results will be lost. A robust data quality review requires a manifest or a `requirements.txt`-style file for data assets, which is entirely missing.

**Schema and Missing Data Handling (Science/Writing):**
The "Data Curation" section (e001) outlines a multi-stage filtering pipeline (Aesthetic, Motion, NSFW, etc.) but lacks the necessary schema details to verify these claims. The specific threshold values for the filters (e.g., the exact CLIP score cutoff for "low visual quality") are not provided. Furthermore, the "Shot Detection" table (e000) reports a recall rate of 77.44% but does not specify the ground truth dataset or methodology used to derive this metric. The paper also mentions "hundreds of millions" of clips but does not provide a schema describing the data structure, how missing data (e.g., corrupted frames) was handled, or the exact distribution of the final training set.

**Conclusion:**
The paper's claims regarding data quality and scale are unsupported by the necessary documentation. The lack of licensing information, version control, and detailed curation parameters renders the dataset non-reproducible and legally ambiguous. A full revision is required to address these fundamental data quality gaps before the paper can be considered for publication.
