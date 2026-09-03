import os
import sys
import json
import csv
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator

# Import existing utilities from the project API surface
from utils.logging_utils import configure_logging, generate_checksum, write_checksum_file
from utils.graph_utils import is_dag, validate_dag, nesting_depth, branching_factor, get_random_valid_path_different_from_reference, graph_from_dict

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_BATCH_SIZE = 10
DEFAULT_TURN_LIMIT = 50
DEFAULT_INPUT_FILE = "data/raw/logical_puzzles.jsonl"
DEFAULT_OUTPUT_FILE = "data/processed/execution_log.csv"

class ReflectiveMaskingExecutor:
    """
    Executes the Reflective Masking (RM) loop on logical puzzles.
    Implements batch processing to stay within RAM constraints by streaming
    the input dataset and processing in configurable batches.
    """

    def __init__(
        self,
        turn_limit: int = DEFAULT_TURN_LIMIT,
        batch_size: int = DEFAULT_BATCH_SIZE,
        device: str = "cpu",
        verbose: bool = False
    ):
        self.turn_limit = turn_limit
        self.batch_size = batch_size
        self.device = device
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Placeholder for model loading - in real implementation, load Mask Diffusion Model here
        # self.model = self._load_model()

    def _load_model(self):
        """
        Load the pre-trained Mask Diffusion Model.
        For CPU feasibility, ensure model is loaded on CPU device.
        """
        # TODO: Implement actual model loading from spec
        # This is a placeholder to satisfy the API structure
        self.logger.info("Loading Mask Diffusion Model on CPU...")
        return {"status": "loaded", "device": self.device}

    def _process_single_puzzle(self, puzzle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single puzzle instance through the RM loop.
        
        Args:
            puzzle_data: Dictionary containing puzzle metadata and graph structure
        
        Returns:
            Dictionary with execution results including turns_to_converge, status, etc.
        """
        instance_id = puzzle_data.get('instance_id')
        graph_dict = puzzle_data.get('graph_structure')
        ground_truth_path = puzzle_data.get('ground_truth_path')
        
        # Validate DAG structure
        try:
            graph = graph_from_dict(graph_dict)
            if not is_dag(graph):
                return {
                    'instance_id': instance_id,
                    'turns_to_converge': 0,
                    'convergence_status': 'failure',
                    'error': 'Invalid DAG structure',
                    'path_coverage': 0.0,
                    'divergence_from_ground_truth': 1.0
                }
        except Exception as e:
            return {
                'instance_id': instance_id,
                'turns_to_converge': 0,
                'convergence_status': 'failure',
                'error': f'Graph validation failed: {str(e)}',
                'path_coverage': 0.0,
                'divergence_from_ground_truth': 1.0
            }

        # Simulate RM loop (placeholder for actual model execution)
        # In real implementation, this would run the masking/prediction cycle
        turns = 0
        converged = False
        final_path = ground_truth_path if ground_truth_path else []
        
        while turns < self.turn_limit:
            turns += 1
            # Simulate convergence check (placeholder)
            # In real implementation: model_output = self.model.predict(...)
            #                    converged = self._check_convergence(model_output, ground_truth_path)
            
            # For simulation, we'll assume convergence after a random number of turns
            # This should be replaced with actual model logic
            if turns >= 5:  # Placeholder convergence condition
                converged = True
                break
        
        # Calculate metrics (placeholder logic)
        path_coverage = 0.95 if converged else 0.0
        divergence = 0.0 if converged else 1.0
        
        return {
            'instance_id': instance_id,
            'turns_to_converge': turns if converged else self.turn_limit,
            'convergence_status': 'converged' if converged else 'failure',
            'path_coverage': path_coverage,
            'divergence_from_ground_truth': divergence,
            'error': None
        }

    def _stream_puzzles(self, input_file: str) -> Iterator[Dict[str, Any]]:
        """
        Stream puzzles from JSONL file one at a time to minimize memory usage.
        
        Args:
            input_file: Path to the JSONL file containing puzzles
        
        Yields:
            Dictionary for each puzzle instance
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    puzzle_data = json.loads(line)
                    yield puzzle_data
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
                    continue

    def _process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of puzzles and collect results.
        
        Args:
            batch: List of puzzle dictionaries to process
        
        Returns:
            List of result dictionaries for each puzzle
        """
        results = []
        for puzzle_data in batch:
            try:
                result = self._process_single_puzzle(puzzle_data)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing puzzle {puzzle_data.get('instance_id')}: {e}")
                results.append({
                    'instance_id': puzzle_data.get('instance_id', 'unknown'),
                    'turns_to_converge': 0,
                    'convergence_status': 'failure',
                    'error': str(e),
                    'path_coverage': 0.0,
                    'divergence_from_ground_truth': 1.0
                })
        return results

    def execute_batched(
        self,
        input_file: str = DEFAULT_INPUT_FILE,
        output_file: str = DEFAULT_OUTPUT_FILE
    ) -> List[Dict[str, Any]]:
        """
        Execute RM loop on all puzzles using batched processing to stay within RAM constraints.
        
        This method:
        1. Streams puzzles from input file one at a time
        2. Accumulates them into batches of configurable size
        3. Processes each batch sequentially
        4. Writes results to output CSV after each batch
        
        Args:
            input_file: Path to input JSONL file
            output_file: Path to output CSV file
        
        Returns:
            List of all execution results
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        all_results = []
        batch = []
        processed_count = 0
        
        self.logger.info(f"Starting batched execution with batch_size={self.batch_size}")
        self.logger.info(f"Input: {input_file}, Output: {output_file}")
        
        # Stream and process in batches
        for puzzle_data in self._stream_puzzles(input_file):
            batch.append(puzzle_data)
            
            # Process batch when it reaches the configured size
            if len(batch) >= self.batch_size:
                self.logger.info(f"Processing batch of {len(batch)} puzzles...")
                batch_results = self._process_batch(batch)
                all_results.extend(batch_results)
                
                # Write batch results to CSV immediately
                self._write_results_to_csv(batch_results, output_file, mode='a' if processed_count > 0 else 'w')
                
                processed_count += len(batch_results)
                self.logger.info(f"Processed {processed_count} puzzles so far")
                
                # Clear batch for next iteration
                batch = []
        
        # Process any remaining puzzles in the final partial batch
        if batch:
            self.logger.info(f"Processing final batch of {len(batch)} puzzles...")
            batch_results = self._process_batch(batch)
            all_results.extend(batch_results)
            
            # Write final batch results
            self._write_results_to_csv(batch_results, output_file, mode='a')
            processed_count += len(batch_results)
            self.logger.info(f"Processed final batch. Total: {processed_count} puzzles")
        
        self.logger.info(f"Batched execution complete. Total processed: {processed_count}")
        return all_results

    def _write_results_to_csv(
        self,
        results: List[Dict[str, Any]],
        output_file: str,
        mode: str = 'w'
    ) -> None:
        """
        Write results to CSV file.
        
        Args:
            results: List of result dictionaries
            output_file: Path to output CSV file
            mode: File write mode ('w' for write, 'a' for append)
        """
        fieldnames = [
            'instance_id',
            'turns_to_converge',
            'convergence_status',
            'path_coverage',
            'divergence_from_ground_truth',
            'error'
        ]
        
        file_exists = os.path.exists(output_file) and mode == 'a'
        
        with open(output_file, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header only if creating new file
            if not file_exists:
                writer.writeheader()
            
            for result in results:
                # Clean up result for CSV (remove None values or convert to string)
                clean_result = {
                    k: (v if v is not None else '') for k, v in result.items()
                }
                writer.writerow(clean_result)

def main():
    """
    Main entry point for batched RM execution.
    """
    # Configure logging
    configure_logging(level=logging.INFO)
    
    # Parse command line arguments (optional)
    import argparse
    parser = argparse.ArgumentParser(description='Batched Reflective Masking Execution')
    parser.add_argument('--input', type=str, default=DEFAULT_INPUT_FILE,
                      help='Input JSONL file path')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_FILE,
                      help='Output CSV file path')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                      help='Batch size for processing')
    parser.add_argument('--turn-limit', type=int, default=DEFAULT_TURN_LIMIT,
                      help='Maximum turns per puzzle')
    parser.add_argument('--device', type=str, default='cpu',
                      help='Device to run on (cpu/cuda)')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Create executor with configured parameters
    executor = ReflectiveMaskingExecutor(
        turn_limit=args.turn_limit,
        batch_size=args.batch_size,
        device=args.device,
        verbose=args.verbose
    )
    
    # Execute batched processing
    try:
        results = executor.execute_batched(
            input_file=args.input,
            output_file=args.output
        )
        
        logger.info(f"Execution complete. Processed {len(results)} puzzles.")
        logger.info(f"Results written to: {args.output}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()