import logging
import time
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import torch
from datasets import load_dataset, Dataset
from src.models import EvaluationReport

logger = logging.getLogger(__name__)

class PerplexityDataset:
    """Wrapper for dataset used in perplexity calculation."""
    def __init__(self, dataset: Dataset, tokenizer: Any, max_length: int = 2048):
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        item = self.dataset[idx]
        text = item.get('text', '')
        if isinstance(text, list):
            text = ' '.join(text)
        encoding = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=self.max_length)
        return encoding

def calculate_perplexity(model: torch.nn.Module, dataset: PerplexityDataset) -> float:
    """
    Calculate perplexity on a dataset.
    Note: This is a placeholder for the actual implementation which depends on T027.
    """
    model.eval()
    total_loss = 0.0
    total_tokens = 0

    with torch.no_grad():
        for i in range(len(dataset)):
            batch = dataset[i]
            input_ids = batch['input_ids']
            labels = input_ids.clone()
            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs.loss
            total_loss += loss.item() * labels.numel()
            total_tokens += labels.numel()

    avg_loss = total_loss / total_tokens
    perplexity = torch.exp(torch.tensor(avg_loss)).item()
    return perplexity

def load_hotpotqa_validation() -> Dataset:
    """
    Load the HotpotQA validation dataset from Hugging Face.
    Raises an explicit error if the dataset is unavailable.
    """
    try:
        logger.info("Attempting to load hotpotqa validation dataset...")
        ds = load_dataset("hotpotqa", "plain_text", split="validation", streaming=False)
        logger.info(f"Successfully loaded hotpotqa validation dataset with {len(ds)} examples.")
        return ds
    except Exception as e:
        error_msg = f"CRITICAL: Failed to load hotpotqa validation dataset. Spec FR-007 requires this dataset. Error: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def evaluate_qa(model: torch.nn.Module, dataset: Dataset, tokenizer: Any, 
                static_inference_fn: Optional[Callable] = None,
                dynamic_baseline_fn: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Evaluate QA accuracy on the HotpotQA validation dataset.
    
    Args:
        model: The model to evaluate (either dynamic or static HiLS).
        dataset: The HotpotQA validation dataset.
        tokenizer: The tokenizer for the model.
        static_inference_fn: Optional function for static inference if model needs special handling.
        dynamic_baseline_fn: Optional function for dynamic baseline comparison.
        
    Returns:
        Dict with 'accuracy' (float) and 'total_examples' (int).
    """
    logger.info("Starting QA evaluation on HotpotQA validation set.")
    
    if dataset is None:
        raise ValueError("Dataset cannot be None. Load HotpotQA first.")

    correct = 0
    total = 0
    results = []

    # Simple evaluation loop - in a real scenario, this would involve more complex
    # answer extraction and matching logic depending on the model's output format.
    # For this implementation, we assume the model can generate an answer given the question.
    
    model.eval()
    device = next(model.parameters()).device

    with torch.no_grad():
        for i, item in enumerate(dataset):
            question = item.get('question', '')
            answer = item.get('answer', '')
            
            if not question or not answer:
                continue

            # Prepare input
            inputs = tokenizer(question, return_tensors='pt', truncation=True, max_length=512)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate answer (simplified - in reality, this would be more complex)
            # This assumes the model can be used for generation
            try:
                # If static_inference_fn is provided, use it for static model
                if static_inference_fn is not None:
                    output = static_inference_fn(model, inputs)
                else:
                    # Standard generation
                    output = model.generate(
                        **inputs,
                        max_new_tokens=50,
                        do_sample=False,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                # Decode generated answer
                generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
                
                # Simple accuracy check (exact match or substring match)
                # In a real implementation, this would use more sophisticated metrics
                is_correct = answer.lower() in generated_text.lower() or generated_text.lower() in answer.lower()
                
                if is_correct:
                    correct += 1
                
                total += 1
                results.append({
                    'question': question,
                    'gold_answer': answer,
                    'predicted_answer': generated_text,
                    'correct': is_correct
                })
                
                if total % 10 == 0:
                    logger.info(f"Processed {total} examples, current accuracy: {correct/total:.4f}")
                    
            except Exception as e:
                logger.warning(f"Failed to process example {i}: {str(e)}")
                total += 1  # Count as attempted but incorrect

    accuracy = correct / total if total > 0 else 0.0
    logger.info(f"QA Evaluation Complete: {correct}/{total} correct, accuracy: {accuracy:.4f}")
    
    return {
        'accuracy': accuracy,
        'total_examples': total,
        'correct_count': correct,
        'results_sample': results[:10]  # Store first 10 for inspection
    }

def run_qa_evaluation_comparison(
    dynamic_model: torch.nn.Module,
    static_model: torch.nn.Module,
    tokenizer: Any,
    dynamic_baseline_fn: Optional[Callable] = None,
    static_inference_fn: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Run QA evaluation on both dynamic and static models and compare results.
    
    Args:
        dynamic_model: The dynamic HiLS model.
        static_model: The static HiLS model.
        tokenizer: The tokenizer.
        dynamic_baseline_fn: Optional function for dynamic inference.
        static_inference_fn: Optional function for static inference.
        
    Returns:
        Dict with accuracy for both models and degradation percentage.
    """
    # Load HotpotQA dataset
    hotpotqa_dataset = load_hotpotqa_validation()
    
    # Evaluate dynamic baseline
    logger.info("Evaluating dynamic baseline...")
    dynamic_results = evaluate_qa(
        dynamic_model, 
        hotpotqa_dataset, 
        tokenizer, 
        static_inference_fn=None,  # Dynamic doesn't need special handling
        dynamic_baseline_fn=dynamic_baseline_fn
    )
    
    # Evaluate static model
    logger.info("Evaluating static model...")
    static_results = evaluate_qa(
        static_model,
        hotpotqa_dataset,
        tokenizer,
        static_inference_fn=static_inference_fn,
        dynamic_baseline_fn=dynamic_baseline_fn
    )
    
    # Calculate degradation
    dynamic_acc = dynamic_results['accuracy']
    static_acc = static_results['accuracy']
    degradation = dynamic_acc - static_acc
    degradation_percent = (degradation / dynamic_acc * 100) if dynamic_acc > 0 else 0.0
    
    comparison = {
        'dynamic_accuracy': dynamic_acc,
        'static_accuracy': static_acc,
        'absolute_degradation': degradation,
        'percent_degradation': degradation_percent,
        'dynamic_total': dynamic_results['total_examples'],
        'static_total': static_results['total_examples'],
        'dataset': 'hotpotqa_validation'
    }
    
    logger.info(f"QA Comparison: Dynamic={dynamic_acc:.4f}, Static={static_acc:.4f}, Degradation={degradation_percent:.2f}%")
    
    return comparison

def main():
    """Main entry point for QA evaluation (for testing purposes)."""
    logging.basicConfig(level=logging.INFO)
    
    # This would normally be called with actual models and tokenizers
    # For now, it just demonstrates the structure
    logger.info("QA Evaluation Module Loaded Successfully")
    logger.info("To run evaluation, call run_qa_evaluation_comparison() with appropriate models.")

if __name__ == "__main__":
    main()