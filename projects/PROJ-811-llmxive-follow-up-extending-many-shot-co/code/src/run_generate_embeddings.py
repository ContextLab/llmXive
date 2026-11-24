"""
Helper script to invoke the PromptGenerator solely for the purpose of
generating SBERT embeddings (T024a) and persisting them to
``data/processed/embeddings.json``.
This script is executed in the verification step to ensure the required
output artifact exists.
"""

import argparse
import logging
from pathlib import Path
from code.src.prompt_gen import PromptGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate SBERT embeddings for all DAG examples.")
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to the DAG manifest JSON file."
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="original_cds",
        help="Prompt strategy (must be 'original_cds' to trigger embedding generation)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/original_cds_prompts.json",
        help="Dummy output path for prompts (required by the generator)."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    config = {
        "embedding_model": "sentence-transformers/all-MiniLM-L-v",
    }

    generator = PromptGenerator(config)
    # The generator will automatically compute and save embeddings when
    # the 'original_cds' strategy is used.
    try:
        dags = generator.load_dags(args.manifest)
        generator.generate_prompts(dags, args.strategy)
        logger.info("Embedding generation completed successfully.")
    except Exception as exc:
        logger.error(f"Failed to generate embeddings: {exc}")
        raise

if __name__ == "__main__":
    main()