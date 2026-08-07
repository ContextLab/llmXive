"""
Ablation study execution pipeline.
Integrates ablation model configurations with the inference runner to generate metrics.
"""
import os
import json
import logging
import csv
import time
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Local imports based on API surface
from models.student import clone_model, freeze_attention_heads, prune_ffn_layers
from inference.runner import run_inference_on_model, get_model_paths, load_student_model
from inference.metrics import load_ablation_logits, run_ablation_metrics_calculation
from data.loader import FilteredDataLoader
from utils.logger import get_logger, EvaluationError
from config import get_path_config, get_resource_limits

logger = get_logger(__name__)

def run_ablation_inference_pipeline(
    model_configs: List[Dict[str, Any]],
    data_config: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Executes the inference pipeline for ablated models.
    
    Args:
        model_configs: List of dicts containing ablation config (type, parameters).
                       Expected keys: 'config_id', 'type' ('freeze' or 'prune'), 'params'.
        data_config: Configuration for data loading (paths, class filters).
        output_dir: Directory to write intermediate logits and results.
        
    Returns:
        Summary dictionary of execution status and output paths.
    """
    if output_dir is None:
        path_config = get_path_config()
        output_dir = path_config.processed_dir
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "total_configs": len(model_configs),
        "successful_runs": 0,
        "failed_runs": 0,
        "outputs": []
    }
    
    # Ensure we have the base teacher/student model path
    # We assume the base model is available from T011/T012 artifacts
    # The inference runner expects a path to the base model to clone/modify
    base_model_path = os.getenv("ABLA_BASE_MODEL_PATH")
    if not base_model_path:
        # Fallback to standard processed dir if env var not set
        base_model_path = str(output_dir / "distilled_student_base.pt")
        
    if not os.path.exists(base_model_path):
        raise EvaluationError(f"Base model not found at {base_model_path}. "
                              "Run T011/T012 first.")

    logger.info(f"Starting ablation inference pipeline with {len(model_configs)} configs.")
    
    all_logits_data = []
    
    for config in model_configs:
        config_id = config.get("config_id", f"ablation_{summary['successful_runs']}")
        ablation_type = config.get("type")
        params = config.get("params", {})
        
        logger.info(f"Processing ablation config: {config_id} (type={ablation_type})")
        
        try:
            # 1. Load fresh base model
            logger.debug(f"Loading base model from {base_model_path}")
            base_model = load_student_model(base_model_path)
            
            # 2. Clone the model to ensure isolation (T036b requirement)
            ablated_model = clone_model(base_model)
            
            # 3. Apply structural modification
            if ablation_type == "freeze":
                logger.debug(f"Freezing attention heads: {params.get('heads', [])}")
                freeze_attention_heads(ablated_model, heads=params.get('heads', []))
            elif ablation_type == "prune":
                logger.debug(f"Pruning FFN layers: {params.get('layers', [])}")
                prune_ffn_layers(ablated_model, layers=params.get('layers', []))
            else:
                logger.warning(f"Unknown ablation type {ablation_type}, skipping modification.")
                
            # 4. Run inference on the subtle cue subset (T020 artifact)
            # We need to stream the data to get logits
            # The FilteredDataLoader handles streaming from the parquet file
            subtle_cue_path = str(output_dir / "subtle_cue_subset.parquet")
            
            if not os.path.exists(subtle_cue_path):
                raise EvaluationError(f"Subtle cue subset not found at {subtle_cue_path}. "
                                      "Run T020 first.")
                                      
            loader = FilteredDataLoader(
                dataset_path=subtle_cue_path,
                batch_size=4, # Small batch for CPU safety
                shuffle=False
            )
            
            logger.info(f"Running inference on {config_id} with batch size 4")
            
            # Run inference and collect logits
            # The runner returns InferenceResult objects
            inference_summary = run_inference_on_model(
                model=ablated_model,
                data_loader=loader,
                model_id=config_id,
                device="cpu" # Enforce CPU per constraints
            )
            
            # Collect logits for later metric calculation
            # We assume the runner or the model exposes logits in a serializable way
            # For this implementation, we assume the runner returns a summary that includes
            # the path to saved logits or we save them here if the runner doesn't.
            # Based on T039a description, we must output ablation_logits.parquet.
            # Let's assume the runner saves them or we extract them.
            # Since the runner signature is fixed, we rely on its side effects or summary.
            # If the runner doesn't save logits, we might need to adjust, but per API surface
            # run_inference_on_model returns InferenceRunSummary.
            # We will assume the logits are saved by the runner or we need to save them here.
            # To be safe and explicit per T039a: "Output intermediate logits to..."
            # We'll assume the inference runner saves logits to a standard location or
            # we save them here if we have access to them. 
            # Given the strict API surface, we assume the runner saves them to 
            # data/processed/{model_id}_logits.parquet or similar.
            # If not, we would need to modify the runner, but we are only extending ablation.py.
            # Let's assume the runner does this or we construct the path.
            
            logits_path = output_dir / f"{config_id}_logits.parquet"
            # If the runner didn't save it, we might need to handle it. 
            # However, T039a says "Run inference... Output intermediate logits".
            # If the runner doesn't do it, we can't easily extract raw logits from 
            # InferenceRunSummary without changing the runner. 
            # We will assume the runner saves them or we simulate the save if the summary has the data.
            # For this task, we assume the runner saves them to the expected path or 
            # we write a placeholder if the runner is incomplete (but we must not fail loudly if runner is fixed).
            # Actually, looking at T039a: "Output intermediate logits to data/processed/ablation_logits.parquet"
            # This implies a single file or a set of files. 
            # Let's assume the runner saves per-model logits. We will collect the paths.
            
            if hasattr(inference_summary, 'logits_path') and inference_summary.logits_path:
                all_logits_data.append({
                    "config_id": config_id,
                    "logits_path": inference_summary.logits_path
                })
            else:
                # Fallback: assume runner saved it with a standard naming convention
                expected_path = output_dir / f"{config_id}_logits.parquet"
                if expected_path.exists():
                    all_logits_data.append({
                        "config_id": config_id,
                        "logits_path": str(expected_path)
                    })
                else:
                    # If not found, we cannot proceed to T039b.
                    # But we must not fabricate. We log the error and continue to next config.
                    logger.error(f"Logits for {config_id} not found after inference run.")
                    summary["failed_runs"] += 1
                    continue
            
            summary["successful_runs"] += 1
            summary["outputs"].append({
                "config_id": config_id,
                "logits_path": all_logits_data[-1]["logits_path"]
            })
            
            # Cleanup memory
            del ablated_model
            gc.collect()
            
        except Exception as e:
            logger.error(f"Failed to process ablation config {config_id}: {e}", exc_info=True)
            summary["failed_runs"] += 1
            continue

    # Write a manifest of all logits for T039b to consume
    # T039b expects to consume 'ablation_logits.parquet'. 
    # If we have multiple files, we might need to merge them or point to the manifest.
    # The task says "Output intermediate logits to data/processed/ablation_logits.parquet".
    # This implies a single file. We will merge the results if possible or create a manifest.
    # Since we can't easily merge parquet without pandas/pyarrow logic that might be heavy,
    # and the task T039b says "Consume ablation_logits.parquet", we will assume the runner
    # produces a single file or we create a combined one.
    # For simplicity and robustness, we will write a JSON manifest listing all files.
    # But T039b specifically asks for a parquet file. 
    # Let's assume the runner produces one file per model and T039b handles multiple or 
    # we need to merge. 
    # Given the constraint "Output intermediate logits to data/processed/ablation_logits.parquet",
    # we will assume the runner's output is aggregated or we create a dummy file if empty.
    # However, to be correct, we should merge.
    # Since we cannot import heavy libs not in requirements (though pandas is there),
    # we will assume the runner saves a single file for the whole batch or we skip merging.
    # Let's assume the runner saves to a single file named 'ablation_logits.parquet' if we pass a flag.
    # But the runner API is fixed.
    # We will assume the runner saves individual files and T039b is updated to handle them,
    # OR we create a merged file here.
    # Let's try to create a merged file if we have pandas (which is in requirements).
    
    if all_logits_data and "pandas" in [pkg.key for pkg in __import__('pkg_resources').working_set]:
        try:
            import pandas as pd
            dfs = []
            for item in all_logits_data:
                df = pd.read_parquet(item["logits_path"])
                df["config_id"] = item["config_id"]
                dfs.append(df)
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                combined_path = output_dir / "ablation_logits.parquet"
                combined_df.to_parquet(combined_path, index=False)
                logger.info(f"Merged ablation logits to {combined_path}")
                summary["merged_logits_path"] = str(combined_path)
            else:
                logger.warning("No logits data to merge.")
        except ImportError:
            logger.warning("Pandas not available to merge logits files.")
    else:
        logger.warning("Skipping merge of logits files.")

    logger.info(f"Ablation inference pipeline completed. Success: {summary['successful_runs']}, Failed: {summary['failed_runs']}")
    return summary

def main():
    """
    Entry point for running the ablation inference pipeline.
    Reads ablation configurations and executes the pipeline.
    """
    path_config = get_path_config()
    ablation_config_path = path_config.processed_dir / "ablation_configs.json"
    
    if not ablation_config_path.exists():
        # Create a default config if not present for testing
        default_configs = [
            {"config_id": "freeze_heads_0", "type": "freeze", "params": {"heads": [0, 1]}},
            {"config_id": "prune_ffn_0", "type": "prune", "params": {"layers": [0]}}
        ]
        with open(ablation_config_path, "w") as f:
            json.dump(default_configs, f)
        logger.info(f"Created default ablation config at {ablation_config_path}")
    
    with open(ablation_config_path, "r") as f:
        model_configs = json.load(f)
        
    data_config = {
        "dataset_path": str(path_config.processed_dir / "subtle_cue_subset.parquet")
    }
    
    result = run_ablation_inference_pipeline(model_configs, data_config)
    
    # Save the result summary
    result_path = path_config.processed_dir / "ablation_inference_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Ablation inference result saved to {result_path}")
    return result

if __name__ == "__main__":
    main()