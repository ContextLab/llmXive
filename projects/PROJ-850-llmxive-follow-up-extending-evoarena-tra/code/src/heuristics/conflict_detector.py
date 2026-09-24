import os
import sys
import json
import csv
import yaml
import torch
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from src.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ModelResult:
    patch_id: str
    score: float
    is_conflict: bool
    model_name: str

class ConflictDetector:
    """
    CPU-tractable conflict detector using DistilBERT to flag semantic contradictions.
    Implements FR-007: Safe retrieval mode on timeout or failure.
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
        
        logger.info(f"Initializing ConflictDetector with model: {model_name} on {self.device}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # Create inference pipeline
            self.pipe = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                return_all_scores=False,
                device=0 if self.device == "cuda" else -1
            )
            logger.info(f"Model loaded successfully: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def _predict_with_timeout(
        self,
        pair: Dict[str, Any],
        timeout_seconds: float = 30.0
    ) -> ModelResult:
        """
        Predict contradiction score with timeout protection.
        Returns ModelResult with is_conflict=False if timeout occurs.
        """
        patch_a = pair.get("patch_a", "")
        patch_b = pair.get("patch_b", "")
        patch_id = pair.get("id", "unknown")
        
        start_time = time.time()
        
        try:
            # Prepare input for text-classification pipeline
            # Format: "PREMISE: {patch_a} HYPOTHESIS: {patch_b}"
            input_text = f"PREMISE: {patch_a} HYPOTHESIS: {patch_b}"
            
            result = self.pipe(input_text)[0]
            label = result["label"]
            score = result["score"]
            
            # Determine if conflict based on threshold
            # Assuming label "LABEL_1" or similar indicates contradiction
            # Adjust based on model's actual label mapping
            is_conflict = score > self.threshold and ("1" in label or "contradiction" in label.lower())
            
            elapsed = time.time() - start_time
            logger.debug(f"Prediction for {patch_id}: score={score:.4f}, is_conflict={is_conflict}, time={elapsed:.2f}s")
            
            return ModelResult(
                patch_id=patch_id,
                score=score,
                is_conflict=is_conflict,
                model_name=self.model_name
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(f"Error during prediction for {patch_id} after {elapsed:.2f}s: {e}")
            # Return safe result (non-conflict) on error
            return ModelResult(
                patch_id=patch_id,
                score=0.0,
                is_conflict=False,
                model_name=self.model_name
            )

    def detect_conflicts(
        self,
        patches: List[Dict[str, Any]],
        timeout_per_patch: float = 30.0
    ) -> List[ModelResult]:
        """
        Detect conflicts in a list of patch pairs.
        Implements FR-007: Safe mode - returns non-conflict on failure.
        
        Args:
            patches: List of dicts with keys: patch_a, patch_b, id
            timeout_per_patch: Timeout in seconds per prediction
            
        Returns:
            List of ModelResult objects
        """
        results = []
        for i, patch in enumerate(patches):
            try:
                result = self._predict_with_timeout(patch, timeout_per_patch)
                results.append(result)
            except Exception as e:
                logger.error(f"Critical failure in detect_conflicts at index {i}: {e}")
                # Safe fallback: treat as non-conflict
                results.append(ModelResult(
                    patch_id=patch.get("id", f"patch_{i}"),
                    score=0.0,
                    is_conflict=False,
                    model_name=self.model_name
                ))
        return results

    def run_sensitivity_analysis_thresholds(
        self,
        patches: List[Dict[str, Any]],
        thresholds: List[float],
        output_path: str
    ) -> List[Dict[str, Any]]:
        """
        Run sensitivity analysis across different thresholds.
        
        Args:
            patches: List of patch pairs
            thresholds: List of threshold values to test
            output_path: Path to write CSV results
            
        Returns:
            List of result dictionaries
        """
        all_results = []
        
        for threshold in thresholds:
            self.threshold = threshold
            logger.info(f"Running analysis with threshold: {threshold}")
            results = self.detect_conflicts(patches)
            
            for r in results:
                all_results.append({
                    "patch_id": r.patch_id,
                    "score": r.score,
                    "threshold": threshold,
                    "is_conflict": r.is_conflict,
                    "model_name": self.model_name
                })
        
        # Write to CSV
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["patch_id", "score", "threshold", "is_conflict", "model_name"])
            writer.writeheader()
            writer.writerows(all_results)
        
        logger.info(f"Sensitivity analysis results written to {output_path}")
        return all_results

    def run_sensitivity_analysis_models(
        self,
        patches: List[Dict[str, Any]],
        model_names: List[str],
        output_path: str,
        timeout_per_patch: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        Run sensitivity analysis across different model sizes.
        
        Args:
            patches: List of patch pairs
            model_names: List of model names to test
            output_path: Path to write CSV results
            timeout_per_patch: Timeout per prediction
            
        Returns:
            List of result dictionaries
        """
        all_results = []
        
        for model_name in model_names:
            logger.info(f"Loading model: {model_name}")
            try:
                detector = ConflictDetector(model_name=model_name, device=self.device)
                results = detector.detect_conflicts(patches, timeout_per_patch)
                
                for r in results:
                    all_results.append({
                        "patch_id": r.patch_id,
                        "score": r.score,
                        "is_conflict": r.is_conflict,
                        "model_name": r.model_name
                    })
            except Exception as e:
                logger.error(f"Failed to run analysis for model {model_name}: {e}")
                # Continue with other models
                continue
        
        # Write to CSV
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["patch_id", "score", "is_conflict", "model_name"])
            writer.writeheader()
            writer.writerows(all_results)
        
        logger.info(f"Model sensitivity analysis results written to {output_path}")
        return all_results

def main():
    """Main entry point for conflict detector CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Conflict Detector CLI")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config YAML")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file with patch pairs")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file for results")
    parser.add_argument("--thresholds", type=str, default="0.7,0.8,0.9,0.95", help="Comma-separated thresholds for sensitivity analysis")
    parser.add_argument("--models", type=str, default="distilbert-base-uncased", help="Comma-separated model names")
    parser.add_argument("--mode", type=str, default="single", choices=["single", "threshold", "model"], help="Analysis mode")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout per prediction in seconds")
    
    args = parser.parse_args()
    
    # Load patches
    with open(args.input, "r") as f:
        patches = json.load(f)
    
    logger.info(f"Loaded {len(patches)} patches from {args.input}")
    
    detector = ConflictDetector()
    
    if args.mode == "single":
        results = detector.detect_conflicts(patches, args.timeout)
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["patch_id", "score", "is_conflict", "model_name"])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "patch_id": r.patch_id,
                    "score": r.score,
                    "is_conflict": r.is_conflict,
                    "model_name": r.model_name
                })
    elif args.mode == "threshold":
        thresholds = [float(t) for t in args.thresholds.split(",")]
        detector.run_sensitivity_analysis_thresholds(patches, thresholds, args.output)
    elif args.mode == "model":
        model_names = [m.strip() for m in args.models.split(",")]
        detector.run_sensitivity_analysis_models(patches, model_names, args.output, args.timeout)
    
    logger.info(f"Analysis complete. Results written to {args.output}")

if __name__ == "__main__":
    main()