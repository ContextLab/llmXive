# Data Model: The Impact of Visual Attention on False Memory Formation

## Overview

This document defines the data model for the project, including entities, relationships, and schemas. The model is designed to support the analysis of visual attention and false memory formation, with strict adherence to the project's constitution (reproducibility, data hygiene, etc.).

## Entities

### Image
Represents a single Visual Genome photograph.
- `image_id`: Unique identifier (integer).
- `url`: URL to the image (string).
- `width`: Image width (integer).
- `height`: Image height (integer).
- `checksum`: SHA-256 checksum of the raw image file (string).
- `annotation_density`: Number of objects annotated in the image (float) - **Confounder**.

### Object
An annotated region within an Image.
- `object_id`: Unique identifier (integer).
- `image_id`: Foreign key to `Image`.
- `category`: Object category (string).
- `mask`: Binary mask (numpy array, stored as a file or serialized).
- `saliency_score`: Average saliency score for the object (float).
- `is_irrelevant`: Boolean flag indicating if the object is "salient but irrelevant" (boolean).
- `object_size`: Area of the bounding box (float) - **Confounder**.

### ParticipantRecall
Transcript of a participant's free recall for a given image.
- `participant_id`: Unique identifier (string).
- `image_id`: Foreign key to `Image`.
- `reported_objects`: List of object categories mentioned in the transcript (list of strings).
- `timestamp`: Timestamp of the recall (datetime).

### FalseMemoryFlag
Binary flag indicating if an object was falsely remembered.
- `object_id`: Foreign key to `Object`.
- `participant_id`: Foreign key to `ParticipantRecall`.
- `is_false_memory`: Boolean flag (true if the object was mentioned in the transcript but absent from the ground truth).
- `verification_status`: Status of the secondary verification (e.g., "confirmed", "unconfirmed", "rejected") (string).
- `consensus_score`: Number of raters agreeing on the flag (integer) - **For Consensus Coding**.

### SaliencyModel
Information about the saliency model used.
- `model_name`: Name of the model (string).
- `weights_path`: Path to the pretrained weights (string).
- `benchmark_auc`: AUC score on the SALICON benchmark (float).

### NoiseMetric
Metrics for annotation density and noise analysis.
- `image_id`: Foreign key to `Image`.
- `annotation_density`: Number of objects per image (float).
- `saliency_correlation`: Correlation between saliency and annotation density (float).

## Relationships

- **Image** has many **Objects**.
- **Image** has many **ParticipantRecall** entries.
- **Object** is linked to **FalseMemoryFlag** via `object_id`.
- **ParticipantRecall** is linked to **FalseMemoryFlag** via `participant_id`.
- **SaliencyModel** is used to generate **saliency_score** for **Object**.
- **Image** has one **NoiseMetric**.

## Data Flow

1. **Download**: Visual Genome images and annotations are downloaded and stored in `data/raw`.
2. **Preprocess**: Images are resized, masks are extracted, and saliency maps are generated.
3. **Link**: Recall transcripts are aligned with Visual Genome IDs.
4. **Code**: False memory flags are computed based on the transcript and ground truth.
5. **Analyze**: Statistical tests are performed on the aggregated data.
6. **Noise Check**: Correlation between saliency and annotation density is computed.

## Storage Strategy

- **Raw Data**: Stored in `data/raw` with checksums.
- **Processed Data**: Stored in `data/processed` as CSV/JSON files and serialized numpy arrays.
- **Models**: Pretrained weights stored in `models/` with versioning.
- **Logs**: Exclusion logs and verification status stored in `data/logs/`.
