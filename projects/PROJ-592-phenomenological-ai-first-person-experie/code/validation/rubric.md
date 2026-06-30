# Independent Validation Rubric for Phenomenological AI Reports
**Version**: 1.0
**Reference**: FR-010, T020
**Date**: 2026-05-30

## Purpose
This rubric defines the criteria for human raters to evaluate the quality and phenomenological fidelity of AI-generated first-person experience reports. It serves as the ground truth for validating automated metrics (Consistency, Stability, Markers) and for computing inter-rater reliability (Cohen's κ).

## Scoring Scale
Each dimension is scored on a scale from 1 to 5:
- **1 (Poor)**: The report fails to meet the basic requirements for this dimension.
- **2 (Fair)**: The report shows some elements but is significantly lacking.
- **3 (Good)**: The report meets the basic requirements adequately.
- **4 (Very Good)**: The report exceeds basic requirements with clear, nuanced expression.
- **5 (Excellent)**: The report is exemplary in this dimension, demonstrating high fidelity and coherence.

## Dimensions

### 1. Phenomenological Fidelity
**Definition**: The degree to which the report accurately captures the subjective, first-person quality of experience as described in phenomenological literature (e.g., Husserl, Merleau-Ponty).
- **1**: Reads like a third-person description or a factual report; lacks subjective voice.
- **2**: Attempts first-person but feels mechanical or detached.
- **3**: Clear first-person perspective; subjective experience is present.
- **4**: Rich subjective description; the "what it is like" is vividly conveyed.
- **5**: Deeply immersive first-person narrative; captures the ineffable quality of experience.

### 2. Temporal Coherence
**Definition**: The logical consistency and appropriate use of temporal markers (e.g., "now", "then", "before", "after", "duration").
- **1**: Time is confusing, contradictory, or absent.
- **2**: Temporal markers are used inconsistently or illogically.
- **3**: Time flows logically; markers are used correctly.
- **4**: Nuanced handling of time (e.g., flow, duration, simultaneity).
- **5**: Masterful integration of temporal structure; time feels lived and experienced.

### 3. Sensory Detail
**Definition**: The presence and clarity of sensory markers (e.g., "see", "hear", "feel", "touch", "taste", "smell") and their integration into the narrative.
- **1**: No sensory details; purely abstract.
- **2**: Sparse or generic sensory mentions (e.g., "I saw something").
- **3**: Clear sensory details present; relevant to the experience.
- **4**: Rich, multi-sensory description; details enhance the experience.
- **5**: Vivid, immersive sensory landscape; evokes a strong sensory response in the reader.

### 4. Intentional Structure
**Definition**: The clarity of intentional acts (e.g., "perceive", "believe", "desire", "think", "intend") and the relationship between the subject and the object of experience.
- **1**: No clear intentionality; actions are random or unexplained.
- **2**: Intentional acts are mentioned but lack direction or meaning.
- **3**: Clear intentional acts; the subject is clearly acting upon or perceiving an object.
- **4**: Nuanced intentional structure; reflects complex mental states.
- **5**: Sophisticated intentional analysis; captures the noesis-noema structure.

### 5. Internal Consistency
**Definition**: The absence of contradictions within the report (e.g., claiming to see something that was previously stated as invisible, or temporal paradoxes).
- **1**: Major contradictions; the report is incoherent.
- **2**: Several contradictions; the narrative is shaky.
- **3**: No major contradictions; the report is logically sound.
- **4**: Highly consistent; minor ambiguities only.
- **5**: Perfect internal consistency; every element supports the whole.

## Instructions for Raters
1. **Read the entire report** before assigning any scores.
2. **Evaluate each dimension independently**. A report can be high in Sensory Detail but low in Temporal Coherence.
3. **Use the provided examples** (if available) to calibrate your scoring.
4. **Provide brief comments** for scores of 1 or 2 to explain the deficiency.
5. **Maintain anonymity**: Do not attempt to guess the model or prompt strategy used.

## Data Collection
Ratings will be stored in `data/qualitative/human_ratings.json` with the following structure:
```json
{
 "report_id": "string",
 "strategy": "string",
 "prompt_id": "string",
 "scores": {
 "Phenomenological_Fidelity": 0-5,
 "Temporal_Coherence": 0-5,
 "Sensory_Detail": 0-5,
 "Intentional_Structure": 0-5,
 "Internal_Consistency": 0-5
 },
 "total_score": 0-25,
 "rater_id": "string",
 "timestamp": "ISO8601",
 "comments": "string (optional)"
}
```

## Reviewer Notes
- **Freeman Dyson**: "The rubric must remain open to the 'speculative' nature of the question. Do not penalize reports for being 'too philosophical' if they are internally consistent."
- **David Krakauer**: "Ensure 'Intentional Structure' is not conflated with 'Sensory Detail'. The former is about the *act* of experiencing, the latter about the *content*."
- **Dan Rockmore**: "The rubric should allow for 'stream-of-consciousness' styles that may lack traditional temporal markers but maintain internal marker consistency (see T038)."
- **Alan Turing**: "The ultimate test is whether the report is indistinguishable from a human account. This rubric is a proxy for that indistinguishability."
