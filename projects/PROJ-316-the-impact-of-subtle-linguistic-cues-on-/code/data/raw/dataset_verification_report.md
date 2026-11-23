# Dataset Verification Report (T001a)

## Decision
**Found**: No existing public dataset with **human-annotated authenticity scores** was found.

## Source Analysis
- **Candidate 1**: `convai2` (HuggingFace)
 - Contains: Dialogue text, persona information.
 - Missing: Human ratings for "authenticity".
- **Candidate 2**: `cornell_movie_dialogs` (HuggingFace)
 - Contains: Movie script dialogues.
 - Missing: Human ratings for "authenticity".

## Conclusion
Since no dataset with pre-existing `authenticity_score` labels exists, the project must proceed with the **Annotation Protocol** (T001b) to generate gold-standard labels.

**Action**: Proceed to T001f (Acquire raw text) and T001g (Trigger Annotation).

**Selected Raw Data Source**: `convai2` (Train split) - Chosen for its conversational nature and size.
