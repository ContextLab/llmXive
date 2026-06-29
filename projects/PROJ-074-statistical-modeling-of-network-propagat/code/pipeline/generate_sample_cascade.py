"""
Generate sample JSON cascade file for schema validation testing.

This script creates a sample cascade dataset in data/raw/ that can be used
to validate the JSON cascade schema as specified in contracts/ and data-model.md.

The sample data includes cascades with required fields:
- cascade_id: Unique identifier for the cascade
- node_id: Unique identifier for each node in the cascade
- timestamp: UTC timestamp of the node event
- cascade_label: Label indicating cascade type

Additional fields for comprehensive testing:
- historical_degree: Historical degree of the user before cascade
- historical_shares: Historical share count before cascade
- user_id: User identifier
- message_id: Message identifier
- platform_id: Platform identifier (twitter, facebook, etc.)
"""

import json
import logging
from pathlib import Path

from pipeline.utils import set_global_seed, setup_logger


def generate_sample_cascades():
    """
    Generate sample cascade data for schema validation testing.

    Returns:
        list: List of cascade dictionaries with required and optional fields.
    """
    set_global_seed(12345)

    cascades = [
        {
            "cascade_id": "cascade_001",
            "platform_id": "twitter",
            "cascade_label": "misinformation",
            "node_count": 3,
            "nodes": [
                {
                    "node_id": "node_001_1",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "user_id": "user_101",
                    "message_id": "msg_1001",
                    "historical_degree": 2,
                    "historical_shares": 1
                },
                {
                    "node_id": "node_001_2",
                    "timestamp": "2024-01-15T10:35:00Z",
                    "user_id": "user_102",
                    "message_id": "msg_1002",
                    "historical_degree": 3,
                    "historical_shares": 2
                },
                {
                    "node_id": "node_001_3",
                    "timestamp": "2024-01-15T10:40:00Z",
                    "user_id": "user_103",
                    "message_id": "msg_1003",
                    "historical_degree": 1,
                    "historical_shares": 0
                }
            ]
        },
        {
            "cascade_id": "cascade_002",
            "platform_id": "facebook",
            "cascade_label": "misinformation",
            "node_count": 2,
            "nodes": [
                {
                    "node_id": "node_002_1",
                    "timestamp": "2024-01-16T14:20:00Z",
                    "user_id": "user_201",
                    "message_id": "msg_2001",
                    "historical_degree": 5,
                    "historical_shares": 3
                },
                {
                    "node_id": "node_002_2",
                    "timestamp": "2024-01-16T14:25:00Z",
                    "user_id": "user_202",
                    "message_id": "msg_2002",
                    "historical_degree": 2,
                    "historical_shares": 1
                }
        ]
        }
    ]

    return cascades


def main(output_path="data/raw/sample_cascade.json"):
    """
    Main entry point to generate and save sample cascade data.

    Args:
        output_path: Path where the JSON file will be written.
    """
    logger = setup_logger("generate_sample_cascade")
    logger.info(f"Generating sample cascade data to {output_path}")

    cascades = generate_sample_cascades()

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cascades, f, indent=2)

    logger.info(f"Successfully wrote {len(cascades)} cascades to {output_file}")
    logger.info(f"Output file: {output_file.absolute()}")

    return str(output_file)


if __name__ == "__main__":
    main()
