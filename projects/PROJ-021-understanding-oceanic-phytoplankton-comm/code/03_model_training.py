import os
import sys
import logging
import json
import time
import pickle
import gc
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torch import nn
from transformers import CLIPModel, CLIPProcessor, Trainer, TrainingArguments
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split

# Project-relative imports based on API surface
from utils.config import get_config, get_available_ram_gb
from utils.logging_config import get_logger, log_metric, log_pipeline_event

# Setup logging
logger = get_logger(__name__)
config = get_config()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-021-understanding-oceanic-phytoplankton-comm.yaml"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "aligned_dataset.nc"
ARTIFACT_DIR = PROJECT_ROOT / "data" / "artifacts"
LOG_DIR = PROJECT_ROOT / "data" / "logs"

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

def check_vlm_memory_requirements() -> bool:
    """
    Check if VLM training is feasible within RAM limits.
    Returns True if feasible, False otherwise.
    """
    try:
        model = CLIPModel.from_pretrained("facebook/clip-vit-base-patch32")
        params = sum(p.numel() for p in model.parameters())
        # Rough estimate: 4 bytes per param for fp32, plus overhead
        estimated_gb = (params * 4) / (1024**3)
        available_gb = get_available_ram_gb()
        logger.info(f"Estimated VLM memory: {estimated_gb:.2f} GB, Available: {available_gb:.2f} GB")
        del model
        gc.collect()
        return estimated_gb < available_gb * 0.8  # 80% safety margin
    except Exception as e:
        logger.warning(f"Could not estimate VLM memory: {e}")
        return False

def load_aligned_data(path: Path) -> pd.DataFrame:
    """
    Load aligned dataset from NetCDF.
    Raises FileNotFoundError if not found (per spec).
    """
    if not path.exists():
        raise FileNotFoundError(f"Aligned data not found at {path}")
    
    import xarray as xr
    ds = xr.open_dataset(path)
    df = ds.to_dataframe().reset_index()
    
    # Ensure required columns exist
    required_cols = ['temp', 'salinity', 'nutrients', 'chlorophyll_a', 'basin', 'timestamp']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in aligned data: {missing}")
    
    return df

def train_random_forest(df: pd.DataFrame) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    Train Random Forest baseline.
    Returns model and metrics dict.
    """
    logger.info("Training Random Forest baseline...")
    
    # Prepare features and target
    feature_cols = ['temp', 'salinity', 'nutrients']
    X = df[feature_cols].values
    y = df['chlorophyll_a'].values
    
    # Train/val split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=config.seed
    )
    
    # Train model
    rf = RandomForestRegressor(
        n_estimators=500,
        max_depth=10,
        random_state=config.seed,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = rf.predict(X_val)
    metrics = {
        'rmse': float(np.sqrt(mean_squared_error(y_val, y_pred))),
        'r2': float(r2_score(y_val, y_pred)),
        'mae': float(mean_absolute_error(y_val, y_pred))
    }
    
    logger.info(f"RF Metrics: RMSE={metrics['rmse']:.4f}, R2={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}")
    return rf, metrics

def prepare_vlm_dataset(df: pd.DataFrame) -> Tuple[DataLoader, Dict[str, int]]:
    """
    Prepare dataset for VLM fine-tuning.
    Creates synthetic "images" from scalar features and text prompts.
    Returns DataLoader and feature mapping.
    """
    logger.info("Preparing VLM dataset...")
    
    class PhytoplanktonDataset(Dataset):
        def __init__(self, df: pd.DataFrame, processor: CLIPProcessor):
            self.df = df
            self.processor = processor
            
        def __len__(self):
            return len(self.df)
        
        def __getitem__(self, idx):
            row = self.df.iloc[idx]
            
            # Create text prompt
            prompt = f"Temperature: {row['temp']:.2f}, Salinity: {row['salinity']:.2f}, Nutrients: {row['nutrients']:.2f}"
            
            # Create synthetic "image" from scalar features (normalized)
            # This is a workaround since we don't have real images, but CLIP expects image input
            # We create a simple 3-channel "image" from the features
            features = np.array([row['temp'], row['salinity'], row['nutrients']])
            # Normalize to [0, 1] range approximately
            features_norm = (features - features.min()) / (features.max() - features.min() + 1e-8)
            
            # Create a simple 32x32 "image" by tiling the features
            image = np.zeros((32, 32, 3), dtype=np.float32)
            image[:, :, 0] = features_norm[0]  # Temp
            image[:, :, 1] = features_norm[1]  # Salinity
            image[:, :, 2] = features_norm[2]  # Nutrients
            
            # Process inputs
            text_inputs = self.processor(text=prompt, return_tensors="pt", padding=True, truncation=True)
            image_inputs = self.processor(images=image, return_tensors="pt", padding=True, truncation=True)
            
            return {
                'input_ids': text_inputs['input_ids'].squeeze(0),
                'attention_mask': text_inputs['attention_mask'].squeeze(0),
                'pixel_values': image_inputs['pixel_values'].squeeze(0),
                'labels': torch.tensor(row['chlorophyll_a'], dtype=torch.float32)
            }
    
    processor = CLIPProcessor.from_pretrained("facebook/clip-vit-base-patch32")
    dataset = PhytoplanktonDataset(df, processor)
    
    # Use a subset for CPU feasibility if dataset is too large
    if len(dataset) > 5000:
        logger.warning(f"Dataset too large ({len(dataset)}), sampling 5000 for CPU training")
        indices = np.random.choice(len(dataset), 5000, replace=False)
        dataset = torch.utils.data.Subset(dataset, indices)
    
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True, num_workers=0)
    
    return dataloader, {'batch_size': 16, 'num_samples': len(dataset)}

class VLMRegressor(nn.Module):
    """
    Wrapper to use CLIP for regression on chlorophyll_a prediction.
    """
    def __init__(self, clip_model: CLIPModel):
        super().__init__()
        self.clip = clip_model
        # Freeze CLIP parameters
        for param in self.clip.parameters():
            param.requires_grad = False
        
        # Add regression head
        hidden_size = 512  # CLIP text embedding size
        self.regression_head = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 1)
        )
    
    def forward(self, input_ids, attention_mask, pixel_values):
        # Get text embeddings
        text_outputs = self.clip.text_model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        text_embeds = text_outputs.pooler_output
        
        # Get image embeddings (optional, but we include for consistency)
        image_outputs = self.clip.vision_model(pixel_values=pixel_values)
        image_embeds = image_outputs.pooler_output
        
        # Combine embeddings (simple concatenation)
        combined = torch.cat([text_embeds, image_embeds], dim=1)
        
        # Regression prediction
        prediction = self.regression_head(combined)
        return prediction.squeeze(-1)

def train_vlm(df: pd.DataFrame, patience: int = 3) -> Tuple[Optional[nn.Module], Dict[str, Any]]:
    """
    Train VLM with early stopping and 8-bit fallback.
    Returns model and training info dict.
    """
    logger.info("Starting VLM training...")
    
    # Check memory
    if not check_vlm_memory_requirements():
        logger.warning("Standard VLM loading may exceed RAM, attempting 8-bit quantization")
    
    device = torch.device("cpu")
    best_loss = float('inf')
    patience_counter = 0
    vlm_fallback = False
    final_model = None
    training_metrics = {}
    
    try:
        # Try loading with 8-bit quantization first if memory is tight
        try:
            model = CLIPModel.from_pretrained(
                "facebook/clip-vit-base-patch32",
                load_in_8bit=True
            )
            logger.info("Loaded CLIP with 8-bit quantization")
        except Exception as e:
            logger.warning(f"8-bit loading failed ({e}), trying standard loading")
            model = CLIPModel.from_pretrained("facebook/clip-vit-base-patch32")
        
        model = model.to(device)
        vlm_model = VLMRegressor(model).to(device)
        
        # Prepare data
        dataloader, dataset_info = prepare_vlm_dataset(df)
        
        # Optimizer
        optimizer = torch.optim.AdamW(vlm_model.regression_head.parameters(), lr=1e-4)
        criterion = nn.MSELoss()
        
        # Training loop with early stopping
        num_epochs = 10
        for epoch in range(num_epochs):
            vlm_model.train()
            epoch_loss = 0.0
            num_batches = 0
            
            for batch in dataloader:
                optimizer.zero_grad()
                
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                pixel_values = batch['pixel_values'].to(device)
                labels = batch['labels'].to(device)
                
                predictions = vlm_model(input_ids, attention_mask, pixel_values)
                loss = criterion(predictions, labels)
                
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
            
            avg_loss = epoch_loss / num_batches
            logger.info(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
            
            # Early stopping check
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
                # Save best model
                final_model = vlm_model.state_dict()
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"Early stopping triggered at epoch {epoch+1}")
                    break
            
            # Memory monitoring
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        training_metrics = {
            'status': 'success',
            'epochs_trained': epoch + 1,
            'best_loss': float(best_loss),
            'dataset_info': dataset_info
        }
        
    except MemoryError as e:
        logger.error(f"OOM during VLM training: {e}")
        vlm_fallback = True
        training_metrics = {
            'status': 'failed_oom',
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"VLM training failed: {e}")
        vlm_fallback = True
        training_metrics = {
            'status': 'failed',
            'error': str(e)
        }
    
    # Handle fallback
    if vlm_fallback:
        logger.warning("VLM Failed (Baseline Used)")
        # Update state file
        update_state_with_fallback(True)
    
    return final_model, training_metrics

def update_state_with_fallback(vlm_fallback: bool):
    """
    Update the project state YAML with VLM fallback flag.
    """
    # Create state directory if needed
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    state = {}
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    # Update fallback flag
    state['vlm_fallback'] = vlm_fallback
    state['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Write back
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info(f"State updated: vlm_fallback={vlm_fallback}")

def save_model_artifacts(rf_model: RandomForestRegressor, rf_metrics: Dict[str, float],
                         vlm_model: Optional[nn.Module], vlm_metrics: Dict[str, Any]):
    """
    Save all model artifacts and metrics.
    """
    # Save RF model
    rf_path = ARTIFACT_DIR / "rf_model.pkl"
    with open(rf_path, 'wb') as f:
        pickle.dump(rf_model, f)
    logger.info(f"Saved RF model to {rf_path}")
    
    # Save VLM model if available
    if vlm_model is not None:
        vlm_path = ARTIFACT_DIR / "vlm_model.pt"
        torch.save(vlm_model, vlm_path)
        logger.info(f"Saved VLM model to {vlm_path}")
    
    # Save metrics
    metrics_path = ARTIFACT_DIR / "model_training_metrics.json"
    metrics_data = {
        'rf_metrics': rf_metrics,
        'vlm_metrics': vlm_metrics,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(metrics_path, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")

def main():
    """
    Main entry point for model training.
    """
    logger.info("Starting model training pipeline...")
    
    try:
        # Load data
        df = load_aligned_data(DATA_PATH)
        logger.info(f"Loaded {len(df)} samples from {DATA_PATH}")
        
        # Train RF baseline
        rf_model, rf_metrics = train_random_forest(df)
        
        # Train VLM
        vlm_model, vlm_metrics = train_vlm(df)
        
        # Save artifacts
        save_model_artifacts(rf_model, rf_metrics, vlm_model, vlm_metrics)
        
        logger.info("Model training completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        # Create fallback state if data is missing
        update_state_with_fallback(True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        update_state_with_fallback(True)
        sys.exit(1)

if __name__ == "__main__":
    main()
