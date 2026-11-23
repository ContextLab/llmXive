# Data Model Specification

## Synthetic Document Metadata

Each generated document has a corresponding JSON metadata file containing:
- `doc_id`: Unique identifier.
- `page_count`: Total number of pages.
- `page_metadata`: List of per-page objects containing:
 - `page_num`: Page index.
 - `text_density`: Estimated text density (pixels/area).
 - `region`: Classification (first-third, middle-third, last-third).
- `questions`: List of questions with:
 - `question_id`: Unique identifier.
 - `text`: Question string.
 - `target_page`: Page number containing the answer.
 - `target_region`: Region classification.

## Evaluation Metrics

- `baseline_metrics.json`: Per-model accuracy tables, bias trends, and delta calculations.
- `retrieval_metrics.json`: Retrieval precision/recall, false-positive rate, and VLM accuracy with retrieval.
- `statistical_results.json`: Spearman correlation coefficient, p-value, and classification.