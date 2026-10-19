---
action_items: []
artifact_hash: 77801ba9a0c9c4fd9964b58c6769881cc8786d5bf5620817c9f8d77f93da4e59
artifact_path: projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/spec.md
backend: dartmouth
feedback: 'Reading this spec as a case file, I find the design mostly coherent at
  the level of schemas and pipelines, but there are three internal inconsistencies
  that would undermine the inferential claims before any data arrive. First, the spec
  contradicts itself on multiple-testing: SC-007 states that ''Raw p-values are reported
  for each cleaning variant; no family-wise error correction is applied,'' while FR-028
  requires ''Wilcoxon test statistics and Bonferroni-adjusted p-values'' in the same
  hypothesis-t'
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-19T08:09:29.828463Z'
reviewer_kind: llm
reviewer_name: eric-kandel-simulated
score: 0.0
verdict: minor_revision
---

Reading this spec as a case file, I find the design mostly coherent at the level of schemas and pipelines, but there are three internal inconsistencies that would undermine the inferential claims before any data arrive. First, the spec contradicts itself on multiple-testing: SC-007 states that 'Raw p-values are reported for each cleaning variant; no family-wise error correction is applied,' while FR-028 requires 'Wilcoxon test statistics and Bonferroni-adjusted p-values' in the same hypothesis-testing artifact. One of these must govern; as written, a reviewer cannot tell whether the project's headline test (SC-011/FR-017) is corrected or not. Second, FR-017's paired Wilcoxon test on effect_size_change across datasets presupposes a paired-differences sample large enough for the signed-rank test to have any power; with the stated floor of 10-15 datasets this is marginal, and the spec sets 'No significance threshold' (SC-011) while simultaneously building an H1 around that test — a hypothesis attached to a test whose outcome the design declines to threshold is not falsifiable in any operational sense. Third, FR-023 and SC-010 demand a sample-size justification 'based on prior meta-analyses that indicate this quantity is sufficient,' yet the originating idea document itself concedes 'Literature search returned limited results directly addressing this question.' The spec thus mandates citing a prior literature that the project has already established does not exist; the justification artifact is being set up to fail or to be padded with citations that do not support the claim. Separately, FR-013's requirement to 'automatically trigger a download of a public dataset that satisfies the missingness and size requirements' is not achievable as stated: real public datasets do not arrive labelled MCAR/MAR/MNAR — those labels can only be assigned to missingness the experiment itself injects (as US-002's scenario correctly does with 'MCAR missingness artificially introduced'), and the spec nowhere specifies the mechanism by which MNAR would be simulated, which is precisely the hardest and most consequential case.

---

> *Note: this contribution was authored by **Eric Kandel (simulated)** — a simulated AI persona shaped from the public-record writings of Eric Kandel, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Eric Kandel.*
