import json
import logging
import sys
import re
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path('logs/01_data_curation.log'))
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_TOKENS = 200
TIMEOUT_SECONDS = 300
MAX_MEMORY_GB = 7
COMPLEXITY_THRESHOLDS = {
    'low': (0, 5),
    'medium': (5, 10),
    'high': (10, float('inf'))
}

def fetch_code_search_net() -> List[Dict[str, Any]]:
    """Fetch Python subset from CodeSearchNet dataset."""
    try:
        from datasets import load_dataset
        logger.info("Fetching CodeSearchNet Python subset...")
        dataset = load_dataset("codeparrot/code-search-net", "python", split="train", streaming=True)
        snippets = []
        count = 0
        for item in dataset:
            if count >= 100:  # Limit for demonstration
                break
            snippets.append({
                'snippet_id': f"csnet_{count}",
                'code': item['code'],
                'language': item['language']
            })
            count += 1
        logger.info(f"Fetched {count} snippets from CodeSearchNet")
        return snippets
    except Exception as e:
        logger.error(f"Failed to fetch CodeSearchNet: {e}")
        raise

def calculate_cyclomatic_complexity(code: str) -> float:
    """Calculate raw cyclomatic complexity score for a code snippet."""
    try:
        # Simple heuristic: count decision points
        patterns = [
            r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\band\b', r'\bor\b', r'\bexcept\b', r'\bassert\b',
            r'\bcase\b'  # Python 3.10+
        ]
        complexity = 1  # Base complexity
        for pattern in patterns:
            matches = re.findall(pattern, code)
            complexity += len(matches)
        logger.debug(f"Cyclomatic complexity calculated: {complexity}")
        return float(complexity)
    except Exception as e:
        logger.error(f"Error calculating complexity for code: {e}")
        return 1.0

def label_complexity(raw_score: float) -> str:
    """Label complexity based on raw score ranges."""
    if raw_score <= COMPLEXITY_THRESHOLDS['low'][1]:
        return 'low'
    elif raw_score <= COMPLEXITY_THRESHOLDS['medium'][1]:
        return 'medium'
    else:
        return 'high'

def process_complexity(snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process snippets to add complexity scores and labels."""
    processed = []
    for snippet in snippets:
        raw_score = calculate_cyclomatic_complexity(snippet['code'])
        label = label_complexity(raw_score)
        processed.append({
            **snippet,
            'complexity_score': raw_score,
            'complexity': label
        })
        logger.debug(f"Processed snippet {snippet['snippet_id']}: score={raw_score}, label={label}")
    return processed

def save_snippets(snippets: List[Dict[str, Any]], output_path: str):
    """Save processed snippets to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(snippets, f, indent=2)
    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

def generate_explanation(code: str, complexity: str, model_name: str = "CodeLlama-7B") -> Dict[str, Any]:
    """Generate LLM explanation for code snippet with fallback logic."""
    start_time = time.time()
    model_loaded = False
    fallback_triggered = False
    model_used = model_name
    explanation_text = ""
    token_count = 0
    status = "success"

    try:
        # Attempt to load CodeLlama-7B (4-bit quantized)
        try:
            logger.info(f"Attempting to load {model_name}...")
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-Instruct-hf")
            
            # Check memory availability before loading
            if torch.cuda.is_available():
                device_map = "auto"
            else:
                # CPU fallback with 4-bit quantization
                try:
                    from transformers import BitsAndBytesConfig
                    bnb_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.float16
                    )
                    model = AutoModelForCausalLM.from_pretrained(
                        "codellama/CodeLlama-7b-Instruct-hf",
                        quantization_config=bnb_config,
                        device_map="cpu"
                    )
                    model_loaded = True
                    logger.info("CodeLlama-7B loaded successfully on CPU with 4-bit quantization")
                except Exception as e:
                    logger.warning(f"CodeLlama-7B failed to load on CPU: {e}")
                    raise
        except Exception as e:
            logger.warning(f"CodeLlama-7B loading failed: {e}")
            # Fallback to TinyLlama
            fallback_triggered = True
            logger.info("Switching to TinyLlama fallback model...")
            
            from transformers import AutoTokenizer, AutoModelForCausalLM
            tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
            model = AutoModelForCausalLM.from_pretrained(
                "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                device_map="cpu"
            )
            model_loaded = True
            model_used = "TinyLlama-1.1B-Chat-v1.0"
            logger.info("TinyLlama fallback model loaded successfully")

        if not model_loaded:
            raise Exception("No model could be loaded")

        # Generate explanation
        prompt = f"Explain the following {complexity} complexity code snippet in simple terms. Keep it under {MAX_TOKENS} tokens:\n\n{code}"
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_TOKENS,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        explanation_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        token_count = len(outputs[0])
        
        elapsed_time = time.time() - start_time
        if elapsed_time > TIMEOUT_SECONDS:
            logger.warning(f"Generation exceeded timeout ({elapsed_time}s > {TIMEOUT_SECONDS}s)")
            status = "skipped"
        
        logger.info(f"Generated explanation using {model_used}: {token_count} tokens, {elapsed_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        status = "skipped"
        explanation_text = ""
        token_count = 0
        model_used = model_name if not fallback_triggered else "TinyLlama-1.1B-Chat-v1.0"

    # Log skipped snippets and fallback triggers
    if status == "skipped":
        logger.warning(f"SKIPPED: Snippet explanation generation failed. Reason: {str(e)}")
    if fallback_triggered:
        logger.info(f"FALLBACK TRIGGERED: Switched to TinyLlama for snippet generation due to CodeLlama failure")

    return {
        'explanation': explanation_text,
        'token_count': token_count,
        'model_used': model_used,
        'status': status,
        'fallback_triggered': fallback_triggered
    }

def main():
    """Main function to run data curation and explanation generation."""
    logger.info("Starting data curation and explanation generation pipeline...")
    
    # Fetch and process data
    snippets = fetch_code_search_net()
    processed_snippets = process_complexity(snippets)
    
    # Save processed snippets
    save_path = "data/intermediate/snippets_processed.json"
    save_snippets(processed_snippets, save_path)
    
    # Generate explanations
    explanations = []
    for snippet in processed_snippets:
        result = generate_explanation(
            code=snippet['code'],
            complexity=snippet['complexity'],
            model_name="CodeLlama-7B"
        )
        explanations.append({
            'snippet_id': snippet['snippet_id'],
            'code': snippet['code'],
            'complexity': snippet['complexity'],
            'complexity_score': snippet['complexity_score'],
            'explanation': result['explanation'],
            'token_count': result['token_count'],
            'model_used': result['model_used'],
            'status': result['status'],
            'fallback_triggered': result['fallback_triggered']
        })
        
        # Log skipped snippets
        if result['status'] == 'skipped':
            logger.warning(f"SKIPPED: Snippet {snippet['snippet_id']} - Explanation generation failed")
        
        # Log fallback triggers
        if result['fallback_triggered']:
            logger.info(f"FALLBACK: Snippet {snippet['snippet_id']} used TinyLlama due to CodeLlama failure")
    
    # Save explanations
    explanations_path = "data/intermediate/explanations.json"
    save_snippets(explanations, explanations_path)
    
    logger.info(f"Pipeline completed. Generated {len(explanations)} explanations.")
    logger.info(f"Output saved to {explanations_path}")
    
    return explanations

if __name__ == "__main__":
    main()
