import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import from existing project API surface
from metrics import calculate_iou, compute_saa
from config import get_config_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(get_config_dict()['paths']['logs']) / 'reasoning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import torch and transformers, handle gracefully if not available
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("Torch or Transformers not available. Running in mock mode.")
    TORCH_AVAILABLE = False

def get_quantization_config():
    """
    Returns the 4-bit quantization config for Phi-3-mini to ensure CPU tractability.
    """
    if not TORCH_AVAILABLE:
        return None
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )

def load_phi3_model():
    """
    Loads the Phi-3-mini model with 4-bit quantization for CPU execution.
    """
    if not TORCH_AVAILABLE:
        logger.error("Cannot load model: Torch not available.")
        return None, None

    model_name = "microsoft/Phi-3-mini-4k-instruct"
    config = get_config_dict()
    
    logger.info(f"Loading model: {model_name}")
    
    # Determine device (CPU only per constraints)
    device_map = "cpu"
    torch_dtype = torch.float32
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=get_quantization_config(),
            device_map=device_map,
            torch_dtype=torch_dtype,
            trust_remote_code=True
        )
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None, None

def build_prompt(query: str, context_chunks: List[Dict]) -> str:
    """
    Constructs the prompt for the reasoning model including query and retrieved chunks.
    """
    context_text = "\n\n".join([f"[Chunk {c['chunk_id']}]: {c['text']}" for c in context_chunks])
    
    prompt = f"""<|user|>
    You are an expert research assistant. Answer the following question based ONLY on the provided text chunks.
    If the answer is not in the text, state that you don't know.
    You MUST identify the specific chunk ID that contains the answer.
    
    Question: {query}
    
    Context Chunks:
    {context_text}
    
    <|end|>
    <|assistant|>
    """
    return prompt

def parse_model_response(response_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses the model's response to extract the answer and the predicted chunk ID.
    Expected format: "Answer: [answer text]. Source: [chunk_id]"
    Handles missing chunk IDs gracefully.
    """
    answer = None
    chunk_id = None
    
    # Basic parsing logic
    lines = response_text.strip().split('\n')
    for line in lines:
        if "Answer:" in line:
            answer = line.split("Answer:", 1)[1].strip()
        if "Source:" in line:
            chunk_id = line.split("Source:", 1)[1].strip()
    
    # Fallback if specific keywords aren't found but text exists
    if not answer and response_text:
        answer = response_text.strip()
        
    if not chunk_id:
        # Log error for missing chunk ID as per T016
        logger.warning(f"Failed to parse chunk ID from response: '{response_text[:100]}...'")
        return answer, None
        
    return answer, chunk_id

def generate_response(model, tokenizer, prompt: str) -> str:
    """
    Generates a response from the model given a prompt.
    """
    if model is None or tokenizer is None:
        logger.error("Model or tokenizer not loaded. Returning empty response.")
        return ""

    inputs = tokenizer(prompt, return_tensors="pt")
    # Move inputs to CPU explicitly
    inputs = {k: v.to("cpu") for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

def process_test_set(model, tokenizer, test_set_path: str, results_path: str):
    """
    Processes the entire test set, running the reasoning pipeline on each sample.
    Implements error handling for missing chunk IDs (T016).
    """
    config = get_config_dict()
    results = []
    
    # Load test set
    try:
        with open(test_set_path, 'r') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Test set not found at {test_set_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in test set: {test_set_path}")
        return

    logger.info(f"Processing {len(test_data)} test samples...")

    for i, sample in enumerate(test_data):
        query = sample.get('query', '')
        context_chunks = sample.get('context_chunks', [])
        ground_truth_chunk_id = sample.get('ground_truth_chunk_id')
        
        # Build prompt and generate response
        prompt = build_prompt(query, context_chunks)
        response_text = generate_response(model, tokenizer, prompt)
        
        # Parse response
        answer, predicted_chunk_id = parse_model_response(response_text)
        
        # Calculate metrics
        # T016: If chunk_id is missing, assign IoU=0.0 and log error
        iou_score = 0.0
        if predicted_chunk_id is None:
            logger.error(f"Sample {i}: Missing predicted chunk ID. Assigning IoU=0.0.")
            # If we have ground truth, we could theoretically calculate IoU=0, 
            # but without a prediction box/ID, we treat it as a total failure for spatial correctness.
            # We assume calculate_iou requires two valid boxes/IDs.
            # Since we only have IDs here, we map ID mismatch to IoU=0.
            spatial_correct = False
        else:
            # Check if predicted ID matches ground truth (simplified IoU for discrete IDs)
            # In a real scenario with boxes, we would call calculate_iou(box_pred, box_gt)
            # Here, we simulate: if IDs match, IoU=1.0 (perfect overlap), else 0.0
            # This is a placeholder for the actual box calculation logic which would be in metrics.py
            # assuming the test data contains boxes. If not, we fall back to ID match.
            if ground_truth_chunk_id and predicted_chunk_id == ground_truth_chunk_id:
                iou_score = 1.0
                spatial_correct = True
            else:
                iou_score = 0.0
                spatial_correct = False
                if ground_truth_chunk_id:
                    logger.warning(f"Sample {i}: ID mismatch. Pred: {predicted_chunk_id}, GT: {ground_truth_chunk_id}")

        # Calculate SAA
        # SAA = Answer Correctness AND Spatial Correctness
        # Answer Correctness: Exact Match OR Semantic Similarity >= 0.85
        # For this implementation, we assume a simple exact match or semantic check if available
        # Since we don't have the actual semantic similarity result here, we'll approximate or use a placeholder
        # In a real run, we would call semantic_similarity(answer, ground_truth_answer)
        answer_correct = False
        if answer and sample.get('ground_truth_answer'):
            if answer == sample['ground_truth_answer']:
                answer_correct = True
            # else:
            #     sim = semantic_similarity(answer, sample['ground_truth_answer'])
            #     if sim >= 0.85: answer_correct = True
        
        saa_score = 1.0 if (answer_correct and spatial_correct) else 0.0

        result = {
            "sample_id": i,
            "query": query,
            "answer": answer,
            "predicted_chunk_id": predicted_chunk_id,
            "ground_truth_chunk_id": ground_truth_chunk_id,
            "iou_score": iou_score,
            "answer_correct": answer_correct,
            "spatial_correct": spatial_correct,
            "saa_score": saa_score
        }
        results.append(result)

        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(test_data)} samples")

    # Save results
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    return results

def main():
    """
    Main entry point for the reasoning module.
    """
    config = get_config_dict()
    paths = config['paths']
    
    # Load model
    model, tokenizer = load_phi3_model()
    if model is None:
        logger.error("Model loading failed. Exiting.")
        return

    # Paths
    test_set_path = Path(paths['processed']) / "test_set.json"
    results_path = Path(paths['results']) / "reasoning_results.json"
    
    # Run evaluation
    results = process_test_set(model, tokenizer, str(test_set_path), str(results_path))
    
    if results:
        # Calculate aggregate metrics
        total_saa = sum(r['saa_score'] for r in results)
        avg_saa = total_saa / len(results)
        logger.info(f"Average SAA: {avg_saa:.4f}")

if __name__ == "__main__":
    main()