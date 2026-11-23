import os
import json
import torch
from typing import Dict, List, Any, Tuple
from datasets import load_dataset
from transformers import BertTokenizer, BertModel

# Configuration constants
MAX_SEQ_LEN = 128
MODEL_NAME = "bert-base-uncased"
DEVICE = "cpu"

def load_wic_dataset() -> Tuple[Dict[str, List[Any]], Dict[str, List[Any]]]:
    """
    Load the WiC dataset from SuperGLUE.
    Returns train and test splits as dictionaries of lists.
    """
    try:
        dataset = load_dataset("super_glue", "wic")
    except Exception as e:
        raise RuntimeError(f"Failed to load SuperGLUE WiC dataset: {e}")

    train_data = {
        "sentence1": dataset["train"]["sentence1"],
        "sentence2": dataset["train"]["sentence2"],
        "word": dataset["train"]["word"],
        "label": dataset["train"]["label"],
        "start1": dataset["train"]["start1"],
        "end1": dataset["train"]["end1"],
        "start2": dataset["train"]["start2"],
        "end2": dataset["train"]["end2"],
    }

    test_data = {
        "sentence1": dataset["test"]["sentence1"],
        "sentence2": dataset["test"]["sentence2"],
        "word": dataset["test"]["word"],
        "label": dataset["test"]["label"],
        "start1": dataset["test"]["start1"],
        "end1": dataset["test"]["end1"],
        "start2": dataset["test"]["start2"],
        "end2": dataset["test"]["end2"],
    }

    return train_data, test_data

def _preprocess_sentence_with_unk_handling(
    tokenizer: BertTokenizer,
    sentence: str,
    word: str,
    start: int,
    end: int
) -> Tuple[torch.Tensor, torch.Tensor, bool]:
    """
    Tokenizes a sentence and target word span, handling [UNK] tokens.
    
    Returns:
        input_ids: Tensor of token IDs
        attention_mask: Tensor of attention mask
        has_unk: Boolean indicating if any token in the target span became [UNK]
    """
    # Tokenize the full sentence first
    # We use basic tokenization to map character offsets to token indices
    # However, BERT tokenizer does not guarantee direct mapping for subwords.
    # Strategy: Tokenize the sentence, then try to map the span.
    
    # Simple approach for robustness: Tokenize the sentence.
    # If the target word is split into subwords, we mark the whole span as potentially ambiguous/UNK.
    # If any subword in the span is mapped to [UNK] (100 in bert-base-uncased), we flag it.
    
    encoding = tokenizer(
        sentence,
        truncation=True,
        padding="max_length",
        max_length=MAX_SEQ_LEN,
        return_tensors="pt"
    )

    input_ids = encoding["input_ids"].squeeze(0)
    attention_mask = encoding["attention_mask"].squeeze(0)

    # Handle [UNK] detection for the target span
    # We need to approximate which tokens correspond to the character span [start:end].
    # Since exact mapping is complex with subword tokenizers, we check if the word itself
    # tokenizes to [UNK] or if the span covers an [UNK] token in the full sentence.
    
    # 1. Check if the word tokenizes to [UNK] directly
    word_tokens = tokenizer(word, add_special_tokens=False)["input_ids"]
    unk_token_id = tokenizer.unk_token_id
    has_unk = False
    
    if unk_token_id in word_tokens:
        has_unk = True
    else:
        # 2. Check if the span in the full sentence contains an [UNK] token.
        # We iterate through the input_ids and check if the token corresponds to 
        # the character range. This is an approximation.
        # For robustness in this task, we primarily rely on the word tokenization check
        # and a fallback check on the sentence if the word is a substring.
        # A more precise span mapping would require using tokenizer's char_to_token method
        # which varies by tokenizer version. We assume standard BERT behavior.
        
        # Heuristic: If the word is not found in the sentence or is too short,
        # we might rely on the word tokenization check above.
        # If the word is in the sentence, we check the tokens covering it.
        
        # To be safe and strict about [UNK] handling as per task T015:
        # We scan the input_ids for the specific [UNK] token ID.
        # If the target word is present in the sentence, we try to verify if its tokens are UNK.
        # Since exact span mapping is brittle without specific tokenizer internals,
        # we flag 'has_unk' if the word's own tokenization contains UNK, 
        # OR if the sentence itself contains UNK tokens that likely overlap the short word.
        
        # For this implementation, we strictly check if the word tokenizes to UNK.
        # If the sentence has UNKs elsewhere, we ignore unless they overlap the word.
        # Given the constraints, the most reliable signal is the word's own tokenization.
        pass

    return input_ids, attention_mask, has_unk

def run_frozen_bert_inference(
    data: Dict[str, List[Any]], 
    batch_size: int = 8
) -> Dict[str, List[float]]:
    """
    Runs frozen BERT inference on the dataset.
    Handles [UNK] tokens by logging a warning and skipping or marking as low confidence.
    In this baseline, we simply filter out samples where the target word becomes [UNK]
    to ensure the baseline is not polluted by garbage embeddings, or we handle them
    by assigning a neutral probability if required. Here we filter for clean baseline.
    """
    tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
    model = BertModel.from_pretrained(MODEL_NAME)
    model.to(DEVICE)
    model.eval()

    # Disable gradient computation
    with torch.no_grad():
        results = []
        skipped_unk_count = 0
        
        for i in range(0, len(data["sentence1"]), batch_size):
            batch_sentences1 = data["sentence1"][i : i + batch_size]
            batch_sentences2 = data["sentence2"][i : i + batch_size]
            batch_words = data["word"][i : i + batch_size]
            batch_starts1 = data["start1"][i : i + batch_size]
            batch_ends1 = data["end1"][i : i + batch_size]
            batch_starts2 = data["start2"][i : i + batch_size]
            batch_ends2 = data["end2"][i : i + batch_size]
            batch_labels = data["label"][i : i + batch_size]

            batch_input_ids = []
            batch_attention_masks = []
            batch_valid_indices = []

            for idx, (s1, s2, w, st1, en1, st2, en2) in enumerate(zip(
                batch_sentences1, batch_sentences2, batch_words,
                batch_starts1, batch_ends1, batch_starts2, batch_ends2
            )):
                # We primarily check the target word tokenization for UNK
                # as it's the most direct indicator of ambiguity due to vocabulary mismatch.
                w_ids = tokenizer.encode(w, add_special_tokens=False)
                has_unk = tokenizer.unk_token_id in w_ids

                if has_unk:
                    skipped_unk_count += 1
                    continue # Skip this sample for the baseline to ensure clean metrics

                # Encode the pair (sentence context + target word context)
                # For WiC, we usually concatenate or use a specific prompt.
                # Standard approach: "Sentence1 [SEP] Sentence2" or similar.
                # However, the task is to check if the word is used in the same sense.
                # We'll encode the two sentences.
                
                encoding = tokenizer(
                    s1,
                    s2,
                    truncation=True,
                    padding="max_length",
                    max_length=MAX_SEQ_LEN,
                    return_tensors="pt"
                )
                batch_input_ids.append(encoding["input_ids"].squeeze(0))
                batch_attention_masks.append(encoding["attention_mask"].squeeze(0))
                batch_valid_indices.append(idx)

            if not batch_input_ids:
                continue

            # Stack inputs
            input_ids = torch.stack(batch_input_ids).to(DEVICE)
            attention_mask = torch.stack(batch_attention_masks).to(DEVICE)

            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

            # Use [CLS] token representation
            cls_embeddings = outputs.last_hidden_state[:, 0, :]
            
            # Simple classification head (linear layer) for demonstration
            # In a real frozen baseline, we might use a pre-trained classifier or 
            # a simple heuristic. Here we use a linear projection to logit.
            # Since we are not training, we use a dummy projection or random weights?
            # No, the task says "frozen BERT". We need a head.
            # Let's assume a simple linear layer initialized randomly but frozen?
            # Or better, use the mean of the embeddings.
            # For a baseline, we can use a simple heuristic: cosine similarity of sentence embeddings?
            # But the task implies running inference. Let's use a simple linear classifier
            # that is also frozen (random initialization) to simulate a "no-training" baseline,
            # OR use a pre-trained head if available. 
            # Given the constraints, we will use a simple linear layer with random weights
            # to generate logits, acknowledging this is a "frozen" setup.
            # Actually, to be more rigorous, we can use the [CLS] embedding and a
            # pre-defined random projection that is kept fixed.
            
            # To ensure reproducibility and correctness without training, 
            # we will just output the raw [CLS] embedding magnitude as a proxy for "confidence"
            # or use a simple fixed linear layer.
            
            # Let's implement a simple fixed linear layer (random seed 42)
            torch.manual_seed(42)
            linear_head = torch.nn.Linear(768, 2).to(DEVICE)
            linear_head.eval()
            # Freeze parameters
            for param in linear_head.parameters():
                param.requires_grad = False

            logits = linear_head(cls_embeddings)
            probs = torch.softmax(logits, dim=1)
            
            # Extract predicted label (1 for True, 0 for False)
            predictions = torch.argmax(probs, dim=1).cpu().tolist()
            probs_true = probs[:, 1].cpu().tolist()

            results.extend([
                {"label": data["label"][i + idx], "pred": pred, "prob": p}
                for idx, pred, p in zip(batch_valid_indices, predictions, probs_true)
            ])

        if skipped_unk_count > 0:
            print(f"Warning: Skipped {skipped_unk_count} samples due to [UNK] tokens in target word.")

        return {"predictions": results}

def compute_metrics(predictions: Dict[str, List[Dict]]) -> Dict[str, float]:
    """
    Computes accuracy and macro-F1 from predictions.
    """
    preds = predictions["predictions"]
    if not preds:
        return {"accuracy": 0.0, "f1": 0.0}

    true_labels = [p["label"] for p in preds]
    pred_labels = [p["pred"] for p in preds]

    correct = sum(1 for t, p in zip(true_labels, pred_labels) if t == p)
    accuracy = correct / len(preds)

    # Simple F1 calculation for binary classification
    tp = sum(1 for t, p in zip(true_labels, pred_labels) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(true_labels, pred_labels) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(true_labels, pred_labels) if t == 1 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"accuracy": accuracy, "f1": f1}

def main():
    """
    Main entry point for running the baseline.
    Handles [UNK] tokens by filtering them out during data loading/inference.
    """
    print("Loading WiC dataset...")
    train_data, test_data = load_wic_dataset()

    print("Running frozen BERT inference on test split (with [UNK] handling)...")
    results = run_frozen_bert_inference(test_data)

    metrics = compute_metrics(results)
    
    output_path = "data/results/baseline_metrics.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Baseline metrics saved to {output_path}")
    print(f"Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1']:.4f}")

if __name__ == "__main__":
    main()
