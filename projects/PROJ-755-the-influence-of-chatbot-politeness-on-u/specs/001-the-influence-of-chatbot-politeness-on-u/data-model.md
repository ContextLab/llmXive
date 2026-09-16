# Data Model: Chatbot Politeness and User Trust

## Entities

*   **Dialogue**: A single conversation.
    *   `dialogue_id` (string): Unique identifier for the dialogue.
    *   `user_id` (string): Unique identifier for the user.
    *   `quality_rating` (integer): User-reported quality rating (1-5).
    *   `mean_politeness_score` (float): Mean politeness score for the dialogue (z-scored).
*   **Utterance**: A single message within a dialogue.
    *   `utterance_id` (string): Unique identifier for the utterance.
    *   `dialogue_id` (string): Foreign key referencing the Dialogue.
    *   `speaker_role` (string): "user" or "chatbot".
    *   `text_content` (string): Text of the utterance.
    *   `politeness_score` (float): Politeness score for the utterance.
*   **User**: A participant in the dataset.
    *   `user_id` (string): Unique identifier for the user.
    *   `age` (integer): User's age.
    *   `gender` (string): User's gender.

## Relationships

*   One User has many Dialogues.
*   One Dialogue has many Utterances.

## Data Types

*   Strings will be UTF-8 encoded.
*   Integers will be 32-bit.
*   Floats will be 64-bit.

## Schema (contracts/dataset.schema.yaml)

```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
description: Schema for the dataset used in the chatbot politeness and user trust analysis.
properties:
  dialogue_id:
    type: string
    description: Unique identifier for the dialogue.
  user_id:
    type: string
    description: Unique identifier for the user.
  quality_rating:
    type: integer
    description: User-reported quality rating (1-5).
    minimum: 1
    maximum: 5
  mean_politeness_score:
    type: number
    format: float
    description: Mean politeness score for the dialogue (z-scored).
  utterances:
    type: array
    items:
      type: object
      properties:
        utterance_id:
          type: string
          description: Unique identifier for the utterance.
        speaker_role:
          type: string
          description: "user" or "chatbot".
          enum: ["user", "chatbot"]
        text_content:
          type: string
          description: Text of the utterance.
        politeness_score:
          type: number
          format: float
          description: Politeness score for the utterance.
```
