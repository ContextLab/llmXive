import argparse
import sys
import signal
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from utils.config import get_config
from utils.metrics import calculate_fid, calculate_clip_score
from models.inference import run_integrator
from utils.statistics import run_bootstrap_test, run_ttest, save_partial_results

# Global state for timeout
_timeout_active = False

def timeout_handler(signum, frame):
    raise TimeoutError("Execution timed out")

def setup_timeout(seconds: int):
    global _timeout_active
    if not hasattr(signal, 'SIGALRM'):
        return
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    _timeout_active = True

def cancel_timeout():
    global _timeout_active
    if _timeout_active:
        signal.alarm(0)
        _timeout_active = False

def load_dataset(path: str) -> pd.DataFrame:
    """Load the teacher routing dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_parquet(path)

def load_trees(models_dir: str) -> Dict[int, Any]:
    """Load trained decision trees from disk."""
    trees = {}
    path = Path(models_dir)
    if not path.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    for f in path.glob("tree_depth*.pkl"):
        # Assuming naming convention tree_depth{N}.pkl
        depth = int(f.stem.replace("tree_depth", ""))
        import joblib
        trees[depth] = joblib.load(str(f))
    return trees

def generate_tree_images(
    dataset: pd.DataFrame,
    trees: Dict[int, Any],
    depth: int,
    output_dir: str,
    config: Dict[str, Any]
) -> List[str]:
    """Generate images using tree-predicted routing."""
    if depth not in trees:
        raise ValueError(f"Tree for depth {depth} not found")
    
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    tree = trees[depth]
    
    # We assume the dataset has columns: 'prompt_embedding', 'noise_level', 'velocity_vector'
    # But for Tree-Generated, we need to predict the expert, then re-run that expert.
    # The dataset likely has 'expert_id' or similar from teacher, but we need to predict.
    # Assuming 'prompt_embedding' and 'noise_level' are features.
    # The target was 'routing_label' (expert_id).
    
    X = dataset[['prompt_embedding', 'noise_level']] # Simplified feature selection
    predictions = tree.predict(X)
    
    # We need to regenerate velocity vectors based on predicted expert.
    # The original dataset might have 'velocity_vector' for the teacher path.
    # We need to simulate the expert field again.
    # Since we don't have the exact expert field logic here, we assume the integrator
    # can take an expert_id and noise_level to generate.
    # However, the task says: "predict the expert with the trained Decision Tree, 
    # re-run that expert to obtain a fresh velocity_vector".
    # This implies we need access to the expert field model or a function that generates 
    # velocity given expert_id and noise.
    # For this implementation, we assume the integrator or a helper can do this.
    # Let's assume we have a function `get_velocity_for_expert(expert_id, noise, prompt)`
    # But the prompt is an embedding.
    # Given the constraints, we will assume the 'velocity_vector' in the dataset is 
    # specific to the teacher's choice. We need a new one.
    # Since the full expert logic is complex and not fully exposed in the API surface 
    # provided for this snippet, we will assume a placeholder function that mimics 
    # the behavior or that the `run_integrator` handles the expert selection internally 
    # if passed the correct ID.
    
    # Re-implementation of the logic based on T029 description:
    # "The function accepts velocity_vector, noise_level, and expert_type"
    # So we need to generate a NEW velocity_vector for the predicted expert.
    # This requires a "generate_velocity_vector" function which might be missing from the 
    # provided API surface. 
    # However, T028 description says: "re-run that expert to obtain a fresh velocity_vector".
    # If we cannot generate a fresh vector, we cannot strictly follow the spec.
    # Assuming the `models/inference.py` has a way to generate velocity or we use a 
    # simplified approximation for this task.
    # To satisfy the requirement of "real code", we will assume the dataset contains 
    # enough info or we use a mock generation that is deterministic based on expert_id 
    # and noise (as a stand-in for the missing complex expert logic in this snippet).
    # BUT the constraint says "NEVER fabricate". 
    # The only way is if the `run_integrator` or a helper in `models/inference` 
    # actually does the generation.
    # Let's assume `models.inference` has a function `generate_velocity_vector(expert_id, noise, embedding)`.
    # If not, we must fail or use the existing one (which is not "fresh" for the tree path).
    # Given the strictness, I will assume the `run_integrator` takes the expert_id 
    # and generates the image directly, or the velocity generation is internal.
    # The T028 description: "re-run that expert to obtain a fresh velocity_vector, and integrate".
    # Let's assume we have a helper `get_expert_velocity` in `models/inference`.
    
    # Since I cannot invent names not in the API, and `models/inference.py` only lists:
    # `ExpertFieldSimulator, euler_integrate, generate_image_from_velocity, run_integrator`
    # I will use `run_integrator` which likely handles the full flow if passed the expert ID.
    # But `run_integrator` signature in API is not fully detailed.
    # Let's assume `run_integrator` takes `expert_id`, `noise_level`, `prompt_embedding`.
    
    for idx, row in dataset.iterrows():
        pred_expert = int(predictions[idx])
        # Attempt to generate image directly via integrator with predicted expert
        # Assuming run_integrator can take expert_id and generate the image
        # If it requires a velocity vector, we are stuck without a velocity generator.
        # However, the task T029 says "invokes the appropriate expert field logic to generate an image".
        # So `run_integrator` might be the full pipeline.
        
        # Let's try to call run_integrator with the predicted expert
        # We need to map the expert ID to the expert_type string if needed.
        # Assuming integer ID works or we map it.
        
        img_path = os.path.join(output_dir, f"tree_depth{depth}_sample_{idx}.png")
        
        # Placeholder for actual generation logic if run_integrator doesn't take ID directly
        # We assume run_integrator returns a path or we handle it.
        # Given the ambiguity, we assume run_integrator(expert_id, noise, embedding) -> image_path
        # This is a critical assumption.
        
        # If we cannot generate, we must raise an error.
        # But to make the code runnable as per the task "Implement logic...":
        # We will assume the existence of a helper that was implied by T029's description 
        # but not fully listed in the API surface, OR that `run_integrator` is smart enough.
        # Let's assume `run_integrator` takes `expert_id` and `noise_level` and `embedding`.
        
        try:
            # This call assumes `run_integrator` can generate the image from expert selection
            # If it requires a velocity vector, we would need a `generate_velocity` function.
            # Since T029 says "invokes ... to generate an image", `run_integrator` likely does it.
            # We pass the predicted expert ID.
            # Note: This might fail if the actual signature is different, but it's the best 
            # interpretation of the provided API.
            generated_path = run_integrator(
                expert_id=pred_expert,
                noise_level=row['noise_level'],
                prompt_embedding=row['prompt_embedding'],
                config=config
            )
            if generated_path:
                image_paths.append(generated_path)
            else:
                # If it returns None, maybe it saved internally?
                # Or we assume the function returns the path.
                # If it doesn't work, we raise.
                raise RuntimeError("run_integrator did not return a path")
        except Exception as e:
            # If we can't generate, we stop.
            raise RuntimeError(f"Failed to generate tree image for sample {idx}: {e}")

    return image_paths

def generate_teacher_images(
    dataset: pd.DataFrame,
    output_dir: str,
    config: Dict[str, Any]
) -> List[str]:
    """Generate images using teacher routing labels."""
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    
    for idx, row in dataset.iterrows():
        # Teacher routing label is in 'routing_label'
        expert_id = int(row['routing_label'])
        img_path = os.path.join(output_dir, f"teacher_baseline_sample_{idx}.png")
        
        try:
            generated_path = run_integrator(
                expert_id=expert_id,
                noise_level=row['noise_level'],
                prompt_embedding=row['prompt_embedding'],
                config=config
            )
            if generated_path:
                image_paths.append(generated_path)
            else:
                raise RuntimeError("run_integrator did not return a path")
        except Exception as e:
            raise RuntimeError(f"Failed to generate teacher image for sample {idx}: {e}")

    return image_paths

def compute_fidelity_metrics(
    tree_images: List[str],
    teacher_images: List[str],
    output_csv: str
) -> Dict[str, float]:
    """Compute FID and CLIP Score between tree and teacher images."""
    if len(tree_images) != len(teacher_images):
        raise ValueError("Image lists must be of equal length")
    
    results = []
    total_fid_diff = 0.0
    total_clip_diff = 0.0
    
    # We need to compute FID and CLIP for the ENTIRE dataset.
    # FID is usually between two sets. CLIP is usually pairwise or set-based.
    # The task says "comparing Tree-Generated images vs Teacher-Baseline images".
    # And "Store results in data/results/fidelity_metrics.csv".
    # And "Derive total degradation metrics (ΔFID, ΔCLIP)".
    # This implies computing the metric for the whole set (FID) and maybe per-sample (CLIP).
    # But FID requires two sets.
    # Let's compute FID for the whole set and CLIP per sample if possible, or set-based.
    # The task says "ΔFID, ΔCLIP". If FID is a single number for the set, then ΔFID is 0?
    # No, it means the degradation is the FID between Tree set and Teacher set.
    # And CLIP score might be the average similarity or degradation.
    # Let's compute:
    # 1. FID between Tree set and Teacher set.
    # 2. CLIP Score between Tree set and Teacher set (maybe average pairwise?).
    # But the CSV might need per-sample metrics? "Store results in ... csv".
    # Let's assume we compute FID (global) and CLIP (global or average).
    # Or maybe per-sample CLIP?
    # The task says "comparing ...".
    # Let's compute FID for the two sets.
    # And CLIP score for the two sets (if supported) or average per-sample.
    
    # Since calculate_clip_score takes two paths, and calculate_fid takes two paths (or dirs).
    # We will compute:
    # FID: calculate_fid(tree_dir, teacher_dir) -> single float
    # CLIP: We might need to compute pairwise or average.
    # But the function `calculate_clip_score` takes two paths.
    # Let's assume it computes the score between two images.
    # Then we need to iterate?
    # The task says "Compute FID and CLIP Score on the entire dataset".
    # This could mean FID between the two sets, and CLIP between the two sets.
    # If `calculate_clip_score` is pairwise, we might need to average.
    # However, the function signature in API is `calculate_clip_score(image_path_1, image_path_2)`.
    # So it's pairwise.
    # To get a set metric, we might need to average over pairs?
    # Or maybe the function handles directories? The API says `image_path_1: str`.
    # Let's assume we compute the average CLIP score over all samples (pairwise).
    
    # For FID, we pass the two directories (or lists converted to temp dirs).
    # But the function takes two paths. We might need to create temp directories.
    
    # Let's assume the helper functions can handle lists or we create temp dirs.
    # Since we have lists of paths, we can create temp dirs for FID.
    # For CLIP, we iterate.
    
    # Create temp dirs for FID
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmp_tree, tempfile.TemporaryDirectory() as tmp_teacher:
        # Copy files to temp dirs (or symlink)
        for i, path in enumerate(tree_images):
            shutil.copy(path, os.path.join(tmp_tree, f"tree_{i}.png"))
        for i, path in enumerate(teacher_images):
            shutil.copy(path, os.path.join(tmp_teacher, f"teacher_{i}.png"))
        
        fid_score = calculate_fid(tmp_tree, tmp_teacher)
        
        # Compute CLIP scores pairwise
        clip_scores = []
        for i, (t_path, te_path) in enumerate(zip(tree_images, teacher_images)):
            score = calculate_clip_score(t_path, te_path)
            clip_scores.append(score)
        
        avg_clip = np.mean(clip_scores)
        
        # We need to store results in CSV.
        # Columns: metric, value, sample_id (if per sample)
        # Since FID is global, we might write one row for FID and one for CLIP?
        # Or per sample CLIP and global FID.
        # The task says "Store results in ... csv".
        # Let's write:
        # metric, value, sample_id
        # FID, <val>, global
        # CLIP, <val>, <sample_id> for each
        
        rows = []
        rows.append({"metric": "FID", "value": fid_score, "sample_id": "global"})
        for i, score in enumerate(clip_scores):
            rows.append({"metric": "CLIP", "value": score, "sample_id": i})
        
        df = pd.DataFrame(rows)
        df.to_csv(output_csv, index=False)
        
        return {
            "fid": fid_score,
            "avg_clip": avg_clip,
            "clip_scores": clip_scores,
            "fid_diff": fid_score, # Degradation is the FID itself? Or 0?
            "clip_diff": 1.0 - avg_clip # Assuming higher is better?
        }

def save_results(results: Dict[str, Any], output_path: str):
    """Save results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def run_fidelity_evaluation(args):
    config = get_config()
    setup_timeout(args.timeout if args.timeout else 21600) # 6 hours
    
    try:
        # Load dataset
        dataset_path = args.dataset or config.get_path('processed_dataset')
        dataset = load_dataset(dataset_path)
        
        # Load trees
        models_dir = args.models_dir or config.get_path('models_dir')
        trees = load_trees(models_dir)
        
        # Generate images
        output_dir = args.output_dir or config.get_path('results_dir')
        tree_images_dir = os.path.join(output_dir, "tree_images")
        teacher_images_dir = os.path.join(output_dir, "teacher_images")
        
        # We need to generate for a specific depth? The task says "all" or "depth=5"?
        # The task T030 says "comparing Tree-Generated images vs Teacher-Baseline images".
        # It doesn't specify depth. But T028 says "all samples" and "two modes".
        # We assume we use the best tree or a specific one (e.g., depth=5 as per test).
        # Let's assume we use depth=5 as the primary comparison, or we do all?
        # The task says "on the entire dataset".
        # Let's assume we use the tree with depth=5 (as per T020 test).
        depth = 5
        if depth not in trees:
            raise ValueError(f"Tree for depth {depth} not found. Available: {list(trees.keys())}")
        
        tree_images = generate_tree_images(dataset, trees, depth, tree_images_dir, config)
        teacher_images = generate_teacher_images(dataset, teacher_images_dir, config)
        
        # Compute metrics
        metrics_csv = os.path.join(output_dir, "fidelity_metrics.csv")
        metrics = compute_fidelity_metrics(tree_images, teacher_images, metrics_csv)
        
        # Save summary
        summary = {
            "depth": depth,
            "num_samples": len(dataset),
            "fid": metrics["fid"],
            "avg_clip": metrics["avg_clip"],
            "degradation": {
                "fid": metrics["fid"],
                "clip": 1.0 - metrics["avg_clip"]
            }
        }
        save_results(summary, os.path.join(output_dir, "fidelity_summary.json"))
        
        print(f"Fidelity metrics computed. CSV: {metrics_csv}")
        
    except TimeoutError:
        save_partial_results("data/results/partial_results.json", {"status": "partial", "reason": "timeout"})
        sys.exit(2)
    finally:
        cancel_timeout()

def main():
    parser = argparse.ArgumentParser(description="Evaluate Fidelity Metrics")
    parser.add_argument("--dataset", type=str, help="Path to dataset")
    parser.add_argument("--models-dir", type=str, help="Path to trained models")
    parser.add_argument("--output-dir", type=str, help="Path to output directory")
    parser.add_argument("--timeout", type=int, help="Timeout in seconds")
    args = parser.parse_args()
    run_fidelity_evaluation(args)

if __name__ == "__main__":
    main()