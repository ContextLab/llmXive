---
action_items:
- id: d5b69549a811
  severity: writing
  text: In Table 1, the citation for 'Gemini Live API' and 'Sesame web app' points
    to `hume2025evi3`. This citation key corresponds to the Hume EVI 3 paper, not
    Google's Gemini or Sesame. Verify the correct source for these benchmarks or remove
    the citation if the data is proprietary/unpublished.
- id: 8620d05ab42c
  severity: writing
  text: The claim that Wan-Streamer 'does not rely on external language, speech, avatar,
    or video-generation modules' (Abstract, Intro) is absolute. While the architecture
    is unified, the training section mentions initializing from `yang2025qwen25` and
    `yang2025qwen3`. Clarify if these base models count as 'external language modules'
    in the context of the claim, or rephrase to 'does not rely on *separate* external
    modules at inference'.
- id: '343762147625'
  severity: writing
  text: Table 2 lists 'Qwen3/3.5-Omni' with a 'first-packet' latency of 234/547 ms.
    The citation `qwen3omni2025` and `qwen35omni2026` are included in the bib, but
    ensure the specific numbers (234/547) are explicitly reported in those sources
    or clearly marked as internal measurements to avoid misattribution.
artifact_hash: 17b9da44bd0e95030f93bbc19c09a0e8be715a82553be99ad52037aacf918aae
artifact_path: projects/PROJ-790-wan-streamer-v0-1-end-to-end-real-time-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:35:50.217872Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the validity of their supporting citations.

**Citation Mismatches and Attribution:**
In Table 1 (`tab:response-latency-comparison`), the rows for "Gemini Live API" and "Sesame web app" cite `hume2025evi3` (Hume EVI 3). The bibliography confirms `hume2025evi3` refers to the Hume paper. Unless the Hume paper explicitly benchmarks Google's Gemini or Sesame (which is unlikely for proprietary API benchmarks), this is a citation error. The authors should either cite the official Google/Sesame documentation or remove the citation if the numbers are internal estimates. Currently, the text implies the Hume paper is the source for Gemini/Sesame latency, which is factually unsupported by the provided bibliography.

**Scope of Claims vs. Evidence:**
The Abstract and Introduction make a strong claim: "Wan-Streamer does not rely on external language, speech, avatar, or video-generation modules." However, Section 3.3 (Training) states the model is initialized from a language model (`yang2025qwen25`, `yang2025qwen3`). While the *inference* pipeline is unified, the claim of not relying on external modules could be interpreted as ignoring the foundational pre-training dependency. To maintain accuracy, the claim should be qualified (e.g., "does not rely on *separate* external modules at inference" or "does not require *additional* external modules beyond the base initialization"). As written, the absolute phrasing risks being technically inaccurate regarding the model's lineage.

**Data Source Verification:**
Table 2 (`tab:av-runtime-comparison`) lists specific latency metrics for "Qwen3/3.5-Omni" (234/547 ms). While the citations `qwen3omni2025` and `qwen35omni2026` are present, the authors must ensure these specific numbers are explicitly reported in those papers. If these are internal measurements or derived from a different source not cited, the attribution is incorrect. Given the "first-packet" metric is often a specific engineering detail, precise sourcing is required to support the comparative claim.

**Latency Definitions:**
The paper defines "model-side response latency" as ~200 ms and "total interaction latency" as ~550 ms (including 350 ms network). This distinction is clearly stated and supported by the text in Section 4. However, the comparison in Table 1 mixes "model-only," "first-packet," and "API" metrics. While the authors explain this in the text, the claim that Wan-Streamer's 550 ms is "sub-second" is accurate, but the comparison to systems with "160 ms theoretical" (Moshi) requires the reader to trust the text's explanation that Moshi's number is not a full interaction loop. The text handles this well, but the table's "User-visible response" column for Moshi says "N/R product path," which is accurate, yet the "Other reported metric" column lists "160 ms theoretical." The claim that Wan-Streamer is faster than Moshi in a *full* loop is supported, but the raw numbers in the table could be misleading without the accompanying text. The text is sufficient, so no revision is needed here, but the citation accuracy in Table 1 remains the primary issue.
