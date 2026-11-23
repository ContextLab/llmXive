"""
Hybrid Generator: Wrapper integrating HybridController with the video generator.
Implements dynamic prompt re-conditioning via correction tokens.
"""
import json
import os
import sys
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import from project API surface
from naive_generator import (
    load_verification_status,
    load_ground_truth_subset,
    generate_synthetic_frames,
    save_synthetic_frames_to_video,
    generate_methodological_validation_report,
    generate_real_videos,
    main as naive_main
)
from symbolic_engine import SymbolicEngine, ActionType, ObjectState
from hybrid_controller import HybridController, DiscrepancyReport, HybridControlState
from utils.resource_logger import ResourceMonitor, log_resource_usage
from utils.seed_manager import set_seed


class HybridGenerator:
    """
    Wrapper that integrates HybridController with the generator.
    When a discrepancy is detected, it modifies the text prompt string
    passed to the model's tokenizer (dynamic prompt re-conditioning).
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        output_dir: str = "data",
        seed: int = 42,
        use_real_model: bool = True
    ):
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.seed = seed
        self.use_real_model = use_real_model
        
        # Initialize components
        self.symbolic_engine = SymbolicEngine()
        self.controller = HybridController()
        self.resource_monitor = ResourceMonitor()
        
        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "videos").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        (self.output_dir / "results").mkdir(exist_ok=True)

    def _load_verification_status(self) -> Dict[str, Any]:
        """Load model verification status."""
        verification_path = self.output_dir / "model_verification.json"
        if not verification_path.exists():
            return {"status": "MISSING", "model_path": None}
        
        with open(verification_path, 'r') as f:
            return json.load(f)

    def _generate_initial_prompt(self, action: Dict[str, Any]) -> str:
        """Generate the initial prompt based on the action."""
        action_type = action.get("type", "move")
        target = action.get("target", "unknown")
        return f"The character {action_type} towards {target}."

    def _apply_correction_token(self, base_prompt: str, discrepancy: DiscrepancyReport) -> str:
        """
        Apply correction token to the prompt based on discrepancy.
        This implements the dynamic prompt re-conditioning mechanism.
        """
        correction_token = discrepancy.correction_token
        
        if correction_token:
            # Inject correction token into the prompt
            # Format: "base_prompt [CORRECTION_TOKEN]"
            modified_prompt = f"{base_prompt} {correction_token}"
            return modified_prompt
        
        return base_prompt

    def _simulate_model_generation(self, prompt: str, frame_id: int) -> List[List[int]]:
        """
        Simulate model generation for testing purposes.
        In a real implementation, this would call the actual model's tokenizer and generator.
        Returns a list of simulated frame pixel values (grayscale).
        """
        # Simulate frame generation based on prompt hash for determinism
        random.seed(hash(prompt) % (2**32))
        height, width = 64, 64
        frame = [[random.randint(0, 255) for _ in range(width)] for _ in range(height)]
        return frame

    def generate_sequence(
        self,
        action_sequence: List[Dict[str, Any]],
        sequence_id: str,
        log_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a video sequence with hybrid correction.
        
        Args:
            action_sequence: List of actions to execute
            sequence_id: Unique identifier for this sequence
            log_file: Optional path to log file
            
        Returns:
            Dictionary containing generation results and metrics
        """
        self.resource_monitor.start()
        set_seed(self.seed)
        
        results = {
            "sequence_id": sequence_id,
            "seed": self.seed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "frames": [],
            "discrepancies": [],
            "corrections_applied": 0,
            "status": "success"
        }
        
        # Load verification status
        verification = self._load_verification_status()
        
        if verification.get("status") == "MISSING" and not self.use_real_model:
            # Generate methodological validation report
            report = generate_methodological_validation_report(
                sequence_id=sequence_id,
                reason="Model unavailable, using synthetic frames for pipeline validation"
            )
            results["status"] = "methodological_validation"
            results["report"] = report
            return results
        
        # Initialize symbolic engine state
        self.symbolic_engine.reset()
        
        # Process each action in the sequence
        for idx, action in enumerate(action_sequence):
            frame_id = idx
            
            # 1. Update symbolic engine with action
            self.symbolic_engine.execute_action(action)
            symbolic_state = self.symbolic_engine.get_current_state()
            
            # 2. Generate initial prompt
            base_prompt = self._generate_initial_prompt(action)
            
            # 3. Check for discrepancies using controller
            # In a real scenario, we would compare symbolic state with visual output
            # Here we simulate the check
            discrepancy = self.controller.check_discrepancy(
                symbolic_state=symbolic_state,
                frame_id=frame_id,
                action=action
            )
            
            # 4. Apply correction if discrepancy detected
            final_prompt = base_prompt
            if discrepancy and discrepancy.correction_token:
                final_prompt = self._apply_correction_token(base_prompt, discrepancy)
                results["corrections_applied"] += 1
                results["discrepancies"].append({
                    "frame_id": frame_id,
                    "discrepancy_type": discrepancy.discrepancy_type,
                    "correction_token": discrepancy.correction_token,
                    "original_prompt": base_prompt,
                    "modified_prompt": final_prompt
                })
            
            # 5. Generate frame (simulated)
            frame = self._simulate_model_generation(final_prompt, frame_id)
            results["frames"].append({
                "frame_id": frame_id,
                "prompt": final_prompt,
                "symbolic_state": symbolic_state,
                "frame_data": frame[:10]  # Store first 10 rows for brevity
            })
            
            # 6. Update controller state
            self.controller.update_state(discrepancy, frame_id)
            
            # Log resource usage periodically
            if idx % 10 == 0:
                self.resource_monitor.log(
                    self.output_dir / "logs" / f"realtime_seq_{sequence_id}.json",
                    step=idx
                )
        
        # Finalize resource logging
        self.resource_monitor.stop()
        resource_log = self.resource_monitor.get_summary()
        results["resource_usage"] = resource_log
        
        # Save results
        results_path = self.output_dir / "results" / f"hybrid_seq_{sequence_id}.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results

    def run_hybrid_experiment(
        self,
        num_sequences: int = 10,
        actions_per_sequence: int = 10,
        seeds: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Run the full hybrid experiment with multiple sequences and seeds.
        
        Args:
            num_sequences: Number of sequences to generate per seed
            actions_per_sequence: Number of actions per sequence
            seeds: List of random seeds to use
            
        Returns:
            Aggregated results for the experiment
        """
        if seeds is None:
            seeds = [i * 10 for i in range(num_sequences)]
        
        all_results = []
        
        for seed in seeds:
            self.seed = seed
            random.seed(seed)
            
            for seq_idx in range(num_sequences):
                sequence_id = f"hybrid_{seed}_{seq_idx}"
                
                # Generate random action sequence
                action_sequence = []
                for _ in range(actions_per_sequence):
                    action_type = random.choice(["move", "attack", "summon", "heal"])
                    action = {
                        "type": action_type,
                        "target": f"object_{random.randint(1, 10)}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    action_sequence.append(action)
                
                # Generate sequence with hybrid correction
                result = self.generate_sequence(
                    action_sequence=action_sequence,
                    sequence_id=sequence_id
                )
                
                all_results.append(result)
                
                # Log progress
                print(f"Completed sequence: {sequence_id}, "
                      f"corrections: {result['corrections_applied']}")
        
        # Aggregate results
        total_corrections = sum(r['corrections_applied'] for r in all_results)
        total_frames = sum(len(r['frames']) for r in all_results)
        
        summary = {
            "total_sequences": len(all_results),
            "total_frames": total_frames,
            "total_corrections": total_corrections,
            "average_corrections_per_sequence": total_corrections / len(all_results) if all_results else 0,
            "seeds_used": seeds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Save summary
        summary_path = self.output_dir / "results" / "hybrid_experiment_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return {
            "individual_results": all_results,
            "summary": summary
        }


def main():
    """Main entry point for the hybrid generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid Generator with Correction Tokens")
    parser.add_argument("--num-sequences", type=int, default=10, help="Number of sequences per seed")
    parser.add_argument("--actions-per-sequence", type=int, default=10, help="Number of actions per sequence")
    parser.add_argument("--seeds", type=str, default=None, help="Comma-separated list of seeds")
    parser.add_argument("--use-real-model", action="store_true", help="Use real model if available")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory")
    
    args = parser.parse_args()
    
    # Parse seeds
    seeds = None
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]
    
    # Initialize generator
    generator = HybridGenerator(
        output_dir=args.output_dir,
        use_real_model=args.use_real_model
    )
    
    # Run experiment
    print("Starting Hybrid Generator Experiment...")
    results = generator.run_hybrid_experiment(
        num_sequences=args.num_sequences,
        actions_per_sequence=args.actions_per_sequence,
        seeds=seeds
    )
    
    print(f"Experiment completed. Summary: {results['summary']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())