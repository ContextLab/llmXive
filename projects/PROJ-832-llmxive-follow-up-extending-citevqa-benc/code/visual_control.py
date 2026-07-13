"""
Visual Control Experiment: Visual-Only Localization Pipeline (US3)

Implements the visual-only control experiment where a model receives
full-page images to predict bounding boxes without text context.

Uses microsoft/phi-3-vision-128k-instruct (4-bit quantized) for CPU execution.
Profiles memory usage to ensure < 7GB constraint.
"""
import os
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
from PIL import Image
import transformers
from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig, DynamicCache
import memory_profiler
import psutil

from config import get_config_dict
from metrics import calculate_iou, compute_vla, compute_saa

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
MODEL_ID = "microsoft/phi-3-vision-128k-instruct"
QUANTIZATION_BITS = 4

def get_quantization_config() -> BitsAndBytesConfig:
    """
    Configure 4-bit quantization for memory-efficient loading.
    Uses NF4 (Normal Float 4) for better precision on weights.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

def load_phi3_vision_model() -> Tuple[AutoModelForImageTextToText, AutoProcessor]:
    """
    Load the Phi-3 Vision model with 4-bit quantization.
    
    Returns:
        Tuple of (model, processor)
    """
    logger.info(f"Loading {MODEL_ID} with 4-bit quantization...")
    
    quantization_config = get_quantization_config()
    
    try:
        model = AutoModelForImageTextToText.from_pretrained(
            MODEL_ID,
            quantization_config=quantization_config,
            device_map="cpu",  # Force CPU usage as per constraints
            torch_dtype=torch.float16,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            cache_dir=os.environ.get("HF_HOME", "./.hf_cache")
        )
        
        processor = AutoProcessor.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            cache_dir=os.environ.get("HF_HOME", "./.hf_cache")
        )
        
        logger.info(f"Model loaded successfully. Memory footprint: {model.get_memory_footprint() / (1024**3):.2f} GB")
        return model, processor
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def build_visual_prompt(image_path: str, question: str) -> str:
    """
    Build the prompt for visual-only inference.
    
    Args:
        image_path: Path to the full-page image
        question: The question to ask about the image
        
    Returns:
        Formatted prompt string
    """
    # Phi-3 Vision uses a specific chat format
    prompt = f"""<|user|>
    <image>
    {question}
    <|end|>
    <|assistant|>
    """
    return prompt

def parse_model_response(response_text: str) -> Tuple[Optional[str], Optional[Dict[str, float]]]:
    """
    Parse the model's response to extract predicted chunk ID and bounding box.
    
    Args:
        response_text: Raw text response from the model
        
    Returns:
        Tuple of (predicted_chunk_id, bounding_box_dict)
        bounding_box_dict: {"x": float, "y": float, "width": float, "height": float}
    """
    predicted_chunk_id = None
    bounding_box = None
    
    try:
        # Look for chunk ID patterns
        import re
        chunk_id_match = re.search(r'chunk[_\s]*(id|#)?\s*[:=]?\s*([a-zA-Z0-9_]+)', response_text, re.IGNORECASE)
        if chunk_id_match:
            predicted_chunk_id = chunk_id_match.group(2)
        
        # Look for bounding box patterns (x, y, w, h or x1, y1, x2, y2)
        box_pattern = r'box\s*[:=]?\s*\[?\s*([\d.]+)\s*,?\s*([\d.]+)\s*,?\s*([\d.]+)\s*,?\s*([\d.]+)\s*\]?'
        box_match = re.search(box_pattern, response_text, re.IGNORECASE)
        
        if box_match:
            coords = [float(x) for x in box_match.groups()]
            # Assume format: x, y, width, height
            bounding_box = {
                "x": coords[0],
                "y": coords[1],
                "width": coords[2],
                "height": coords[3]
            }
        elif len(coords) == 4:
            # Try x1, y1, x2, y2 format
            bounding_box = {
                "x": coords[0],
                "y": coords[1],
                "width": coords[2] - coords[0],
                "height": coords[3] - coords[1]
            }
            
    except Exception as e:
        logger.warning(f"Failed to parse response: {e}")
        
    return predicted_chunk_id, bounding_box

def generate_response(
    model: AutoModelForImageTextToText,
    processor: AutoProcessor,
    image_path: str,
    question: str
) -> str:
    """
    Generate a response from the model given an image and question.
    
    Args:
        model: Loaded model
        processor: Loaded processor
        image_path: Path to the image
        question: Question to ask
        
    Returns:
        Generated response text
    """
    prompt = build_visual_prompt(image_path, question)
    
    # Load and preprocess image
    image = Image.open(image_path).convert("RGB")
    
    # Prepare inputs
    messages = [
        {"role": "user", "content": [
            {"type": "image"},
            {"type": "text", "text": question}
        ]}
    ]
    
    text_prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    
    inputs = processor(
        text=text_prompt,
        images=[image],
        return_tensors="pt"
    )
    
    # Move to CPU
    inputs = {k: v.to("cpu") for k, v in inputs.items()}
    
    # Generate response
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
            pad_token_id=processor.tokenizer.eos_token_id
        )
    
    # Extract generated text
    generated_text = processor.batch_decode(
        generated_ids[:, inputs["input_ids"].shape[1]:],
        skip_special_tokens=True
    )[0]
    
    return generated_text

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def profile_and_log_query(
    query_id: str,
    image_path: str,
    question: str,
    model: AutoModelForImageTextToText,
    processor: AutoProcessor
) -> Dict[str, Any]:
    """
    Profile memory usage during a single query execution.
    
    Args:
        query_id: Unique identifier for the query
        image_path: Path to the image
        question: Question to ask
        model: Loaded model
        processor: Loaded processor
        
    Returns:
        Dictionary with execution metrics and results
    """
    initial_memory = get_memory_usage_mb()
    start_time = time.time()
    
    try:
        response = generate_response(model, processor, image_path, question)
        predicted_chunk_id, bounding_box = parse_model_response(response)
        
        end_time = time.time()
        final_memory = get_memory_usage_mb()
        
        result = {
            "query_id": query_id,
            "status": "success",
            "response": response,
            "predicted_chunk_id": predicted_chunk_id,
            "bounding_box": bounding_box,
            "runtime_seconds": end_time - start_time,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "peak_memory_mb": final_memory  # Simplified for now
        }
        
        logger.info(f"Query {query_id} completed in {result['runtime_seconds']:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        logger.error(f"Query {query_id} failed: {e}")
        result = {
            "query_id": query_id,
            "status": "error",
            "error": str(e),
            "runtime_seconds": end_time - start_time,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": get_memory_usage_mb(),
            "peak_memory_mb": get_memory_usage_mb()
        }
    
    return result

def load_test_set(test_set_path: str) -> List[Dict[str, Any]]:
    """
    Load the test set from a JSON file.
    
    Args:
        test_set_path: Path to the test set JSON file
        
    Returns:
        List of test samples
    """
    with open(test_set_path, 'r') as f:
        test_set = json.load(f)
    return test_set

def run_visual_control_experiment(
    model: AutoModelForImageTextToText,
    processor: AutoProcessor,
    test_set: List[Dict[str, Any]],
    output_path: str
) -> Dict[str, Any]:
    """
    Run the visual-only control experiment on the test set.
    
    Args:
        model: Loaded model
        processor: Loaded processor
        test_set: List of test samples
        output_path: Path to save results
        
    Returns:
        Dictionary with experiment results and metrics
    """
    results = []
    memory_samples = []
    
    logger.info(f"Starting visual control experiment on {len(test_set)} samples")
    
    for sample in test_set:
        query_id = sample.get("query_id", f"query_{len(results)}")
        image_path = sample.get("image_path")
        question = sample.get("question")
        ground_truth = sample.get("ground_truth", {})
        
        if not image_path or not question:
            logger.warning(f"Skipping sample {query_id}: missing image or question")
            continue
        
        result = profile_and_log_query(
            query_id, image_path, question, model, processor
        )
        results.append(result)
        
        if result["status"] == "success":
            memory_samples.append(result["peak_memory_mb"])
            
            # Compute metrics if ground truth is available
            if "bounding_box" in ground_truth and result["bounding_box"]:
                iou = calculate_iou(
                    result["bounding_box"],
                    ground_truth["bounding_box"]
                )
                result["iou"] = iou
                
                # Compute VLA and SAA
                vla = compute_vla(iou)
                saa = compute_saa(
                    result.get("predicted_chunk_id"),
                    ground_truth.get("chunk_id"),
                    iou
                )
                result["vla"] = vla
                result["saa"] = saa
    
    # Calculate summary metrics
    successful_queries = [r for r in results if r["status"] == "success"]
    total_queries = len(results)
    
    summary = {
        "total_queries": total_queries,
        "successful_queries": len(successful_queries),
        "error_queries": total_queries - len(successful_queries),
        "success_rate": len(successful_queries) / total_queries if total_queries > 0 else 0,
        "avg_runtime": np.mean([r["runtime_seconds"] for r in successful_queries]) if successful_queries else 0,
        "peak_memory_usage_mb": max(memory_samples) if memory_samples else 0,
        "avg_memory_usage_mb": np.mean(memory_samples) if memory_samples else 0,
        "vla_score": np.mean([r.get("vla", 0) for r in successful_queries if "vla" in r]) if any("vla" in r for r in successful_queries) else None,
        "saa_score": np.mean([r.get("saa", 0) for r in successful_queries if "saa" in r]) if any("saa" in r for r in successful_queries) else None
    }
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            "results": results,
            "summary": summary
        }, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Summary: {summary}")
    
    return summary

def main():
    """Main entry point for the visual control experiment."""
    config = get_config_dict()
    
    # Paths
    test_set_path = config.get("test_set_path", "data/processed/test_set.json")
    output_path = config.get("visual_control_output", "data/results/visual_control_results.json")
    
    # Check memory constraint
    initial_memory = get_memory_usage_mb()
    logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
    
    if initial_memory / 1024 > MEMORY_LIMIT_GB:
        logger.warning(f"Initial memory usage ({initial_memory/1024:.2f} GB) exceeds limit ({MEMORY_LIMIT_GB} GB)")
        # Flag as research blocker but continue
    
    # Load model
    try:
        model, processor = load_phi3_vision_model()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        print(f"RESEARCH_BLOCKER: Model loading failed - {e}")
        return
    
    # Check memory after loading
    model_memory = get_memory_usage_mb()
    logger.info(f"Memory after model load: {model_memory:.2f} MB ({model_memory/1024:.2f} GB)")
    
    if model_memory / 1024 > MEMORY_LIMIT_GB:
        logger.error(f"Memory usage ({model_memory/1024:.2f} GB) exceeds limit ({MEMORY_LIMIT_GB} GB)")
        print(f"RESEARCH_BLOCKER: Memory usage exceeds 7GB limit after model load")
        # Save memory profile and exit
        profile_output = {
            "status": "BLOCKED",
            "reason": "Memory exceeds 7GB limit",
            "initial_memory_mb": initial_memory,
            "model_memory_mb": model_memory,
            "limit_gb": MEMORY_LIMIT_GB
        }
        with open("data/results/visual_memory_blocker.json", 'w') as f:
            json.dump(profile_output, f, indent=2)
        return
    
    # Load test set
    try:
        test_set = load_test_set(test_set_path)
        logger.info(f"Loaded {len(test_set)} test samples")
    except Exception as e:
        logger.error(f"Failed to load test set: {e}")
        return
    
    # Run experiment
    summary = run_visual_control_experiment(model, processor, test_set, output_path)
    
    # Final memory check
    final_memory = get_memory_usage_mb()
    logger.info(f"Final memory usage: {final_memory:.2f} MB ({final_memory/1024:.2f} GB)")
    
    # Save memory profile
    memory_profile = {
        "status": "OK" if final_memory / 1024 <= MEMORY_LIMIT_GB else "EXCEEDED",
        "initial_memory_mb": initial_memory,
        "model_memory_mb": model_memory,
        "final_memory_mb": final_memory,
        "peak_memory_mb": max(initial_memory, model_memory, final_memory),
        "limit_gb": MEMORY_LIMIT_GB,
        "limit_mb": MEMORY_LIMIT_GB * 1024
    }
    
    with open("data/results/visual_memory_profile.json", 'w') as f:
        json.dump(memory_profile, f, indent=2)
    
    print(f"Visual control experiment completed.")
    print(f"Memory status: {'OK' if memory_profile['status'] == 'OK' else 'EXCEEDED'}")
    print(f"Peak memory: {memory_profile['peak_memory_mb']/1024:.2f} GB (limit: {MEMORY_LIMIT_GB} GB)")

if __name__ == "__main__":
    main()
