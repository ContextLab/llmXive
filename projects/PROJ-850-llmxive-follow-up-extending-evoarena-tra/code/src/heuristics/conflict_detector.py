import os
import sys
import json
import csv
import yaml
import torch
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import logging utility from project structure
try:
    from src.utils.logging import get_logger, ExecutionTimer, log_metrics
except ImportError:
    # Fallback if run as standalone script without package structure
    def get_logger(name):
        return logging.getLogger(name)
    class ExecutionTimer:
        def __init__(self, name): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    def log_metrics(*args, **kwargs): pass

logger = get_logger(__name__)

class ConflictDetector:
    """
    Conflict Detector using DistilBERT for semantic contradiction scoring.
    Implements error handling and safe retrieval fallback (FR-007).
    """
    
    def __init__(
        self, 
        model_name: str = "distilbert-base-uncased", 
        threshold: float = 0.90,
        device: Optional[str] = None
    ):
        self.model_name = model_name
        self.threshold = threshold
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        """Load the transformer model and tokenizer."""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            logger.info(f"Loading model: {self.model_name} on {self.device}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=2
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

    def detect_conflict(self, patch_a: str, patch_b: str) -> Tuple[bool, float]:
        """
        Detects if patch_b contradicts patch_a.
        Returns (is_conflict, confidence_score).
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not initialized.")

        try:
            inputs = self.tokenizer(
                patch_a, 
                patch_b, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512,
                padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)
                # Assuming label 1 is 'contradiction' or 'conflict' based on training
                # Standard MNLI/Contradiction setup: 0=Entailment, 1=Neutral, 2=Contradiction
                # For binary contradiction detection, we assume 1 is conflict if trained as such,
                # or we map the specific contradiction label.
                # Here we assume a binary classification where 1 = Conflict.
                conflict_prob = probs[0, 1].item()
            
            is_conflict = conflict_prob > self.threshold
            return is_conflict, conflict_prob

        except torch.cuda.OutOfMemoryError:
            logger.error("CUDA OOM during inference. Falling back to CPU if available.")
            if self.device == "cuda":
                self.device = "cpu"
                self.model.to("cpu")
                return self.detect_conflict(patch_a, patch_b)
            raise
        except Exception as e:
            logger.error(f"Inference error: {e}")
            raise

    def run_sensitivity_analysis_thresholds(self, thresholds: List[float], synthetic_data_path: str) -> List[Dict[str, Any]]:
        """
        Runs sensitivity analysis across different thresholds.
        """
        results = []
        if not Path(synthetic_data_path).exists():
            logger.warning(f"Synthetic data path not found: {synthetic_data_path}")
            return results

        with open(synthetic_data_path, 'r') as f:
            data = json.load(f)

        for thresh in thresholds:
            self.threshold = thresh
            tp, tn, fp, fn = 0, 0, 0, 0
            
            for item in data:
                try:
                    is_conflict, _ = self.detect_conflict(item['patch_a'], item['patch_b'])
                    actual = item['is_contradiction']
                    if is_conflict and actual: tp += 1
                    elif is_conflict and not actual: fp += 1
                    elif not is_conflict and actual: fn += 1
                    else: tn += 1
                except Exception as e:
                    logger.error(f"Error processing item with threshold {thresh}: {e}")
                    continue

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            results.append({
                "threshold": thresh,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp": tp, "tn": tn, "fp": fp, "fn": fn
            })

        return results

    def get_safe_retrieval_patches(
        self, 
        all_patches: List[Dict[str, Any]], 
        conflict_flags: List[bool], 
        max_safe_non_conflict: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Implements Safe Mode retrieval (FR-007).
        Returns the latest state patch plus the most recent non-conflict patches.
        
        Args:
            all_patches: List of all state patches in chronological order (oldest to newest).
            conflict_flags: List of booleans indicating if each patch is a conflict.
            max_safe_non_conflict: Number of recent non-conflict patches to include (default 2).
        
        Returns:
            List of patches to retrieve for safe context.
        """
        if not all_patches:
            logger.warning("No patches provided for safe retrieval.")
            return []

        # Ensure lists are aligned
        if len(all_patches) != len(conflict_flags):
            raise ValueError("all_patches and conflict_flags must be of equal length.")

        # The latest state is always the last element (assuming chronological order)
        latest_patch = all_patches[-1]
        
        # Identify non-conflict patches
        safe_candidates = []
        for i, (patch, is_conflict) in enumerate(zip(all_patches, conflict_flags)):
            if not is_conflict:
                safe_candidates.append(patch)

        # Sort candidates by index (chronological) to get the most recent ones
        # Since we iterate in order, the list is already chronological.
        # We need the most recent, so we take the last `max_safe_non_conflict` items.
        recent_non_conflicts = safe_candidates[-max_safe_non_conflict:] if len(safe_candidates) >= max_safe_non_conflict else safe_candidates

        # If the latest patch itself is a conflict, it is still included as "latest state"
        # per the safe mode definition: "Retrieve latest state plus...".
        # However, if the latest state is a conflict, we might want to ensure we don't 
        # double count if it's also in the non-conflict list (it won't be).
        
        # Construct final list: [Latest State] + [Recent Non-Conflicts]
        # Note: If latest is non-conflict, it might be duplicated if we just append.
        # The spec says "latest state plus...".
        
        final_patches = [latest_patch]
        
        # Add recent non-conflicts, ensuring we don't duplicate the latest if it's non-conflict
        for patch in recent_non_conflicts:
            if patch != latest_patch:
                final_patches.append(patch)

        logger.info(f"Safe retrieval mode: Selected {len(final_patches)} patches (1 latest + {len(final_patches)-1} non-conflicts).")
        return final_patches

    def handle_retrieval_with_fallback(
        self, 
        all_patches: List[Dict[str, Any]], 
        timeout_seconds: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for retrieval with error handling and fallback (FR-007).
        Attempts to detect conflicts. If timeout or failure occurs, returns safe patches.
        """
        conflict_flags = []
        
        try:
            with ExecutionTimer("Conflict Detection"):
                for patch in all_patches:
                    # Assuming patch has 'patch_a' and 'patch_b' keys for comparison
                    # If patch is a single state, we might compare against a baseline or previous state.
                    # For this implementation, we assume the input `all_patches` are pairs or
                    # the logic is applied to a sequence where we compare current vs previous.
                    # Simplified: We assume `all_patches` are actually the 'patch_b' candidates
                    # and we compare against a stored 'patch_a' (context).
                    # However, the task description implies filtering a list of patches.
                    # Let's assume `all_patches` contains items with 'patch_a' and 'patch_b'.
                    
                    if 'patch_a' in patch and 'patch_b' in patch:
                        is_conflict, _ = self.detect_conflict(patch['patch_a'], patch['patch_b'])
                        conflict_flags.append(is_conflict)
                    else:
                        # If structure is different, assume no conflict detected for this item
                        # or fallback to safe mode immediately if structure is invalid
                        logger.warning(f"Invalid patch structure: {patch.get('id', 'unknown')}")
                        raise ValueError("Invalid patch structure for conflict detection.")
        
        except (TimeoutError, torch.cuda.OutOfMemoryError, Exception) as e:
            logger.error(f"Conflict detection failed or timed out: {e}. Triggering Safe Mode.")
            # Trigger Safe Mode: Return latest state + 2 most recent non-conflict (assuming all are non-conflict in safe mode)
            # Since we failed to detect, we treat all as non-conflict for the purpose of fallback selection
            # or just return the latest + 2 previous.
            # The spec says "Retrieve latest state plus a small number of the most recent non-conflict patches".
            # If detection fails, we assume the system cannot distinguish, so we take the most recent ones.
            # We will treat all as non-conflict for the fallback selection logic.
            safe_flags = [False] * len(all_patches)
            return self.get_safe_retrieval_patches(all_patches, safe_flags, max_safe_non_conflict=2)

        return self.get_safe_retrieval_patches(all_patches, conflict_flags, max_safe_non_conflict=2)


    def run_sensitivity_analysis_models(self, model_names: List[str], synthetic_data_path: str) -> List[Dict[str, Any]]:
        """
        Runs sensitivity analysis across different model sizes.
        """
        results = []
        original_model = self.model_name
        
        for model_name in model_names:
            logger.info(f"Running analysis for model: {model_name}")
            try:
                self.model_name = model_name
                self._load_model() # Reload model
                
                # Run with default threshold
                analysis_results = self.run_sensitivity_analysis_thresholds([self.threshold], synthetic_data_path)
                if analysis_results:
                    res = analysis_results[0]
                    res['model_name'] = model_name
                    results.append(res)
            except Exception as e:
                logger.error(f"Failed to run analysis for {model_name}: {e}")
                results.append({
                    "model_name": model_name,
                    "error": str(e),
                    "precision": 0, "recall": 0, "f1": 0
                })
            finally:
                # Restore original model
                self.model_name = original_model
                self._load_model()
        
        return results


def main():
    """
    Main entry point for CLI or direct execution.
    """
    # Example usage
    detector = ConflictDetector(model_name="distilbert-base-uncased")
    
    # Load synthetic data if available for a quick sanity check
    data_path = "data/raw/synthetic_pairs.json"
    if os.path.exists(data_path):
        logger.info(f"Running quick test on {data_path}")
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        if len(data) > 0:
            sample = data[0]
            is_conflict, score = detector.detect_conflict(sample['patch_a'], sample['patch_b'])
            logger.info(f"Sample detection: Conflict={is_conflict}, Score={score:.4f}")
    else:
        logger.warning(f"Data file {data_path} not found. Skipping sample test.")

if __name__ == "__main__":
    main()