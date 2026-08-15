"""
Evaluation script for User Story 2: Comparative Performance Analysis.

Loads the unified dataset, splits into symbolic and physical test sets,
runs inference on both, calculates metrics, performs statistical tests,
and outputs comparative analysis results.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, brier_score_loss
from sklearn.preprocessing import LabelEncoder

# Project imports
from config import get_config, get_path, get_device
from utils.logger import get_logger, log_script_start, log_script_end, get_memory_usage_mb

# Setup logging
logger = get_logger(__name__)
CONFIG = get_config()

def load_model(model_path: str):
    """
    Load the trained DistilBERT proxy model.
    Returns a tuple of (model, tokenizer, device).
    """
    try:
        import torch
        from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
        
        device = get_device()
        logger.info(f"Loading model from {model_path} on device {device}")
        
        # Load tokenizer and model architecture
        tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
        model = DistilBertForSequenceClassification.from_pretrained(
            model_path, 
            num_labels=2  # binary classification: constraint_violated vs constraint_satisfied
        )
        model.to(device)
        model.eval()
        
        logger.info("Model loaded successfully")
        return model, tokenizer, device
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def load_unified_dataset(data_path: str) -> List[Dict[str, Any]]:
    """
    Load the unified dataset from JSONL file.
    """
    dataset = []
    path = Path(data_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Unified dataset not found at {data_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    record = json.loads(line)
                    dataset.append(record)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
    
    logger.info(f"Loaded {len(dataset)} records from {data_path}")
    return dataset

def check_physics_reward_exists(dataset: List[Dict[str, Any]]) -> bool:
    """
    Validate that 'physics_reward' field exists in the dataset.
    Aborts with clear error if missing (no proxy fallback).
    """
    if not dataset:
        logger.error("Dataset is empty, cannot check for physics_reward")
        return False
    
    first_record = dataset[0]
    if 'physics_reward' not in first_record:
        error_msg = (
            "CRITICAL: 'physics_reward' field is missing from the dataset. "
            "Cannot perform physical domain evaluation. Aborting as per SC-001. "
            "No proxy fallback allowed."
        )
        logger.error(error_msg)
        raise KeyError(error_msg)
    
    logger.info("Confirmed 'physics_reward' field exists in dataset")
    return True

def split_dataset_by_domain(
    dataset: List[Dict[str, Any]], 
    norm_threshold: float = 0.5,
    text_keywords: List[str] = ["Safety Constraint"]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split dataset into symbolic and physical test sets.
    
    Symbolic set: labeled based on norm > 0.5 AND text context check
    Physical set: labeled based on physics_reward > 0.5
    """
    symbolic_set = []
    physical_set = []
    
    for record in dataset:
        # Determine symbolic label
        actions = record.get('actions', [])
        text_desc = record.get('text_description', '')
        
        # Compute L2 norm of first 3 dimensions
        if len(actions) >= 3:
            first_3 = actions[:3]
            norm = np.linalg.norm(first_3)
        else:
            # Pad with zeros if insufficient dimensions
            padded = actions + [0.0] * (3 - len(actions))
            norm = np.linalg.norm(padded)
        
        # Check text keywords
        text_match = any(kw.lower() in text_desc.lower() for kw in text_keywords)
        
        # Apply composite rule for symbolic label
        symbolic_label = "constraint_violated" if (norm > norm_threshold and text_match) else "constraint_satisfied"
        
        # Determine physical label
        physics_reward = record.get('physics_reward')
        if physics_reward is None:
            logger.warning(f"Record missing physics_reward, skipping for physical set")
            continue
        
        physical_label = "high_reward" if physics_reward > 0.5 else "low_reward"
        
        # Add to respective sets with computed labels
        symbolic_record = record.copy()
        symbolic_record['symbolic_label'] = symbolic_label
        symbolic_set.append(symbolic_record)
        
        physical_record = record.copy()
        physical_record['physical_label'] = physical_label
        physical_set.append(physical_record)
    
    logger.info(f"Split dataset: {len(symbolic_set)} symbolic samples, {len(physical_set)} physical samples")
    return symbolic_set, physical_set

def run_inference(
    model, 
    tokenizer, 
    device, 
    dataset: List[Dict[str, Any]], 
    label_field: str
) -> List[Dict[str, Any]]:
    """
    Run inference on the dataset and attach predictions.
    """
    import torch
    from torch.utils.data import Dataset, DataLoader
    
    class InferenceDataset(Dataset):
        def __init__(self, records, tokenizer, label_field):
            self.records = records
            self.tokenizer = tokenizer
            self.label_field = label_field
        
        def __len__(self):
            return len(self.records)
        
        def __getitem__(self, idx):
            record = self.records[idx]
            # Use text_description as input text
            text = record.get('text_description', '')
            encoding = self.tokenizer(
                text,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=128
            )
            # Get true label
            true_label = record.get(self.label_field, 'constraint_satisfied')
            # Encode labels: 0 for satisfied/low, 1 for violated/high
            label_map = {'constraint_satisfied': 0, 'constraint_violated': 0, 'low_reward': 0, 'high_reward': 1}
            true_label_idx = 1 if true_label in ['constraint_violated', 'high_reward'] else 0
            
            return {
                'input_ids': encoding['input_ids'].squeeze(0),
                'attention_mask': encoding['attention_mask'].squeeze(0),
                'true_label': true_label_idx,
                'record': record
            }
    
    inference_dataset = InferenceDataset(dataset, tokenizer, label_field)
    # Use small batch size to stay within memory limits
    dataloader = DataLoader(inference_dataset, batch_size=8, shuffle=False)
    
    predictions = []
    probabilities = []
    
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            
            # Get probabilities
            probs = torch.softmax(outputs.logits, dim=1)
            pred_probs = probs[:, 1].cpu().numpy()  # Probability of positive class
            preds = (pred_probs > 0.5).astype(int)
            
            true_labels = batch['true_label'].numpy()
            
            for i in range(len(preds)):
                record = batch['record'][i]
                predictions.append({
                    'record': record,
                    'predicted_label': 1,
                    'probability': float(pred_probs[i]),
                    'true_label': int(true_labels[i])
                })
    
    return predictions

def calculate_metrics(predictions: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate Brier Score, Accuracy, F-score, and AUC-ROC.
    """
    if not predictions:
        return {
            'brier_score': 0.0,
            'accuracy': 0.0,
            'f1_score': 0.0,
            'auc_roc': 0.0
        }
    
    true_labels = [p['true_label'] for p in predictions]
    pred_probs = [p['probability'] for p in predictions]
    pred_labels = [1 if p > 0.5 else 0 for p in pred_probs]
    
    # Brier Score
    brier = brier_score_loss(true_labels, pred_probs)
    
    # Accuracy
    acc = accuracy_score(true_labels, pred_labels)
    
    # F1 Score
    f1 = f1_score(true_labels, pred_labels, zero_division=0)
    
    # AUC-ROC (requires at least one positive and one negative)
    try:
        if len(set(true_labels)) < 2:
            auc = 0.5  # Default if no variation
        else:
            auc = roc_auc_score(true_labels, pred_probs)
    except ValueError:
        auc = 0.5
    
    return {
        'brier_score': float(brier),
        'accuracy': float(acc),
        'f1_score': float(f1),
        'auc_roc': float(auc)
    }

def perform_statistical_test(symbolic_metrics: List[float], physical_metrics: List[float]) -> Dict[str, Any]:
    """
    Execute statistical test on the difference in metrics.
    Shapiro-Wilk for normality -> t-test if normal, else Wilcoxon signed-rank.
    """
    if len(symbolic_metrics) == 0 or len(physical_metrics) == 0:
        return {
            'test_name': 'none',
            'p_value': 1.0,
            'is_significant': False,
            'reason': 'Insufficient data for statistical test'
        }
    
    # Check for normality using Shapiro-Wilk
    # Note: We test the difference between paired samples
    if len(symbolic_metrics) != len(physical_metrics):
        # Unpaired test
        if len(symbolic_metrics) >= 8 and len(physical_metrics) >= 8:
            stat, p_value = stats.shapiro(symbolic_metrics[:10])  # Shapiro requires n <= 5000
            if p_value > 0.05:
                # Normal distribution, use t-test
                stat, p_value = stats.ttest_ind(symbolic_metrics, physical_metrics)
                test_name = 't-test'
            else:
                # Non-normal, use Mann-Whitney U
                stat, p_value = stats.mannwhitneyu(symbolic_metrics, physical_metrics)
                test_name = 'mann-whitney-u'
        else:
            # Small sample, use Mann-Whitney U
            stat, p_value = stats.mannwhitneyu(symbolic_metrics, physical_metrics)
            test_name = 'mann-whitney-u'
    else:
        # Paired test
        differences = [s - p for s, p in zip(symbolic_metrics, physical_metrics)]
        if len(differences) >= 3:
            stat, p_value = stats.shapiro(differences[:10])  # Limit for Shapiro
            if p_value > 0.05:
                # Normal distribution, use paired t-test
                stat, p_value = stats.ttest_rel(symbolic_metrics, physical_metrics)
                test_name = 'paired-t-test'
            else:
                # Non-normal, use Wilcoxon signed-rank
                stat, p_value = stats.wilcoxon(symbolic_metrics, physical_metrics)
                test_name = 'wilcoxon-signed-rank'
        else:
            # Too few samples
            return {
                'test_name': 'none',
                'p_value': 1.0,
                'is_significant': False,
                'reason': 'Insufficient samples for statistical test'
            }
    
    is_significant = p_value < 0.05
    
    return {
        'test_name': test_name,
        'p_value': float(p_value),
        'is_significant': bool(is_significant)
    }

def save_results(
    results: Dict[str, Any], 
    output_path: str,
    raw_predictions: List[Dict[str, Any]],
    raw_predictions_path: str
):
    """
    Save comparative analysis results and raw predictions.
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(raw_predictions_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save comparative analysis
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved comparative analysis to {output_path}")
    
    # Save raw predictions (simplified for JSON serialization)
    serializable_predictions = []
    for pred in raw_predictions:
        record = pred['record']
        # Remove large tensors or non-serializable objects
        serializable_record = {k: v for k, v in record.items() if not isinstance(v, (bytes, bytearray))}
        serializable_predictions.append({
            'predicted_label': pred['predicted_label'],
            'probability': pred['probability'],
            'true_label': pred['true_label'],
            'record': serializable_record
        })
    
    with open(raw_predictions_path, 'w', encoding='utf-8') as f:
        for pred in serializable_predictions:
            f.write(json.dumps(pred) + '\n')
    logger.info(f"Saved raw predictions to {raw_predictions_path}")

def main():
    """
    Main execution function for T017.
    """
    log_script_start(__file__)
    logger.info("Starting Comparative Performance Analysis (T017)")
    
    try:
        # Configuration
        model_path = get_path("models", "proxy_hard", "model.pt")
        unified_dataset_path = get_path("data", "processed", "unified_dataset.jsonl")
        output_dir = get_path("data", "results")
        comparative_output = os.path.join(output_dir, "comparative_analysis.json")
        raw_predictions_output = os.path.join(output_dir, "raw_predictions.jsonl")
        
        # Load schema for threshold/keywords
        schema_path = get_path("data", "schema", "action_schema.json")
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        norm_threshold = schema.get('norm_threshold', 0.5)
        text_keywords = schema.get('text_keywords', ["Safety Constraint"])
        
        # Step 1: Load unified dataset
        logger.info("Loading unified dataset...")
        dataset = load_unified_dataset(unified_dataset_path)
        if not dataset:
            raise ValueError("Dataset is empty after loading")
        
        # Step 2: Validate physics_reward exists
        logger.info("Validating physics_reward field...")
        check_physics_reward_exists(dataset)
        
        # Step 3: Split dataset by domain
        logger.info("Splitting dataset into symbolic and physical domains...")
        symbolic_set, physical_set = split_dataset_by_domain(
            dataset, 
            norm_threshold=norm_threshold,
            text_keywords=text_keywords
        )
        
        if not symbolic_set or not physical_set:
            raise ValueError("One or both domains are empty after splitting")
        
        # Step 4: Load model
        logger.info("Loading trained proxy model...")
        model, tokenizer, device = load_model(model_path)
        
        # Step 5: Run inference on symbolic set
        logger.info("Running inference on symbolic test set...")
        symbolic_predictions = run_inference(
            model, tokenizer, device, symbolic_set, 'symbolic_label'
        )
        
        # Step 6: Run inference on physical set
        logger.info("Running inference on physical test set...")
        physical_predictions = run_inference(
            model, tokenizer, device, physical_set, 'physical_label'
        )
        
        # Step 7: Calculate metrics for each domain
        logger.info("Calculating metrics for symbolic domain...")
        symbolic_metrics = calculate_metrics(symbolic_predictions)
        
        logger.info("Calculating metrics for physical domain...")
        physical_metrics = calculate_metrics(physical_predictions)
        
        # Step 8: Perform statistical test
        logger.info("Performing statistical significance test...")
        # Use accuracy values for statistical test (could use any metric)
        stat_test_result = perform_statistical_test(
            [symbolic_metrics['accuracy']],
            [physical_metrics['accuracy']]
        )
        
        # Step 9: Compile results
        results = {
            'symbolic_domain': {
                'sample_size': len(symbolic_set),
                'metrics': symbolic_metrics
            },
            'physical_domain': {
                'sample_size': len(physical_set),
                'metrics': physical_metrics
            },
            'statistical_test': {
                **stat_test_result,
                'physics_baseline_source': 'bridge-to-worlds/bridge-data'
            }
        }
        
        # Step 10: Save results
        logger.info("Saving results...")
        save_results(
            results, 
            comparative_output,
            symbolic_predictions + physical_predictions,
            raw_predictions_output
        )
        
        logger.info("Comparative analysis completed successfully")
        log_script_end(__file__)
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        log_script_end(__file__, success=False)
        raise

if __name__ == "__main__":
    main()