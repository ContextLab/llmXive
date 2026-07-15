import os
import sys
import argparse
import json
import pandas as pd
from main import TrainingConfig, run_spiking_training, TrainingTerminationError
from metrics.energy_logger import EnergyLogger, estimate_energy_from_time
from metrics.temporal_coding import collect_and_log_temporal_metrics, log_temporal_metrics_to_csv
from metrics.perplexity import log_perplexity_to_csv
import time

# Ensure output directory exists
os.makedirs("data/processed", exist_ok=True)

OUTPUT_FILE = "data/processed/spiking_metrics.csv"
TEMPORAL_LOG_FILE = "data/processed/temporal_coding_metrics.csv"

def run_all_seeds():
    """
    Runs the spiking training loop for a range of seeds (1-5) and saves
    the aggregated results to data/processed/spiking_metrics.csv.
    Implements T020: Saves results with an 'estimated' flag if codecarbon fails.
    """
    seeds = [1, 2, 3, 4, 5]
    records = []

    # Check if file exists to append or create new
    file_exists = os.path.exists(OUTPUT_FILE)
    
    print(f"Starting Spiking Training for seeds: {seeds}")

    for seed in seeds:
        print(f"--- Running Seed {seed} ---")
        try:
            config = TrainingConfig(
                seed=seed,
                batch_size=32,
                lr=1e-3,
                num_epochs=5,
                model_type="spiking",
                hidden_dim=256,
                num_heads=4,
                num_layers=2,
                vocab_size=1000 # Placeholder, actual loaded from dataset
            )
            
            # Setup seed
            import random
            import numpy as np
            import torch
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)

            # Initialize Energy Logger
            # T020 Logic: Wrap in try/except to handle codecarbon failure gracefully
            energy_logger = EnergyLogger()
            energy_estimated = False
            
            try:
                energy_logger.start()
            except Exception as e:
                print(f"WARNING: CodeCarbon initialization failed ({e}). Using wall-clock estimation.")
                energy_estimated = True
                # Fallback logic handled inside EnergyLogger or here if needed

            # Run Training
            # The run_spiking_training function returns a list of MetricRecord or similar structure
            # We assume it handles the loop internally or we iterate epochs here.
            # Based on T017, it returns results. We need to capture per-epoch metrics.
            
            # Re-implementing the loop here to ensure we capture per-epoch data for CSV
            # as T017 implies a training loop that produces metrics.
            
            # Load dataset (simplified for this script context, assuming helper exists)
            from data.dataset_loader import get_wikitext_dataloader
            try:
                train_loader, val_loader = get_wikitext_dataloader()
            except Exception as e:
                print(f"Error loading dataset: {e}")
                continue

            # Initialize model
            from models.spiking_transformer import create_spiking_model
            model = create_spiking_model(
                vocab_size=1000, # Should match dataset vocab
                d_model=config.hidden_dim,
                nhead=config.num_heads,
                num_layers=config.num_layers,
                dropout=0.1
            )
            
            # Training Loop (Simplified version of run_spiking_training logic)
            # We need to manually step through epochs to log per-row CSV entries
            best_val_loss = float('inf')
            patience = 3
            patience_counter = 0
            
            epoch_records = []

            for epoch in range(config.num_epochs):
                start_time = time.time()
                
                # Train one epoch
                train_loss = 0.0
                num_tokens = 0
                model.train()
                
                for batch_idx, (data, target) in enumerate(train_loader):
                    # data, target shape: [batch, seq_len]
                    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
                    optimizer.zero_grad()
                    
                    output = model(data)
                    # Assuming output is logits
                    loss_fn = torch.nn.CrossEntropyLoss()
                    # Flatten for loss
                    loss = loss_fn(output.view(-1, output.size(-1)), target.view(-1))
                    loss.backward()
                    optimizer.step()
                    
                    train_loss += loss.item() * data.size(0)
                    num_tokens += data.numel()
                
                train_loss /= num_tokens
                
                # Validate
                model.eval()
                val_loss = 0.0
                val_num_tokens = 0
                with torch.no_grad():
                    for data, target in val_loader:
                        output = model(data)
                        loss_fn = torch.nn.CrossEntropyLoss()
                        loss = loss_fn(output.view(-1, output.size(-1)), target.view(-1))
                        val_loss += loss.item() * data.size(0)
                        val_num_tokens += data.numel()
                
                val_loss /= val_num_tokens
                perplexity = float(torch.exp(torch.tensor(val_loss)).item())
                
                wall_clock = time.time() - start_time
                
                # Energy Logging (T020 specific: estimated flag)
                if energy_estimated:
                    # Fallback estimation if codecarbon failed
                    estimated_kwh = estimate_energy_from_time(wall_clock, is_cpu=True)
                    energy_per_token = estimated_kwh / num_tokens if num_tokens > 0 else 0.0
                    energy_flag = "estimated"
                else:
                    energy_logger.stop()
                    energy_record = energy_logger.get_record()
                    energy_per_token = energy_record.energy / num_tokens if num_tokens > 0 and energy_record.energy else 0.0
                    energy_flag = "measured"

                # Temporal Coding Metrics (T019 integration)
                # Collect spike stats from the model if possible
                # For this implementation, we call the logging function which might extract from model state
                # or simulate based on current batch if model exposes hooks.
                # We assume collect_and_log_temporal_metrics returns a dict or None
                temporal_data = collect_and_log_temporal_metrics(model, val_loader)
                temporal_str = json.dumps(temporal_data) if temporal_data else "{}"

                # Create record
                record = {
                    "seed": seed,
                    "epoch": epoch + 1,
                    "perplexity": perplexity,
                    "energy_per_token_kWh": energy_per_token,
                    "wall_clock_time": wall_clock,
                    "energy_flag": energy_flag,
                    "temporal_coding_metrics": temporal_str
                }
                epoch_records.append(record)
                
                # Log to CSV immediately (or append to list and save at end)
                # T020: Save to CSV
                log_perplexity_to_csv(record, OUTPUT_FILE, append=True)
                
                print(f"Epoch {epoch+1}: PPL={perplexity:.2f}, Energy={energy_per_token:.6f} kWh/token ({energy_flag})")

                # Early stopping check
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        print(f"Early stopping triggered at epoch {epoch+1}")
                        break

            # Save final aggregated results if needed, but we logged per epoch above.
            # T020 requires the file to exist.
            
        except TrainingTerminationError as e:
            print(f"Training terminated for seed {seed}: {e}")
            # Handle zero spike report logic if needed
        except Exception as e:
            print(f"Error running seed {seed}: {e}")
            import traceback
            traceback.print_exc()

    print(f"Completed. Results saved to {OUTPUT_FILE}")

def main():
    parser = argparse.ArgumentParser(description="Run Spiking Training for multiple seeds")
    parser.add_argument('--seeds', type=int, nargs='+', default=[1,2,3,4,5], help="List of seeds")
    args = parser.parse_args()
    run_all_seeds()

if __name__ == "__main__":
    main()
