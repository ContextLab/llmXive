---
action_items:
- id: 5792033c013e
  severity: writing
  text: Pin the code repository version (e.g., commit hash or tag) in the manuscript
    to prevent link rot and ensure reproducibility.
- id: 4fb44347304b
  severity: writing
  text: Explicitly state the exact versions of datasets used (e.g., BEIR v1.0.0, TREC
    DL2019/2020) to ensure data consistency.
- id: ac1420975237
  severity: writing
  text: Declare a software license for the code repository and any derived data artifacts
    to ensure legal clarity.
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T16:29:44.336661Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Re-Review Assessment**

This re-review confirms that the three prior action items from my previous data quality assessment remain **unaddressed** in the current manuscript revision.

**1. Code Repository Version (ID: 5792033c013e)**
The abstract (line ~100) states "Code available at \url{https://github.com/jerecoder/IReranker}" but does not pin a specific commit hash, tag, or release version. Without version pinning, future readers may encounter a different code state than what was used for the reported experiments, undermining reproducibility. This is a persistent gap requiring a footnote or appendix entry with the exact commit hash.

**2. Dataset Versions (ID: 4fb44347304b)**
The manuscript references TREC DL2019/2020 and "BEIR-style tasks" (Section 5, line ~380; Table 2) but does not specify exact dataset versions (e.g., BEIR v1.0.0, MS MARCO version). Dataset versions can change over time with new annotations or splits, affecting result reproducibility. The "Results" section (line ~385) mentions BEIR-style tasks without citing the specific dataset snapshot used.

**3. Software License Declaration (ID: ac1420975237)**
No license is declared in the manuscript text for the code repository or derived data artifacts. While the GitHub repository may contain a LICENSE file, the manuscript itself should explicitly state the license (e.g., MIT, Apache 2.0) to ensure legal clarity for downstream users. This omission persists from the prior review.

**New Issues Identified:** None. No new data quality concerns emerged in this revision cycle.

**Recommendation:** All three action items remain unresolved and must be addressed before acceptance. These are writing-level fixes that do not require re-running experiments.
