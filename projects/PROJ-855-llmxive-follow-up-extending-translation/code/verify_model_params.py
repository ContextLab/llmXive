"""
Verify Model Parameters Task (T025)

This script loads the trained Transformer model, prints a summary of its architecture,
calculates the total parameter count, and verifies it is strictly less than 10,000,000.
It exits with code 1 if the parameter count exceeds the limit or if the model file is missing.
"""
import os
import sys
import torch

# Ensure code directory is in path for imports
code_dir = os.path.join(os.path.dirname(__file__), '..')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from models.transformer import TranslationTransformer, count_parameters

def main():
    # Define paths relative to project root
    # Assuming this script is run as `python code/verify_model_params.py`
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(project_root, 'data', 'processed', 'trained_model.pt')

    # Check if model exists
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found at {model_path}")
        print("Please ensure T024 (Save trained model) has been completed successfully.")
        sys.exit(1)

    print(f"Loading model from: {model_path}")

    try:
        # Load the state dict
        # We need to instantiate the model architecture first to load the weights
        # The model architecture is defined in TranslationTransformer
        # We assume default configuration matches training, but we need to reconstruct it.
        # Since we don't have the config saved with the model in this specific step,
        # we assume the standard architecture defined in T021.
        # However, to be safe, we load the state dict and check keys, or just count params
        # on a fresh instance if we know the architecture.
        # A safer approach for verification: Load the full model if saved as object,
        # or reconstruct if only state_dict.
        # T024 says "Save trained model weights". Let's assume it saves the state_dict.
        
        # We need to know the hidden dim, layers, etc. to reconstruct.
        # Since T021 constrained it to <10M, we can try to load the state dict
        # and infer or just create a standard instance if we assume defaults.
        # Let's assume the standard config used in training was:
        # d_model=64, nhead=4, num_layers=4, dim_feedforward=128 (example small config)
        # But to be robust, we should load the config if available.
        # For this task, we will instantiate the model with the constraints known from T021
        # and load the weights. If keys mismatch, we fail.
        
        # Reconstructing the model with the constraints from T021 (<10M params)
        # We use a standard small configuration that fits the constraint.
        # If the training script saved specific hyperparams, we should load them.
        # Assuming we load the full model object for simplicity if saved, 
        # but standard practice is state_dict.
        
        # Let's try to load the state dict and match with a standard small config.
        # If the training script (T022/T023) used specific args, we need them.
        # Since we can't read T022/T023 code here, we assume a standard "lightweight" config.
        # A 4-layer transformer with d_model=64 is well under 10M.
        
        # Strategy: Load the state dict. If we can't reconstruct exactly, we fail.
        # But the task is to VERIFY the count.
        # Let's assume the model was saved as a full object or we have a way to reconstruct.
        # Given the constraints, let's instantiate a TranslationTransformer with 
        # parameters that definitely result in <10M and load the weights.
        
        # Standard small config for <10M:
        # d_model=64, nhead=4, num_layers=4, dim_feedforward=128, input_dim=7 (translation)
        # This is roughly: 4 * (2*64*128 + 64*64) ~ 130k params + embedding ~ 50k. Very small.
        # Even d_model=256 is safe.
        
        # We will instantiate with a config that is known to be safe and load the weights.
        # If the saved model has different keys, it will raise an error.
        
        # To be absolutely safe, we check if the file contains a dict with 'model_state' or similar
        # or just a state_dict.
        
        checkpoint = torch.load(model_path, map_location='cpu')
        
        # Determine how to load
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
            # We need to reconstruct the model to load. 
            # We assume the training used a specific config. 
            # Since we can't read it, we assume the default args of TranslationTransformer.
            # Let's look at the class signature in the API surface: TranslationTransformer
            # It likely has default args.
            model = TranslationTransformer() 
            model.load_state_dict(state_dict)
        elif isinstance(checkpoint, dict) and 'model' in checkpoint:
             model = TranslationTransformer()
             model.load_state_dict(checkpoint['model'])
        else:
            # Assume it's the state dict directly or the model object
            # If it's a model object, we can just count
            if isinstance(checkpoint, TranslationTransformer):
                model = checkpoint
            else:
                # Try to load as state dict into a default model
                model = TranslationTransformer()
                model.load_state_dict(checkpoint)

        # Verify parameters
        total_params = count_parameters(model)
        
        print("-" * 50)
        print("MODEL SUMMARY")
        print("-" * 50)
        print(model)
        print("-" * 50)
        print(f"Total Parameters: {total_params:,}")
        print("-" * 50)
        
        LIMIT = 10_000_000
        
        if total_params < LIMIT:
            print(f"SUCCESS: Model has {total_params:,} parameters, which is less than {LIMIT:,}.")
            print("Verification PASSED.")
            sys.exit(0)
        else:
            print(f"FAILURE: Model has {total_params:,} parameters, which EXCEEDS the limit of {LIMIT:,}.")
            print("Verification FAILED.")
            sys.exit(1)
            
    except Exception as e:
        print(f"ERROR: Failed to load or verify model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()