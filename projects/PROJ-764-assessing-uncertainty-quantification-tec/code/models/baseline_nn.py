import os
import torch
import torch.nn as nn
import numpy as np
import yaml
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)

def load_processed_data(split: str = "train"):
    path = Path(f"data/processed/features_{split}_20pca.csv")
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)

class HeteroscedasticNN(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: list = [32, 16]):
        """
        Heteroscedastic Neural Network.
        Designed to have <= 10k parameters.
        input_dim: 20 (from PCA)
        hidden_dims: [32, 16]
        Params calculation:
          Layer 1: 20*32 + 32 = 672
          Layer 2: 32*16 + 16 = 528
          Mean Head: 16*1 + 1 = 17
          Var Head: 16*1 + 1 = 17
          Total: 672 + 528 + 17 + 17 = 1234 (well under 10k)
        """
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.ReLU())
            prev_dim = h
        self.fc = nn.Sequential(*layers)
        self.mean_head = nn.Linear(prev_dim, 1)
        self.var_head = nn.Linear(prev_dim, 1)

    def forward(self, x):
        h = self.fc(x)
        mean = self.mean_head(h)
        var = torch.exp(self.var_head(h))  # Ensure positive variance
        return mean, var

def negative_log_likelihood_loss(mean, var, target):
    # Heteroscedastic loss: 0.5 * (log(var) + (target - mean)^2 / var)
    # Avoid division by zero or log(0)
    var = torch.clamp(var, min=1e-6)
    return 0.5 * torch.mean(torch.log(var) + ((target - mean) ** 2) / var)

def train_model(model, train_loader, val_loader, epochs=100, lr=1e-3, patience=10):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_val_loss = float('inf')
    best_model_state = None
    patience_counter = 0
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            optimizer.zero_grad()
            mean, var = model(X)
            loss = negative_log_likelihood_loss(mean, var, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        
        # Validation phase
        if val_loader is not None:
            model.eval()
            val_loss = 0
            with torch.no_grad():
                for X, y in val_loader:
                    mean, var = model(X)
                    loss = negative_log_likelihood_loss(mean, var, y)
                    val_loss += loss.item()
            avg_val_loss = val_loss / len(val_loader)
            scheduler.step(avg_val_loss)
            
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                best_model_state = model.state_dict().copy()
                patience_counter = 0
            else:
                patience_counter += 1
                
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}, Train Loss: {avg_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
        else:
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}, Train Loss: {avg_loss:.4f}")
        
        if patience_counter >= patience:
            logger.info(f"Early stopping at epoch {epoch+1}")
            break
    
    # Restore best model if validation was used
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        
    return model

def main(seed: int = 42):
    torch.manual_seed(seed)
    np.random.seed(seed)

    config = load_config()
    input_dim = 20  # From PCA (20 components)
    
    # Count parameters to ensure <= 10k
    model = HeteroscedasticNN(input_dim, hidden_dims=[32, 16])
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Model total parameters: {total_params}")
    if total_params > 10000:
        raise ValueError(f"Model has {total_params} parameters, which exceeds the 10k limit.")
    else:
        logger.info(f"Parameter count {total_params} is within 10k limit.")

    # Load data
    train_df = load_processed_data("train")
    val_df = load_processed_data("val")

    # Extract PCA features and target
    pca_cols = [f'pca_{i}' for i in range(20)]
    
    X_train = torch.tensor(train_df[pca_cols].values, dtype=torch.float32)
    y_train = torch.tensor(train_df['formation_energy'].values, dtype=torch.float32).unsqueeze(1)
    X_val = torch.tensor(val_df[pca_cols].values, dtype=torch.float32)
    y_val = torch.tensor(val_df['formation_energy'].values, dtype=torch.float32).unsqueeze(1)

    train_dataset = torch.utils.data.TensorDataset(X_train, y_train)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    val_dataset = torch.utils.data.TensorDataset(X_val, y_val)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32, shuffle=False)

    model = train_model(model, train_loader, val_loader, epochs=100, lr=1e-3)

    # Save model
    out_dir = Path("results/models")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "baseline_seed42.pt"
    torch.save(model.state_dict(), output_path)
    logger.info(f"Baseline model saved to {output_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()