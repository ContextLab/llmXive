import random
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from code.src.parser_utils import load_json_file, save_json_file
from code.src.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptGenerator:
    """
    Generates few-shot prompts based on different ordering strategies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.prompt_template = self.config.get("prompt", {}).get("template", "")
        self.example_template = self.config.get("prompt", {}).get("example_template", "")
        self.separator = self.config.get("prompt", {}).get("separator", "\n\n")

    def load_examples_from_manifest(self, manifest_path: Path) -> List[Dict[str, Any]]:
        """
        Loads examples from the DAG manifest file.
        
        Args:
            manifest_path: Path to the dag_manifest.json file.
            
        Returns:
            List of example dictionaries.
        """
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        
        manifest = load_json_file(manifest_path)
        if not isinstance(manifest, list):
            raise ValueError("Manifest must be a list of examples")
        
        return manifest

    def sort_by_logical_ascending(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts examples by Logical Difficulty Score (max path depth) in ascending order.
        
        Args:
            examples: List of example dictionaries containing 'logical_difficulty' or 'depth'.
            
        Returns:
            Sorted list of examples.
        """
        return sorted(
            examples,
            key=lambda x: x.get("logical_difficulty", x.get("depth", 0))
        )

    def shuffle_deterministic(self, examples: List[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
        """
        Shuffles examples deterministically using a fixed seed.
        
        Args:
            examples: List of example dictionaries.
            seed: Random seed for reproducibility.
            
        Returns:
            Shuffled list of examples.
        """
        shuffled = examples.copy()
        rng = random.Random(seed)
        rng.shuffle(shuffled)
        return shuffled

    def sort_by_original_cds(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts examples by Original CDS (Semantic Curvature) score.
        
        Args:
            examples: List of example dictionaries containing 'curvature_score'.
            
        Returns:
            Sorted list of examples (descending order for curvature).
        """
        return sorted(
            examples,
            key=lambda x: x.get("curvature_score", 0),
            reverse=True
        )

    def assemble_prompt(self, examples: List[Dict[str, Any]], include_query: bool = True) -> str:
        """
        Assembles a single prompt string from a list of examples.
        
        This method combines the system prompt, few-shot examples, and optionally
        the test query into a single string formatted for LLM inference.
        
        Args:
            examples: List of example dictionaries. Each must contain at least:
                      - 'question': The input question
                      - 'answer': The ground truth or model answer
                      Optionally:
                      - 'thought': Chain of thought if available
            include_query: If True, appends a placeholder for the test query at the end.
            
        Returns:
            A single formatted prompt string.
        """
        if not examples:
            logger.warning("No examples provided to assemble_prompt. Returning empty string.")
            return ""

        parts = []

        # Add system prompt if defined in config
        system_prompt = self.config.get("prompt", {}).get("system_prompt", "")
        if system_prompt:
            parts.append(system_prompt)

        # Assemble few-shot examples
        for i, example in enumerate(examples):
            question = example.get("question", "")
            answer = example.get("answer", "")
            thought = example.get("thought", "")
            
            # Format individual example
            if thought:
                example_text = self.example_template.format(
                    question=question,
                    thought=thought,
                    answer=answer
                )
            else:
                example_text = self.example_template.format(
                    question=question,
                    answer=answer
                )
            
            parts.append(example_text)

        # Add test query placeholder if requested
        if include_query:
            query_placeholder = self.config.get("prompt", {}).get("query_placeholder", "Question: {question}\nAnswer:")
            # We append the start of the query, expecting the actual question to be filled in by the runner
            # or we just append the generic "Question: ..." line if the runner handles the specific text
            # For this assembler, we assume the runner will append the specific question text or
            # we append the template for the question part.
            # Based on standard ICL, we usually end with "Question: [Actual Question]\nAnswer:"
            # Here we assume the caller passes the specific question for the test instance separately
            # or we just leave the prompt ending in "Answer:"
            final_suffix = self.config.get("prompt", {}).get("final_suffix", "Question:\nAnswer:")
            parts.append(final_suffix)

        return self.separator.join(parts)

    def generate_prompt_for_strategy(
        self,
        examples: List[Dict[str, Any]],
        strategy: str,
        seed: Optional[int] = None
    ) -> str:
        """
        Generates a prompt based on the specified ordering strategy.
        
        Args:
            examples: List of example dictionaries.
            strategy: One of 'logical_ascending', 'logical_random', 'original_cds'.
            seed: Random seed (required for 'logical_random').
            
        Returns:
            Formatted prompt string.
        """
        ordered_examples = examples.copy()
        
        if strategy == "logical_ascending":
            ordered_examples = self.sort_by_logical_ascending(ordered_examples)
        elif strategy == "logical_random":
            if seed is None:
                raise ValueError("Seed is required for 'logical_random' strategy")
            ordered_examples = self.shuffle_deterministic(ordered_examples, seed)
        elif strategy == "original_cds":
            ordered_examples = self.sort_by_original_cds(ordered_examples)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        return self.assemble_prompt(ordered_examples)


def main():
    """
    Main entry point for testing prompt generation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate prompts from DAG manifest")
    parser.add_argument("--manifest", type=str, required=True, help="Path to dag_manifest.json")
    parser.add_argument("--output", type=str, required=True, help="Path to output prompt file")
    parser.add_argument("--strategy", type=str, default="logical_ascending", 
                      choices=["logical_ascending", "logical_random", "original_cds"])
    parser.add_argument("--seed", type=int, default=42, help="Random seed for random strategy")
    
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    
    generator = PromptGenerator()
    examples = generator.load_examples_from_manifest(manifest_path)
    
    logger.info(f"Loaded {len(examples)} examples from {manifest_path}")
    logger.info(f"Generating prompt with strategy: {args.strategy}")
    
    prompt = generator.generate_prompt_for_strategy(
        examples, 
        strategy=args.strategy, 
        seed=args.seed
    )
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(prompt)
        
    logger.info(f"Prompt saved to {output_path}")
    print(f"Generated prompt length: {len(prompt)} characters")


if __name__ == "__main__":
    main()
