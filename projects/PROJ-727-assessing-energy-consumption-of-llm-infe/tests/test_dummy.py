"""
Test module for T008a: Dummy Inference Verification.
Performs a lightweight import check and a single-token generation using a small dummy prompt
to verify the environment without OOM risk.
"""
import pytest
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def test_dummy_inference():
    """
    Verify that the environment can load a tokenizer and a tiny model (or a dummy configuration)
    and perform a single forward pass/generation without crashing.
    """
    print("Starting dummy inference test...")
    
    # 1. Import Check
    try:
        from code.config import get_model_hf_id
        from code.inference import load_problems_from_jsonl
        from codecarbon import EmissionsTracker
    except ImportError as e:
        pytest.fail(f"Failed to import required modules: {e}")

    # 2. Load a very small model or a dummy config to avoid OOM.
    # We use 'hf-internal-testing/tiny-random-gpt2' which is < 100MB and safe for CPU.
    model_id = "hf-internal-testing/tiny-random-gpt2"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Add pad token if missing
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model in float32 to ensure compatibility, CPU
        model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
        
        # 3. Perform a single-token generation
        prompt = "def hello():"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Ensure we don't generate too many tokens
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=1, 
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"Dummy generation successful: '{generated_text}'")
        assert len(generated_text) > len(prompt), "Model failed to generate tokens."
        
    except Exception as e:
        pytest.fail(f"Dummy inference execution failed: {e}")

    print("Dummy inference test passed.")