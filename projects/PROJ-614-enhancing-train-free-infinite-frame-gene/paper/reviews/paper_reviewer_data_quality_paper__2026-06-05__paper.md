---
action_items:
- id: 7c02ab3093c4
  severity: writing
  text: The paper lacks explicit license information for VBench, NarrLV, and foundation
    models (VideoCrafter2, Wan2.1). Add a data availability statement specifying licenses
    for all external datasets and models used.
- id: b8b8f752539d
  severity: writing
  text: No version numbers are specified for VBench or NarrLV benchmarks. Include
    version identifiers or commit hashes to ensure reproducibility of evaluation results.
- id: 1645e314732f
  severity: writing
  text: The project page URL (https://xiaokunfeng.github.io/miga_homepage/) in the
    abstract has no archival guarantee. Consider adding an arXiv snapshot or DOI for
    permanent access.
- id: 68319942ac43
  severity: writing
  text: Evaluation data (VBench/NarrLV prompts, data splits) are not described with
    sufficient detail. Add a data card appendix specifying prompt counts, split sizes,
    and any preprocessing applied.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T01:23:14.246116Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This re-review confirms that the four data quality action items from the previous cycle remain unaddressed in the current manuscript revision.

First, explicit license information for VBench, NarrLV, and foundation models (VideoCrafter2, Wan2.1) is still missing. Section 5 (Experiments) and the References do not contain a data availability statement specifying the legal terms under which these external resources are used.

Second, version numbers for VBench and NarrLV benchmarks are not provided. Section 5.1 mentions the benchmarks but lacks version identifiers or commit hashes, which are critical for reproducing the evaluation results.

Third, the project page URL in the Abstract (line ~150) remains a dynamic link without an arXiv snapshot or DOI for permanent access, posing a risk of link rot.

Finally, evaluation data details such as prompt counts and data splits are not included in a data card appendix. While Section 5.1 mentions TNA counts, it lacks full dataset specifications required for transparency.

These omissions hinder reproducibility and compliance with data sharing standards. Please address all four points to meet the data quality requirements.
