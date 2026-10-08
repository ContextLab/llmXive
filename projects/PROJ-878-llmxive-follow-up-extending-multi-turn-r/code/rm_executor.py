import os
import sys
import json
import csv
import logging
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_utils import configure_logging
from utils.graph_utils import is_dag, nesting_depth, branching_factor, longest_path

load_dotenv()

logger = logging.getLogger(__name__)

class ReflectiveMaskingExecutor:
    """
    Executes the Reflective Masking loop on a CPU-feasible baseline.
    Loads a pre-trained Mask Diffusion Model (or equivalent MDM) and
    performs token-level masking, prediction, and unmasking to solve logical puzzles.
    """

    def __init__(self, model_path: str, device: str = "cpu", max_turns: int = 50):
        """
        Initialize the executor with the model and tokenizer.

        Args:
            model_path: HuggingFace repo ID or local path to the model.
            device: Device to run inference on ('cpu' or 'cuda').
            max_turns: Maximum number of reflective turns allowed per instance.
        """
        self.device = torch.device(device)
        self.max_turns = max_turns
        self.model_path = model_path

        logger.info(f"Loading model from {model_path} on {device}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForMaskedLM.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _mask_tokens(self, input_ids: torch.Tensor, mask_indices: List[int]) -> torch.Tensor:
        """
        Apply masking to specific token indices.

        Args:
            input_ids: Tensor of token IDs.
            mask_indices: List of indices to mask.

        Returns:
            Tensor with masked tokens replaced by mask token ID.
        """
        masked_ids = input_ids.clone()
        mask_token_id = self.tokenizer.mask_token_id
        if mask_token_id is None:
            raise ValueError("Tokenizer does not have a mask token.")
        
        for idx in mask_indices:
            if 0 <= idx < masked_ids.shape[1]:
                masked_ids[0, idx] = mask_token_id
        return masked_ids

    def _predict_tokens(self, input_ids: torch.Tensor, mask_indices: List[int]) -> List[int]:
        """
        Predict tokens at masked positions.

        Args:
            input_ids: Tensor of token IDs (with mask tokens).
            mask_indices: List of indices that are masked.

        Returns:
            List of predicted token IDs for the masked positions.
        """
        with torch.no_grad():
            outputs = self.model(input_ids)
            logits = outputs.logits

        predictions = []
        for idx in mask_indices:
            if 0 <= idx < logits.shape[1]:
                token_logits = logits[0, idx, :]
                predicted_token = torch.argmax(token_logits).item()
                predictions.append(predicted_token)
            else:
                predictions.append(self.tokenizer.unk_token_id)
        
        return predictions

    def _extract_path_from_output(self, output_text: str) -> List[str]:
        """
        Extract the logical path from the model's output text.
        This is a placeholder implementation; real logic depends on the prompt template.
        """
        # Simple heuristic: assume path is in a specific format or extract keywords
        # In a real scenario, this would parse the specific output structure
        words = output_text.split()
        # Filter for potential path elements (e.g., starting with 'step', 'node', etc.)
        path_elements = [w.strip(".,") for w in words if w.strip(".,").lower().startswith(('step', 'node', 'path'))]
        return path_elements if path_elements else ["unknown_path"]

    def execute_turn(self, text: str, current_path: List[str], turn: int) -> Dict[str, Any]:
        """
        Perform a single turn of the reflective masking loop.

        Args:
            text: The puzzle text.
            current_path: The path accumulated so far.
            turn: Current turn number.

        Returns:
            Dictionary containing the new path, status, and intermediate data.
        """
        # Prepare input
        prompt = f"Current Path: {', '.join(current_path)}\nSolve the puzzle: {text}"
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        input_ids = inputs["input_ids"].to(self.device)

        # Identify indices to mask (e.g., the last few tokens or specific logical steps)
        # For demonstration, we mask the last 10% of tokens
        seq_len = input_ids.shape[1]
        mask_count = max(1, seq_len // 10)
        mask_indices = list(range(seq_len - mask_count, seq_len))

        # Apply masking
        masked_input_ids = self._mask_tokens(input_ids, mask_indices)

        # Predict
        predicted_tokens = self._predict_tokens(masked_input_ids, mask_indices)

        # Construct new input
        new_input_ids = masked_input_ids.clone()
        for i, idx in enumerate(mask_indices):
            if i < len(predicted_tokens):
                new_input_ids[0, idx] = predicted_tokens[i]

        # Decode
        output_text = self.tokenizer.decode(new_input_ids[0], skip_special_tokens=True)

        # Extract path
        new_path = self._extract_path_from_output(output_text)

        # Check convergence (simplified: check if path length increased or changed)
        converged = len(new_path) > len(current_path) and new_path[-1] != current_path[-1] if current_path else True

        return {
            "turn": turn,
            "output_text": output_text,
            "path": new_path,
            "converged": converged
        }

    def run(self, puzzle_text: str, ground_truth_path: List[str]) -> Dict[str, Any]:
        """
        Run the full reflective masking loop for a single puzzle.

        Args:
            puzzle_text: The text of the puzzle.
            ground_truth_path: The expected ground truth path.

        Returns:
            Dictionary with execution results.
        """
        current_path = []
        turns = 0
        status = "timeout"
        final_path = []

        for turn in range(1, self.max_turns + 1):
            result = self.execute_turn(puzzle_text, current_path, turn)
            current_path = result["path"]
            turns = turn

            if result["converged"]:
                # Check if we reached a stable state or matched ground truth (simplified)
                if len(current_path) > 0:
                    status = "success"
                    final_path = current_path
                    break

        # If loop finished without convergence
        if status == "timeout" and len(current_path) > 0:
            final_path = current_path
            # Check if it actually converged on the last step
            # In a real implementation, we'd have a more robust convergence check
            if turns == self.max_turns:
                status = "timeout"

        return {
            "turns_to_converge": turns,
            "convergence_status": status,
            "final_path": final_path,
            "ground_truth_path": ground_truth_path
        }

def load_puzzles(input_path: str) -> List[Dict[str, Any]]:
    """
    Load puzzles from a JSONL file.
    """
    puzzles = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                puzzles.append(json.loads(line))
    return puzzles

def write_results(results: List[Dict[str, Any]], output_path: str):
    """
    Write execution results to a CSV file.
    """
    if not results:
        logger.warning("No results to write.")
        return

    fieldnames = [
        "instance_id",
        "turns_to_converge",
        "convergence_status",
        "path_coverage",
        "divergence_from_ground_truth"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            # Calculate divergence (Jaccard distance placeholder)
            # In a real scenario, this would be computed based on actual paths
            gt = set(res.get("ground_truth_path", []))
            pred = set(res.get("final_path", []))
            intersection = len(gt.intersection(pred))
            union = len(gt.union(pred))
            jaccard_sim = intersection / union if union > 0 else 0.0
            divergence = 1.0 - jaccard_sim

            row = {
                "instance_id": res.get("instance_id", "unknown"),
                "turns_to_converge": res["turns_to_converge"],
                "convergence_status": res["convergence_status"],
                "path_coverage": 0.0, # Placeholder, to be calculated by ILV
                "divergence_from_ground_truth": divergence
            }
            writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description="Reflective Masking Executor")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSONL file")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file")
    parser.add_argument("--max-turns", type=int, default=50, help="Maximum turns per instance")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size (not used in CPU single-threaded)")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run on")
    args = parser.parse_args()

    configure_logging()

    # Load environment config
    model_path = os.getenv("MODEL_PATH")
    if not model_path:
        logger.error("MODEL_PATH not found in .env. Please set it.")
        sys.exit(1)

    logger.info(f"Starting execution with model: {model_path}, device: {args.device}")

    # Check input file
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Initialize executor
    executor = ReflectiveMaskingExecutor(model_path=model_path, device=args.device, max_turns=args.max_turns)

    # Load puzzles
    puzzles = load_puzzles(args.input)
    logger.info(f"Loaded {len(puzzles)} puzzles.")

    results = []
    start_time = time.time()

    for i, puzzle in enumerate(puzzles):
        instance_id = puzzle.get("instance_id", f"puzzle_{i}")
        text = puzzle.get("text", "")
        ground_truth_path = puzzle.get("ground_truth_path", [])

        logger.info(f"Processing {instance_id} ({i+1}/{len(puzzles)})")

        try:
            result = executor.run(text, ground_truth_path)
            result["instance_id"] = instance_id
            result["ground_truth_path"] = ground_truth_path
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing {instance_id}: {e}")
            results.append({
                "instance_id": instance_id,
                "turns_to_converge": 0,
                "convergence_status": "failure",
                "final_path": [],
                "ground_truth_path": ground_truth_path
            })

    end_time = time.time()
    logger.info(f"Execution completed in {end_time - start_time:.2f} seconds.")

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    write_results(results, args.output)
    logger.info(f"Results written to {args.output}")

if __name__ == "__main__":
    main()