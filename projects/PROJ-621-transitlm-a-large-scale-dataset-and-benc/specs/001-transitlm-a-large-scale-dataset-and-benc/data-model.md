# Data Model: Map-Free Transit Route Generation with LLMs

## Overview

This document defines the data structures used in the project, focusing on the conversion of GTFS data into "map-free" text sequences and the validation results. The data model ensures strict adherence to the "map-free" constraint (no coordinates) and supports the deterministic graph-traversal validation.

## Entities

### 1. GTFS Raw Data (Source)
*Note: Raw GTFS files are not modified. They are the source of truth.*
- **`stops.txt`**: `stop_id`, `stop_name`, `stop_lat`, `stop_lon` (ignored in text generation).
- **`routes.txt`**: `route_id`, `route_short_name`, `route_type`.
- **`stop_times.txt`**: `trip_id`, `stop_id`, `stop_sequence`, `arrival_time`, `departure_time`.
- **`trips.txt`**: `trip_id`, `route_id`, `service_id`.

### 2. Map-Free Text Sequence (Derived)
*Derived from GTFS, strictly excluding coordinates.*
- **`sequence_id`**: Unique identifier (UUID).
- **`origin_station`**: Station name (string).
- **`destination_station`**: Station name (string).
- **`line_id`**: Line identifier (string).
- **`sequence_text`**: The natural language prompt (e.g., "Take Line A from Station X to Station Y.").
- **`ground_truth_path`**: List of station names representing the correct path (for validation).
- **`is_held_out`**: Boolean (True if not in training set).
- **`split_type`**: String ("train" or "test_path_disjoint").

### 3. Generated Route (Model Output)
- **`request_id`**: Link to the input sequence.
- **`generated_text`**: Raw LLM output (may contain filler).
- **`parsed_stations`**: List of station names extracted from `generated_text`.
- **`parsed_lines`**: List of line IDs extracted (optional).
- **`is_valid`**: Boolean (True if `parsed_stations` matches a path in the GTFS graph).
- **`exact_match`**: Boolean (True if `parsed_stations` exactly matches `ground_truth_path`).
- **`shortest_path_deviation`**: Float (Ratio of generated path length to ground-truth shortest path length).
- **`error_message`**: String (if parsing fails or topology is invalid).

### 4. Validation Result (Aggregated)
- **`model_id`**: Identifier for the model (fine-tuned vs. baseline).
- **`total_samples`**: Integer.
- **`valid_count`**: Integer.
- **`exact_match_count`**: Integer.
- **`validity_rate`**: Float (0.0-1.0).
- **`exact_match_rate`**: Float (0.0-1.0).
- **`mean_deviation`**: Float (Average shortest-path deviation).
- **`p_value_mcnemar`**: Float (from McNemar's test).
- **`p_value_permutation`**: Float (from permutation test).
- **`is_significant`**: Boolean (True if p < 0.05).

## Data Flow

1. **Ingestion**: GTFS files downloaded and checksummed.
2. **Transformation**: `gtfs_to_text.py` converts GTFS to `sequence_text` (no coordinates).
3. **Splitting**: `sequence_id` is split into `train` and `held_out` sets (path-disjoint).
4. **Training**: Model fine-tuned on `train` sequences.
5. **Inference**: Model generates `generated_text` for `held_out` sequences.
6. **Parsing**: `parse_llm_output.py` extracts `parsed_stations`.
7. **Validation**: `validate_graph.py` checks `parsed_stations` against GTFS graph.
8. **Aggregation**: `stats.py` computes rates, deviation, and p-values.

## Constraints & Validation Rules

- **No Coordinates**: `sequence_text` must not contain regex patterns matching latitude/longitude.
- **Station Names**: Must match exactly with `stop_name` in GTFS.
- **Graph Connectivity**: Every consecutive pair in `parsed_stations` must exist in the GTFS graph.
- **Held-Out Set**: `is_held_out` must be True for all evaluation samples.
- **Path-Disjoint**: `split_type` must be "test_path_disjoint" for test samples, ensuring no edge sequence overlap with training.
