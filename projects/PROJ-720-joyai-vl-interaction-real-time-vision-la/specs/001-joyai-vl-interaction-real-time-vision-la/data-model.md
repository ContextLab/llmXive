# Data Model: JoyAI-VL-Interaction

## Overview

This document defines the data structures used for the JoyAI-VL-Interaction reproduction pipeline. It covers input data (video frames), model inputs/outputs, decision artifacts, and system logs.

## Input Data

### Video Frame Stream
*   **Source**: Local video files (MP4) or synthetic frames.
*   **Format**: RGB images, 224x224 or 336x336 resolution (model dependent).
*   **Schema**:
    *   `frame_id`: Integer (unique per frame)
    *   `timestamp`: Float (seconds from start)
    *   `image_data`: Bytes or Path (pointer to image file)
    *   `metadata`: Dict (optional, e.g., scene description)

### Sample Video Clip
*   **Source**: `data/samples/`
*   **Format**: MP4 (H.264)
*   **Schema**:
    *   `clip_id`: String (unique identifier)
    *   `duration`: Float (seconds)
    *   `frame_count`: Integer
    *   `path`: String (relative path to file)

## Model I/O

### Model Input
*   **Structure**: Text prompt + Image tensor.
*   **Schema**:
    *   `prompt`: String (e.g., "Describe the scene and decide: silent, respond, or delegate?")
    *   `images`: List[Tensor] (Batch of image tensors)

### Model Output
*   **Structure**: Raw text generation.
*   **Schema**:
    *   `raw_text`: String (Model's unstructured response)
    *   `tokens`: List[Integer] (Token IDs)

## Decision Artifacts

### Decision Record
*   **Purpose**: Stores the model's decision and reasoning for each frame.
*   **Schema**:
    *   `decision_id`: UUID
    *   `clip_id`: String
    *   `frame_id`: Integer
    *   `decision_type`: Enum["silent", "respond", "delegate"]
    *   `reasoning`: String (Extracted from model output)
    *   `confidence`: Float (0.0 - 1.0, if available)
    *   `timestamp`: ISO 8601
    *   `model_metadata`: Dict (Model version, quantization level, size e.g., "8B-4bit" or "1.3B")
    *   `deviation_flag`: Boolean (True if a resource-constrained approximation, e.g., 1.3B model, was used instead of the 8B spec model)
    *   `deviation_reason`: String (Optional, e.g., "OOM on 8B model")

### Delegation Artifact
*   **Purpose**: Records when the system delegates to the background agent.
*   **Schema**:
    *   `delegation_id`: UUID
    *   `decision_id`: UUID (Reference)
    *   `agent_service`: String (Name of the service)
    *   `status`: Enum["success", "failed", "timeout"]
    *   `result`: String (Agent's response or error message)
    *   `timestamp`: ISO 8601

### Memory Summary Artifact
*   **Purpose**: Records the output of the memory summarizer component.
*   **Schema**:
    *   `summary_id`: UUID
    *   `clip_id`: String
    *   `content`: String (Summarized text)
    *   `source_frames`: List[Integer] (Frames included)
    *   `timestamp`: ISO 8601

### Visualization Artifact
*   **Purpose**: Records the output of the visualization component.
*   **Schema**:
    *   `viz_id`: UUID
    *   `clip_id`: String
    *   `file_path`: String (Path to generated image/file)
    *   `type`: String (e.g., "heatmap", "decision_tree")
    *   `timestamp`: ISO 8601

## System Logs

### Pipeline Log
*   **Purpose**: Tracks the execution of the entire pipeline.
*   **Schema**:
    *   `log_id`: UUID
    *   `component`: String (e.g., "ASR", "Model", "TTS", "Agent", "Memory", "Viz")
    *   `level`: Enum["INFO", "WARNING", "ERROR"]
    *   `message`: String
    *   `context`: Dict (Additional context, e.g., frame_id, error_code)
    *   `timestamp`: ISO 8601

### Environment Check Log
*   **Purpose**: Records the result of the environment verification.
*   **Schema**:
    *   `check_id`: UUID
    *   `cpu_cores`: Integer
    *   `ram_gb`: Float
    *   `gpu_available`: Boolean
    *   `status`: Enum["passed", "failed"]
    *   `errors`: List[String]
    *   `timestamp`: ISO 8601

## Output Artifacts

### Generated Artifacts
*   **Purpose**: Final outputs produced by the pipeline.
*   **Schema**:
    *   `artifact_id`: UUID
    *   `type`: Enum["text_response", "audio_tts", "memory_summary", "visualization", "delegation_result"]
    *   `clip_id`: String
    *   `file_path`: String (Relative path to generated file)
    *   `size_bytes`: Integer
    *   `created_at`: ISO 8601