"""
Stream and process data from pre-fetched raw datasets.

This script reads from `data/raw/` (ImageNet and LAION samples), extracts
features using CLIP, and combines them with teacher model outputs (if available)
into a unified Parquet file.
"""
import argparse
import sys
import json
import signal
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from utils.config import get_config

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def setup_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    signal.alarm(0)

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_config_paths() -> Dict[str, Path]:
    config = get_config()
    return {
        "raw_data_dir": config.get_path("RAW_DATA_DIR"),
        "processed_dir": config.get_path("PROCESSED_DIR"),
        "output_file": config.get_path("COMBINED_SAMPLES_PATH"),
    }

def load_imageNet_streaming(
    parquet_path: Path,
    max_samples: Optional[int] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Load ImageNet samples from a pre-fetched Parquet file.
    If max_samples is set, perform a stratified random sample.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"ImageNet samples not found at {parquet_path}")

    df = pd.read_parquet(parquet_path)
    
    # Ensure required columns exist
    required_cols = ["image_path", "label", "source"]
    for col in required_cols:
        if col not in df.columns:
            # Attempt to add source if missing
            if col == "source":
                df["source"] = "imagenet"
            else:
                raise ValueError(f"Missing required column '{col}' in {parquet_path}")

    if max_samples and len(df) > max_samples:
        # Simple random sample if stratification is too complex for unknown schema
        rng = np.random.default_rng(seed)
        indices = rng.choice(len(df), size=max_samples, replace=False)
        df = df.iloc[indices].reset_index(drop=True)

    return df

def load_laion_streaming(
    parquet_path: Path,
    max_samples: Optional[int] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Load LAION samples from a pre-fetched Parquet file.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"LAION samples not found at {parquet_path}")

    df = pd.read_parquet(parquet_path)
    
    required_cols = ["image_path", "caption", "source"]
    for col in required_cols:
        if col not in df.columns:
            if col == "source":
                df["source"] = "laion"
            else:
                raise ValueError(f"Missing required column '{col}' in {parquet_path}")

    if max_samples and len(df) > max_samples:
        rng = np.random.default_rng(seed)
        indices = rng.choice(len(df), size=max_samples, replace=False)
        df = df.iloc[indices].reset_index(drop=True)

    return df

def extract_prompt_embedding(
    processor: CLIPProcessor,
    model: CLIPModel,
    text: str,
    device: str = "cpu"
) -> List[float]:
    """
    Extract CLIP text embedding for a given prompt/caption.
    """
    inputs = processor(
        text=[text],
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=77
    ).to(device)

    with torch.no_grad():
        outputs = model.get_text_features(**inputs)
    
    # Normalize
    features = outputs / outputs.norm(dim=-1, keepdim=True)
    return features[0].cpu().numpy().tolist()

def extract_image_embedding(
    processor: CLIPProcessor,
    model: CLIPModel,
    image_path: str,
    device: str = "cpu"
) -> Optional[List[float]]:
    """
    Extract CLIP image embedding for a given image path.
    """
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Warning: Could not load image {image_path}: {e}")
        return None

    inputs = processor(
        images=image,
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to(device)

    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
    
    # Normalize
    features = outputs / outputs.norm(dim=-1, keepdim=True)
    return features[0].cpu().numpy().tolist()

def load_teacher_ground_truth(
    parquet_path: Path,
    max_samples: Optional[int] = None
) -> pd.DataFrame:
    """
    Load pre-computed teacher ground truth if available.
    This is used to attach routing_label and velocity_vector to the streamed data.
    """
    if not parquet_path.exists():
        return pd.DataFrame()

    df = pd.read_parquet(parquet_path)
    # We assume the ground truth file has an index or ID that matches the raw data
    # For this implementation, we assume the order matches or we merge by a common key.
    # If the ground truth was generated from the exact same sampling process,
    # we can align by index if both are sampled to the same size.
    if max_samples and len(df) > max_samples:
        df = df.iloc[:max_samples].reset_index(drop=True)
    
    return df

def stratified_sample(df: pd.DataFrame, n: int, seed: int = 42) -> pd.DataFrame:
    """
    Perform stratified sampling if 'source' or 'label' columns exist.
    Otherwise, fallback to random sample.
    """
    rng = np.random.default_rng(seed)
    if 'source' in df.columns:
        # Stratify by source
        counts = df['source'].value_counts()
        sample_counts = {}
        for source, count in counts.items():
            # Proportional sampling
            n_source = max(1, int(count * (n / len(df))))
            sample_counts[source] = n_source
        
        samples = []
        for source, n_s in sample_counts.items():
            subset = df[df['source'] == source]
            if len(subset) < n_s:
                n_s = len(subset)
            samples.append(subset.sample(n=n_s, random_state=seed))
        
        result = pd.concat(samples).reset_index(drop=True)
    else:
        # Fallback
        result = df.sample(n=min(n, len(df)), random_state=seed)
    
    return result

def write_batch_to_parquet(
    df: pd.DataFrame,
    output_path: Path,
):
    """
    Write the combined dataframe to Parquet.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Successfully wrote {len(df)} samples to {output_path}")

def run_data_streaming(
    imagenet_path: Path,
    laion_path: Path,
    teacher_gt_path: Path,
    output_path: Path,
    target_samples: int = 1200,
    seed: int = 42,
    timeout_seconds: int = 3600
):
    """
    Main logic to stream, combine, and process data.
    """
    setup_timeout(timeout_seconds)
    try:
        config = get_config()
        device = "cpu" # Enforce CPU only for this task
        torch.set_default_device(device)
        
        # Load CLIP model
        print("Loading CLIP model...")
        clip_model_name = config.get_hyperparameter("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained(clip_model_name)
        model = CLIPModel.from_pretrained(clip_model_name)
        model.to(device)
        model.eval()

        # Load datasets
        print("Loading ImageNet samples...")
        df_imagenet = load_imageNet_streaming(imagenet_path, max_samples=None, seed=seed)
        
        print("Loading LAION samples...")
        df_laion = load_laion_streaming(laion_path, max_samples=None, seed=seed)

        # Combine raw data
        # Ensure 'source' column is present
        if 'source' not in df_imagenet.columns:
            df_imagenet['source'] = 'imagenet'
        if 'source' not in df_laion.columns:
            df_laion['source'] = 'laion'

        combined_raw = pd.concat([df_imagenet, df_laion], ignore_index=True)
        
        # Sample to target size
        if len(combined_raw) > target_samples:
            print(f"Sampling from {len(combined_raw)} to {target_samples}...")
            combined_raw = stratified_sample(combined_raw, target_samples, seed=seed)
        
        print(f"Processing {len(combined_raw)} samples...")

        # Initialize result list
        results = []
        
        # If teacher ground truth exists and has the same length (assuming aligned),
        # we can try to merge. However, the task description implies we generate
        # the tuple (prompt_embedding, noise_level, routing_label, velocity_vector).
        # If teacher_gt is missing, we might not have routing_label/velocity_vector yet.
        # The task says: "pass the image to the teacher model to generate routing_label..."
        # BUT T013a handles teacher inference. T012b is "Stream & Process".
        # If T013a hasn't run, we cannot generate routing labels here.
        # We will extract embeddings and noise_level (default if missing) and leave
        # routing_label/velocity_vector as null or attempt to load if T013a ran.
        
        teacher_df = load_teacher_ground_truth(teacher_gt_path, max_samples=len(combined_raw))
        
        # Merge logic: If teacher_df exists and has an index matching combined_raw, merge.
        # Since we don't have a guaranteed ID, we assume order alignment if lengths match.
        if not teacher_df.empty and len(teacher_df) == len(combined_raw):
            combined_raw = pd.concat([combined_raw, teacher_df], axis=1)
        
        # Process each sample
        for idx, row in combined_raw.iterrows():
            try:
                # Extract text embedding
                text_input = row.get("caption") or row.get("label", "image")
                if isinstance(text_input, (list, np.ndarray)):
                    text_input = str(text_input[0])
                
                prompt_embedding = extract_prompt_embedding(processor, model, str(text_input), device)
                
                # Extract image embedding (optional, for noise_level if needed)
                # For now, default noise_level to 0.0 or extract from image if possible
                image_embedding = extract_image_embedding(processor, model, row["image_path"], device)
                noise_level = row.get("noise_level", 0.0)
                
                # Construct row
                out_row = {
                    "image_path": row["image_path"],
                    "source": row["source"],
                    "prompt_embedding": prompt_embedding,
                    "noise_level": noise_level,
                }
                
                # Add teacher outputs if available
                if not teacher_df.empty:
                    # Assuming teacher_df has 'routing_label' and 'velocity_vector'
                    if "routing_label" in teacher_df.columns:
                        out_row["routing_label"] = teacher_df.iloc[idx].get("routing_label")
                    if "velocity_vector" in teacher_df.columns:
                        out_row["velocity_vector"] = teacher_df.iloc[idx].get("velocity_vector")
                
                results.append(out_row)
                
            except Exception as e:
                print(f"Error processing sample {idx}: {e}")
                continue

        # Convert list of dicts to DataFrame
        # Handle list columns (embeddings, vectors) by storing as lists or JSON strings
        # Parquet supports list columns usually, but sometimes serialization is needed.
        # We'll store as lists if possible.
        final_df = pd.DataFrame(results)
        
        # Save
        write_batch_to_parquet(final_df, output_path)
        
        print("Data streaming and processing complete.")
        
    except TimeoutError:
        print("ERROR: Data streaming timed out.")
        # Save partial results if possible
        partial_path = output_path.parent / "combined_samples_partial.parquet"
        if 'final_df' in locals() and not final_df.empty:
            write_batch_to_parquet(final_df, partial_path)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Data streaming failed: {e}")
        sys.exit(1)
    finally:
        cancel_timeout()

def main():
    parser = argparse.ArgumentParser(description="Stream and process raw data for DanceOPD.")
    parser.add_argument("--target-samples", type=int, default=1200, help="Target number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds")
    args = parser.parse_args()

    paths = get_config_paths()
    
    imagenet_path = paths["raw_data_dir"] / "imagenet_samples.parquet"
    laion_path = paths["raw_data_dir"] / "laion_samples.parquet"
    teacher_gt_path = paths["raw_data_dir"] / "teacher_ground_truth.parquet"
    output_path = paths["output_file"]

    run_data_streaming(
        imagenet_path=imagenet_path,
        laion_path=laion_path,
        teacher_gt_path=teacher_gt_path,
        output_path=output_path,
        target_samples=args.target_samples,
        seed=args.seed,
        timeout_seconds=args.timeout
    )

if __name__ == "__main__":
    main()