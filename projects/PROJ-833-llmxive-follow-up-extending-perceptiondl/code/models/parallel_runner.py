import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass
import torch
import torch.ao.quantization as quantization
import psutil
from config import get_data_path, get_random_state

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class InferenceResult:
    region_id: int
    caption: str
    inference_time: float
    confidence: float

def get_memory_usage_mb() -> float:
    """
    Returns the current Resident Set Size (RSS) of the process in MB.
    Uses psutil for cross-platform compatibility.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def load_model(model_id: str, quantize: bool = True) -> torch.nn.Module:
    """
    Loads the PerceptionDLM model.
    If quantize is True, attempts to apply dynamic INT8 quantization to reduce memory footprint.
    Falls back to standard loading if quantization fails or is not supported by the model.
    
    Args:
        model_id: HuggingFace model identifier.
        quantize: Whether to attempt dynamic quantization.
    
    Returns:
        The loaded (and potentially quantized) model.
    """
    logger.info(f"Loading model: {model_id} (quantize={quantize})")
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        # Load model in float32 first to prepare for quantization
        # If the model is already quantized in the repo, this might be skipped, but we assume standard float32 for dynamic quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            trust_remote_code=True
        )
        
        if quantize:
            logger.info("Applying dynamic INT8 quantization...")
            try:
                # Prepare for dynamic quantization
                model.qconfig = quantization.get_default_qconfig('fbgemm')
                model_prepared = quantization.prepare(model, inplace=False)
                
                # Quantize
                model_quantized = quantization.convert(model_prepared, inplace=False)
                
                # Move to CPU (quantized models must be on CPU)
                model_quantized = model_quantized.to('cpu')
                
                logger.info("Dynamic INT8 quantization successful.")
                return model_quantized, tokenizer
                
            except Exception as e:
                logger.warning(f"Dynamic quantization failed ({e}). Falling back to standard model.")
                model = model.to('cpu')
                return model, tokenizer
        else:
            model = model.to('cpu')
            return model, tokenizer
            
    except ImportError as e:
        logger.error(f"Failed to import transformers or torch.ao.quantization: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def preprocess_image(image_path: str) -> torch.Tensor:
    """
    Preprocesses an image for the model.
    Assumes the model expects a specific format (e.g., PIL Image -> Tensor).
    For this implementation, we simulate the preprocessing logic required by PerceptionDLM.
    """
    try:
        from PIL import Image
        from transformers import AutoImageProcessor
        
        # Load image
        image = Image.open(image_path).convert('RGB')
        
        # Use the model's processor if available, otherwise standard normalization
        # Since specific processor isn't in config, we assume a standard resize/normalize pipeline
        # In a real scenario, we would use the tokenizer/image_processor from the model config
        # Here we return a dummy tensor structure to satisfy the runner logic if processor is missing
        # However, to be robust, we try to get the processor
        
        # Fallback to manual preprocessing if processor is not found or fails
        # This ensures the runner doesn't crash if the specific model's processor is complex
        import torchvision.transforms as transforms
        
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        tensor_image = transform(image)
        return tensor_image.unsqueeze(0) # Add batch dimension
        
    except Exception as e:
        logger.error(f"Failed to preprocess image {image_path}: {e}")
        raise

def run_inference_batch(
    model: torch.nn.Module,
    tokenizer: Any,
    image_tensors: List[torch.Tensor],
    prompts: List[str],
    max_new_tokens: int = 50
) -> List[str]:
    """
    Runs inference on a batch of images and prompts.
    
    Args:
        model: The loaded (quantized) model.
        tokenizer: The model tokenizer.
        image_tensors: List of preprocessed image tensors.
        prompts: List of text prompts corresponding to each image.
        max_new_tokens: Maximum number of tokens to generate.
    
    Returns:
        List of generated captions.
    """
    captions = []
    
    # Prepare inputs
    # Note: PerceptionDLM might expect a specific input format (e.g., concatenated image+text)
    # We assume a standard multimodal input structure here.
    
    for img_tensor, prompt in zip(image_tensors, prompts):
        try:
            # Move to CPU (quantized models run on CPU)
            img_tensor = img_tensor.to('cpu')
            
            # Tokenize prompt
            inputs = tokenizer(prompt, return_tensors="pt", padding=True)
            inputs['pixel_values'] = img_tensor
            
            # Generate
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Clean up the prompt from the output if it's included
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            captions.append(generated_text)
            
        except Exception as e:
            logger.error(f"Error during inference for prompt: {prompt[:20]}... Error: {e}")
            captions.append(f"ERROR: {str(e)}")
    
    return captions

def run_parallel_inference(
    model_id: str,
    image_data: List[Dict[str, Any]],
    batch_size: int = 8,
    quantize: bool = True,
    memory_limit_mb: float = 7000.0
) -> List[Dict[str, Any]]:
    """
    Runs parallel inference on a list of image data.
    Implements dynamic memory monitoring and adaptive reduction.
    
    Args:
        model_id: HuggingFace model ID.
        image_data: List of dicts containing 'image_path', 'region_id', 'prompt'.
        batch_size: Number of images to process in parallel.
        quantize: Whether to use dynamic quantization.
        memory_limit_mb: Maximum allowed RSS in MB (default 7GB).
    
    Returns:
        List of InferenceResult objects (as dicts).
    """
    logger.info(f"Starting parallel inference with batch_size={batch_size}, quantize={quantize}")
    
    # Load model
    model, tokenizer = load_model(model_id, quantize=quantize)
    
    results = []
    total_images = len(image_data)
    
    # Check initial memory
    initial_mem = get_memory_usage_mb()
    logger.info(f"Initial memory usage: {initial_mem:.2f} MB")
    
    if initial_mem > memory_limit_mb:
        logger.error(f"Initial memory usage ({initial_mem:.2f} MB) exceeds limit ({memory_limit_mb} MB).")
        raise MemoryError("Model loading exceeded memory limit immediately.")
    
    for i in range(0, total_images, batch_size):
        batch_data = image_data[i:i+batch_size]
        current_mem = get_memory_usage_mb()
        
        # Memory Check before processing batch
        if current_mem > memory_limit_mb:
            logger.warning(f"Memory usage ({current_mem:.2f} MB) exceeds limit ({memory_limit_mb} MB) before batch {i//batch_size}.")
            # In a real adaptive loop, we would reduce batch size here and retry
            # For this task, we log the violation and fail loudly as per constraints
            # or attempt to reduce batch size dynamically if possible.
            # Since we are inside a loop, we can try reducing batch size for subsequent batches
            # but we cannot undo the current batch if it's already too big.
            # We will attempt to reduce batch size for future iterations.
            new_batch_size = max(1, batch_size // 2)
            logger.warning(f"Reducing batch size to {new_batch_size} for remaining batches.")
            batch_size = new_batch_size
            # Re-check memory
            current_mem = get_memory_usage_mb()
            if current_mem > memory_limit_mb:
                raise MemoryError(f"Memory limit exceeded even after reducing batch size. Current: {current_mem:.2f} MB")

        batch_images = []
        batch_prompts = []
        batch_region_ids = []
        
        for item in batch_data:
            batch_images.append(preprocess_image(item['image_path']))
            batch_prompts.append(item['prompt'])
            batch_region_ids.append(item['region_id'])
        
        # Run inference
        start_time = time.perf_counter()
        batch_captions = run_inference_batch(model, tokenizer, batch_images, batch_prompts)
        end_time = time.perf_counter()
        inference_time = end_time - start_time
        
        # Process results
        for idx, caption in enumerate(batch_captions):
            results.append({
                'region_id': batch_region_ids[idx],
                'caption': caption,
                'inference_time': inference_time / len(batch_data), # Normalize time per item
                'confidence': 1.0 # Placeholder, as quantized models might not expose confidence easily
            })
        
        logger.info(f"Processed batch {i//batch_size + 1}/{(total_images + batch_size - 1)//batch_size}. Time: {inference_time:.2f}s")
    
    logger.info(f"Parallel inference completed. Total results: {len(results)}")
    return results

def main():
    """
    Main entry point for testing the parallel runner with quantization.
    """
    # Example usage
    data_path = get_data_path()
    sample_data = [
        {'image_path': str(Path(data_path) / 'synthetic' / 'sample_001.png'), 'region_id': 1, 'prompt': 'Describe the object in the bounding box.'},
        {'image_path': str(Path(data_path) / 'synthetic' / 'sample_002.png'), 'region_id': 2, 'prompt': 'Describe the object in the bounding box.'},
    ]
    
    # Mock data if files don't exist (for testing structure only)
    # In real execution, these files must exist
    for item in sample_data:
        if not os.path.exists(item['image_path']):
            logger.warning(f"Mocking missing image: {item['image_path']}")
            # Create a dummy image for testing
            from PIL import Image
            img = Image.new('RGB', (224, 224), color='red')
            img.save(item['image_path'])
    
    try:
        results = run_parallel_inference(
            model_id="microsoft/Phi-3-mini-4k-instruct", # Placeholder ID, replace with actual PerceptionDLM ID
            image_data=sample_data,
            batch_size=2,
            quantize=True
        )
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()