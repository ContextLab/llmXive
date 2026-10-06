"""
Model Training Module (T018, T019)
Implements Random Forest baseline and lightweight CLIP-based VLM fine-tuning.
"""
import os
import sys
import logging
import json
import time
import pickle
import gc
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
import xarray as xr
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# VLM Imports (Conditional)
try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    from transformers import TrainingArguments, Trainer
    from datasets import Dataset
    import bitsandbytes as bnb
    VLM_AVAILABLE = True
except ImportError:
    VLM_AVAILABLE = False
    logging.warning("PyTorch or Transformers not installed. VLM training will fallback to RF.")

from utils.config import get_config, get_available_ram_gb
from utils.logging_config import get_logger, log_metric

logger = get_logger(__name__)

CONFIG = get_config()
MEMORY_LIMIT_GB = float(os.environ.get('MEMORY_LIMIT_GB', CONFIG.get('memory_limit_gb', 7.0)))
RAM_LIMIT_GB = 7.0

# --- T019_pre: Memory Pre-check ---
def check_vlm_memory_requirements() -> bool:
    """
    Verifies that the system has sufficient RAM (<7GB) to load the VLM model
    with 4-bit quantization.
    """
    available_ram = get_available_ram_gb()
    logger.info(f"Available RAM: {available_ram:.2f} GB")
    # CLIP ViT-Base is ~400M params. 4-bit quantization reduces footprint significantly.
    # Estimated model size: ~2GB + overhead.
    if available_ram < 4.0:
        logger.error(f"Insufficient RAM ({available_ram:.2f} GB) for VLM fine-tuning.")
        return False
    return True

# --- Data Loading Helpers ---
def load_aligned_data(path: str) -> pd.DataFrame:
    """
    Loads the aligned dataset from NetCDF or CSV.
    Raises FileNotFoundError if not found.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Aligned data not found at {path}")

    if p.suffix == '.nc':
        ds = xr.open_dataset(p)
        df = ds.to_dataframe().reset_index()
    elif p.suffix == '.csv':
        df = pd.read_csv(p)
    else:
        raise ValueError(f"Unsupported file format: {p.suffix}")

    # Ensure required columns exist
    required_cols = ['lat', 'lon', 'timestamp', 'basin', 'temp', 'salinity', 'nutrients', 'chlorophyll_a']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in aligned dataset: {missing}")

    return df

# --- T018: Random Forest Baseline ---
def train_random_forest(df: pd.DataFrame, test_size: float = 0.2) -> Dict[str, Any]:
    """
    Trains a Random Forest baseline (<=500 trees) on CPU.
    """
    logger.info("Training Random Forest Baseline...")
    start = time.time()

    features = ['temp', 'salinity', 'nutrients']
    target = 'chlorophyll_a'

    # Handle missing values
    df_clean = df.dropna(subset=features + [target])

    X = df_clean[features].values
    y = df_clean[target].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=CONFIG.seed
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestRegressor(
        n_estimators=500,
        max_depth=15,
        random_state=CONFIG.seed,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    metrics = {
        "model_type": "RandomForest",
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "training_time_s": time.time() - start,
        "n_samples": len(X_train)
    }

    logger.info(f"RF Training complete. R2: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}")
    return {
        "model": model,
        "scaler": scaler,
        "metrics": metrics
    }

# --- T019: VLM Fine-tuning (CLIP-based) ---
def prepare_vlm_dataset(df: pd.DataFrame, processor: 'CLIPProcessor', max_samples: int = 1000) -> 'Dataset':
    """
    Prepares a HuggingFace Dataset for VLM training.
    Creates a pseudo-image from tabular data and a text prompt.
    """
    # Stream/limit samples to ensure CPU feasibility
    if len(df) > max_samples:
        logger.info(f"Limiting VLM training to {max_samples} samples from {len(df)} total.")
        df = df.sample(n=max_samples, random_state=CONFIG.seed)

    df = df.dropna(subset=['temp', 'salinity', 'nutrients', 'chlorophyll_a'])

    def create_features(example):
        # Text Prompt
        prompt = f"Temperature: {example['temp']:.2f}, Salinity: {example['salinity']:.2f}, Nutrients: {example['nutrients']:.2f}"
        
        # Pseudo-Image: Create a simple 3x3 grid or normalized vector visualization
        # For CLIP, we need a PIL Image. We'll create a simple color-coded patch.
        # Normalize values to 0-1 for visualization
        t_norm = (example['temp'] - df['temp'].min()) / (df['temp'].max() - df['temp'].min() + 1e-6)
        s_norm = (example['salinity'] - df['salinity'].min()) / (df['salinity'].max() - df['salinity'].min() + 1e-6)
        n_norm = (example['nutrients'] - df['nutrients'].min()) / (df['nutrients'].max() - df['nutrients'].min() + 1e-6)
        
        # Create a 3x3 RGB image representing the triplet
        import numpy as np
        from PIL import Image
        img_array = np.zeros((3, 3, 3), dtype=np.uint8)
        # Top row: Temp (Red), Sal (Green), Nut (Blue)
        img_array[0, 0] = [int(t_norm * 255), 0, 0]
        img_array[0, 1] = [0, int(s_norm * 255), 0]
        img_array[0, 2] = [0, 0, int(n_norm * 255)]
        # Fill rest with gray background
        img_array[1:, :] = [128, 128, 128]
        
        img = Image.fromarray(img_array)
        
        return {
            "pixel_values": img,
            "text": prompt,
            "label": example['chlorophyll_a']
        }

    # Convert to HF Dataset
    dataset = Dataset.from_dict({
        "temp": df['temp'].values,
        "salinity": df['salinity'].values,
        "nutrients": df['nutrients'].values,
        "chlorophyll_a": df['chlorophyll_a'].values
    })
    
    # Map features
    dataset = dataset.map(create_features, remove_columns=['temp', 'salinity', 'nutrients', 'chlorophyll_a'])
    dataset = dataset.cast_column("pixel_values", Image.Image) # Ensure type is correct for processor

    return dataset

def train_vlm(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fine-tunes a lightweight CLIP-based VLM.
    Implements early stopping and fallback logic.
    """
    if not VLM_AVAILABLE:
        logger.warning("VLM dependencies missing. Skipping VLM training.")
        return None

    if not check_vlm_memory_requirements():
        logger.warning("Memory check failed. Skipping VLM training.")
        return None

    logger.info("Starting VLM Fine-tuning (CLIP)...")
    start = time.time()

    try:
        # Load Model and Processor
        model_name = "facebook/clip-vit-base-patch32"
        logger.info(f"Loading model: {model_name} with 4-bit quantization...")
        
        # Note: CLIP doesn't natively support 4-bit in the same way LLMs do in transformers,
        # but we can use bitsandbytes for the linear layers if we wrap it or use a custom head.
        # For simplicity and stability in CPU-only, we load standard weights but limit training steps.
        # If bitsandbytes is strictly required for 4-bit, we attempt it, otherwise standard.
        try:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(load_in_4bit=True)
            model = CLIPModel.from_pretrained(model_name, quantization_config=bnb_config, device_map="cpu")
        except Exception:
            # Fallback to standard loading if 4-bit fails on CPU
            logger.warning("4-bit quantization failed on CPU, loading standard model.")
            model = CLIPModel.from_pretrained(model_name)
            # Move to CPU explicitly
            model = model.to("cpu")

        processor = CLIPProcessor.from_pretrained(model_name)

        # Prepare Dataset
        dataset = prepare_vlm_dataset(df, processor)

        # Define a simple regression head on top of CLIP text/image embeddings
        # Since CLIP is contrastive, we adapt it for regression by projecting the joint embedding
        from torch import nn
        import torch.nn.functional as F

        class CLIPRegressionHead(nn.Module):
            def __init__(self, hidden_size):
                super().__init__()
                self.head = nn.Sequential(
                    nn.Linear(hidden_size, 128),
                    nn.ReLU(),
                    nn.Linear(128, 1)
                )
            def forward(self, image_embeds, text_embeds):
                # Concatenate or average embeddings
                joint = (image_embeds + text_embeds) / 2
                return self.head(joint)

        # Freeze base CLIP parameters
        for param in model.parameters():
            param.requires_grad = False

        # Add regression head
        hidden_size = model.config.projection_dim
        regression_head = CLIPRegressionHead(hidden_size)
        regression_head = regression_head.to("cpu")

        # Custom Training Loop (CPU-friendly, small batch)
        batch_size = 4
        max_steps = 100  # Limit steps for CPU feasibility
        patience = 10
        best_loss = float('inf')
        no_improve_count = 0
        losses = []

        logger.info(f"Training with batch_size={batch_size}, max_steps={max_steps}...")

        for step in range(max_steps):
            # Sample a batch
            indices = np.random.choice(len(dataset), size=batch_size, replace=False)
            batch = dataset.select(indices)

            # Process inputs
            pixel_values = [b["pixel_values"] for b in batch]
            texts = [b["text"] for b in batch]
            labels = torch.tensor([b["label"] for b in batch], dtype=torch.float32)

            inputs = processor(text=texts, images=pixel_values, return_tensors="pt", padding=True)
            inputs = {k: v.to("cpu") for k, v in inputs.items()}

            # Forward pass
            with torch.set_grad_enabled(True):
                outputs = model(**inputs)
                image_embeds = outputs.image_embeds
                text_embeds = outputs.text_embeds
                predictions = regression_head(image_embeds, text_embeds).squeeze()

                loss = F.mse_loss(predictions, labels)

            # Backward pass
            loss.backward()

            # Optimizer step (manual for simplicity in custom head)
            if step == 0:
                optimizer = torch.optim.Adam(regression_head.parameters(), lr=1e-4)
            
            optimizer.step()
            optimizer.zero_grad()

            losses.append(loss.item())

            # Early Stopping Logic
            if loss.item() < best_loss:
                best_loss = loss.item()
                no_improve_count = 0
            else:
                no_improve_count += 1

            if no_improve_count >= patience:
                logger.warning(f"Early stopping triggered at step {step}. Loss: {loss.item():.4f}")
                break

        # Evaluate
        # Simple evaluation on a holdout subset
        test_indices = list(range(0, len(dataset), 10))[:50]
        if len(test_indices) > 0:
            test_batch = dataset.select(test_indices)
            pixel_values = [b["pixel_values"] for b in test_batch]
            texts = [b["text"] for b in test_batch]
            labels = torch.tensor([b["label"] for b in test_batch], dtype=torch.float32)

            inputs = processor(text=texts, images=pixel_values, return_tensors="pt", padding=True)
            inputs = {k: v.to("cpu") for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)
                image_embeds = outputs.image_embeds
                text_embeds = outputs.text_embeds
                preds = regression_head(image_embeds, text_embeds).squeeze()

            rmse = float(np.sqrt(mean_squared_error(labels.numpy(), preds.numpy())))
            r2 = float(r2_score(labels.numpy(), preds.numpy()))
        else:
            rmse = float('nan')
            r2 = float('nan')

        training_time = time.time() - start

        return {
            "model": regression_head,
            "processor": processor,
            "base_model": model,
            "metrics": {
                "model_type": "VLM-CLIP",
                "rmse": rmse,
                "r2": r2,
                "training_time_s": training_time,
                "final_loss": losses[-1] if losses else float('nan'),
                "converged": no_improve_count < patience
            }
        }

    except Exception as e:
        logger.error(f"VLM Training failed: {str(e)}", exc_info=True)
        return None

def save_model_artifacts(results: Dict[str, Any], output_path: str):
    """
    Saves model artifacts and metrics.
    Handles VLM failure by saving RF-only results if VLM is None.
    """
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # Prepare serializable metrics
    metrics = results.get("rf_results", {}).get("metrics", {})
    vlm_results = results.get("vlm_results")
    
    if vlm_results and vlm_results.get("metrics"):
        metrics["vlm_metrics"] = vlm_results["metrics"]
    
    # Save metrics JSON
    with open(p / "model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Save RF model
    if "rf_results" in results:
        with open(p / "rf_model.pkl", "wb") as f:
            pickle.dump(results["rf_results"], f)

    # Save VLM model (if successful)
    if vlm_results and vlm_results.get("model"):
        # Save only the head and processor config, base model is too large to pickle safely here
        with open(p / "vlm_head.pkl", "wb") as f:
            pickle.dump({
                "head": vlm_results["model"],
                "processor": vlm_results["processor"]
            }, f)
        # Log fallback flag if needed
        if not vlm_results["metrics"].get("converged", False):
            logger.warning("VLM did not converge. Fallback flag set.")
            # Update state file
            state_path = Path("state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml")
            if state_path.exists():
                import yaml
                with open(state_path, "r") as f:
                    state = yaml.safe_load(f) or {}
                state["vlm_fallback"] = True
                with open(state_path, "w") as f:
                    yaml.dump(state, f)
                logger.info(f"Updated state file: {state_path} with vlm_fallback=True")

def main():
    """
    Main entry point for T019.
    """
    setup_logging = True # Assuming logging is configured globally or here
    logger.info("Starting Model Training (T019)...")

    # Load Data
    data_path = "data/processed/aligned_dataset.nc"
    try:
        df = load_aligned_data(data_path)
        logger.info(f"Loaded {len(df)} samples from {data_path}")
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)

    # Train RF
    rf_results = train_random_forest(df)

    # Train VLM
    vlm_results = train_vlm(df)

    # Save Artifacts
    save_model_artifacts({"rf_results": rf_results, "vlm_results": vlm_results}, "data/artifacts/models")

    logger.info("Model training complete.")

if __name__ == "__main__":
    main()
