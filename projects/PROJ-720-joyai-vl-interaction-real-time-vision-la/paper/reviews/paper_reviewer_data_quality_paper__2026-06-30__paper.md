---
action_items:
- id: 7d6e4384ef5b
  severity: science
  text: The paper makes significant claims regarding the release of a "complete, deployable
    system" and "fully open-sourced" data and training recipes (Abstract, Section
    1). However, a review of the data quality and provenance reveals critical gaps
    that prevent verification of these claims. First, the data provenance and licensing
    are insufficiently documented. Section 3.2 ("Data Construction for VL-Interaction")
    describes a corpus of "more than 4M time-aligned streaming clips" derived from
    "open-source
artifact_hash: 5266e7279b96ba8c30af6614b2b08bda02ec2220e0d4769bb56ba9df667b0fe5
artifact_path: projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T08:12:11.003256Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The paper makes significant claims regarding the release of a "complete, deployable system" and "fully open-sourced" data and training recipes (Abstract, Section 1). However, a review of the data quality and provenance reveals critical gaps that prevent verification of these claims.

First, the **data provenance and licensing** are insufficiently documented. Section 3.2 ("Data Construction for VL-Interaction") describes a corpus of "more than 4M time-aligned streaming clips" derived from "open-source commentary," "broadcast footage," and "web-collected videos." The paper fails to list the specific source datasets, their URLs, or the licenses under which they were obtained. Without this information, it is impossible to determine if the resulting dataset is legally redistributable or if it contains copyrighted material that would restrict its use. The claim of being "fully open-sourced" is unsubstantiated without a clear license (e.g., CC-BY-4.0, MIT) attached to the data release.

Second, the **availability of the data** is contradictory. The header of the paper (lines 45-47) states: "The model weights, interaction data, and full system code will be released by June 20, 2026." If the paper is being reviewed in 2026, this implies the data is not yet available. If the submission date is earlier, the claim of "fully open-sourced" contributions in the abstract is premature. For a data-centric review, the data must be accessible *at the time of review* to verify the training recipe and data quality. The current state renders the reproducibility of the "time-aligned data" impossible.

Third, the **evaluation data** lacks provenance. Section 4.1 states that the 58 evaluation cases are "drawn mostly from public footage on the web." No list of these videos, their sources, or their licenses is provided. This omission prevents independent verification of the benchmark and raises concerns about the legality of the evaluation set.

Finally, the **schema and format** of the data are described only through examples in the Appendix (Section 99). While the JSON structure is visible, there is no formal schema definition (e.g., JSON Schema) or documentation on how the "per-second" labels are strictly enforced across the 4M clips. The lack of a formal data card or documentation on missing-data handling (e.g., how gaps in video streams are handled) further reduces the utility of the claimed release.

To proceed, the authors must provide a public link to the dataset (or a clear statement of its unavailability), a specific license for the data, a list of source datasets with their licenses, and a formal data card detailing the schema and quality control measures.
