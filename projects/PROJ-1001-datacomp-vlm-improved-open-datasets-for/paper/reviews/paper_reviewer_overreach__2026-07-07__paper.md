---
action_items:
- id: 9c743f81e7eb
  severity: writing
  text: The abstract/conclusion claims the method 'solves' or 'eliminates' the need
    for quality filtering, but Section 4 and Appendix E002 show filtering provides
    diminishing returns or small gains only on specific subsets (e.g., global CLIP-score
    on small scale). Replace absolute terms like 'solves' with 'reduces the efficacy
    of' or 'shows diminishing returns for' and scope the claim to the tested model
    scales (1B-4B) and token budgets.
- id: a13e0f050ef8
  severity: writing
  text: The paper states 'no individual quality filter provides reliable and consistent
    gains' (Section 2/Abstract), yet Table E003 (medium scale) shows NVIDIA Nemotron
    (text-only) and OpenAI-CLIP (im-cap) achieving +0.4pp to +0.6pp gains over the
    baseline in specific categories. The claim of 'no reliable gains' overgeneralizes
    the mixed results. Qualify the claim to 'no consistent gains across all data types
    and scales' or explicitly acknowledge the specific conditions where filters did
    help.
- id: d8eb98cd2aa9
  severity: science
  text: The conclusion implies the findings generalize to 'all VLMs' or 'any scale,'
    but the experiments (Section 4, Appendix E001) are restricted to Qwen2.5-based
    models (1B, 2B, 4B) and a specific training recipe (InternVL-style). The claim
    of universality is not licensed by the single-family study. Narrow the claim to
    'within the Qwen2.5 family and tested scales' or add experiments on a distinct
    architecture (e.g., LLaVA or Flamingo-style) to support broader generalization.
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:41:12.529511Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims about the generalizability of its findings regarding data filtering and mixing that exceed the scope of the provided evidence.

First, the abstract and conclusion assert that the study demonstrates "no individual quality filter provides reliable and consistent gains," effectively suggesting that filtering is obsolete for VLM training. However, the data in Appendix E003 (Tables for local filtering) shows that while many filters fail, specific configurations (e.g., NVIDIA Nemotron on text-only data at medium scale, or OpenAI-CLIP on image-caption pairs) do yield small but positive gains (+0.4pp to +0.6pp) over the no-filter baseline. The rhetoric of "no reliable gains" ignores these positive signals and overgeneralizes the null results found in other configurations. The claim should be hedged to reflect that filtering is *inconsistent* rather than universally ineffective, or the authors should demonstrate that these small gains are statistically insignificant or not robust across seeds.

Second, the paper frames its findings on data mixing (specifically the superiority of "Instruction-heavy" mixtures at larger scales) as a universal principle for VLMs. The experiments, however, are conducted exclusively on the Qwen2.5 family of models (1B, 2B, 4B) using a specific InternVL-style training recipe. The conclusion that "scale-aware curation is required" and that instruction-heavy mixes are superior is presented as a general law, yet it is only demonstrated for one model family and one architecture. Without testing on a structurally different model (e.g., a Q-former based model like Flamingo or a different LLM backbone), the claim of universality is an overreach. The text should explicitly limit the scope of the generalization to the tested model families or include a cross-architecture validation.

Finally, the paper uses strong language like "solves" or "eliminates" regarding the problem of data contamination or the necessity of filtering. While the decontamination section is rigorous, the claim that the proposed method "solves" the problem of train-test overlap is too absolute given that the method relies on specific thresholds (SSCD 0.75, MinHash 0.55) which are heuristic choices. The paper admits these thresholds involve trade-offs (false positives/negatives). The rhetoric should be adjusted to "mitigates" or "significantly reduces" rather than "solves," and the limitations of the threshold selection should be more prominently acknowledged in the conclusion rather than buried in the appendix.
