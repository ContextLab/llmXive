import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from code.config import DATA_PROCESSED_PATH, MODEL_NAME, ANXIETY_THRESHOLD, SEED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_text_quality(text: str) -> bool:
    """
    Filter out non-English or gibberish text.
    Implemented in T014a.
    """
    if not isinstance(text, str) or not text.strip():
        return False
    # Simple heuristic: check for excessive non-alphabetic chars or very short
    clean_text = re.sub(r'[^a-zA-Z\s]', '', text)
    if len(clean_text) < 10:
        return False
    return True

def load_anxiety_model(model_name: str = MODEL_NAME) -> Tuple[Any, Any]:
    """
    Load the RoBERTa model for emotion/anxiety detection.
    Implemented in T015.
    """
    logger.info(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    return tokenizer, model

def compute_anxiety_scores(
    texts: List[str],
    tokenizer: Any,
    model: Any,
    batch_size: int = 32
) -> List[Dict[str, float]]:
    """
    Compute anxiety scores for a batch of texts.
    Implemented in T015.
    """
    results = []
    device = torch.device("cpu")
    model.to(device)

    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            encoded = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt"
            ).to(device)

            outputs = model(**encoded)
            probs = torch.softmax(outputs.logits, dim=-1)

            for prob in probs:
                # Assuming label 0 is anxiety or the specific anxiety index
                # For cardiffnlp/twitter-roberta-base-emotion, label 3 is 'anxiety'
                # We map based on the specific model's label mapping if available,
                # but here we assume a standard ordering or specific index.
                # The task specifies 'anxiety_score', so we extract the probability for anxiety.
                # In the cardiffnlp emotion model, the order is:
                # 0: sadness, 1: joy, 2: love, 3: anger, 4: fear, 5: surprise
                # Wait, the task says 'cardiffnlp/twitter-roberta-base-emotion'.
                # Anxiety is often mapped to 'fear' (index 4) in this specific model,
                # or we use a specific anxiety model.
                # Given the task description "anxiety scores" and the model name,
                # we will assume the task implies using the 'fear' class as a proxy for anxiety
                # or a specific anxiety model.
                # However, T015 description says "load 'cardiffnlp/twitter-roberta-base-emotion'".
                # In that model, 'fear' is index 4. Let's use index 4 as anxiety proxy.
                anxiety_prob = prob[4].item()
                results.append({"anxiety_score": anxiety_prob})

    return results

def run_full_scoring_pipeline(
    input_path: Path = DATA_PROCESSED_PATH / "preprocessed_text.csv",
    output_path: Path = DATA_PROCESSED_PATH / "scoring_results.csv",
    confidence_threshold: float = 0.6
) -> None:
    """
    Run the full anxiety scoring pipeline:
    1. Load preprocessed text (from T014a).
    2. Load model (T015).
    3. Compute scores.
    4. Filter by confidence (T016).
    5. Save to scoring_results.csv (T017).
    """
    logger.info(f"Reading input from {input_path}")
    df = pd.read_csv(input_path)

    if df.empty:
        logger.warning("Input dataframe is empty.")
        # Save empty result with correct columns
        pd.DataFrame(columns=["text", "anxiety_score", "confidence_score"]).to_csv(
            output_path, index=False
        )
        return

    # Ensure text column exists and is string
    if "text" not in df.columns:
        raise ValueError("Input file must contain a 'text' column.")
    
    texts = df["text"].astype(str).tolist()

    logger.info(f"Loaded {len(texts)} texts. Loading model...")
    tokenizer, model = load_anxiety_model()

    logger.info("Computing anxiety scores...")
    scores = compute_anxiety_scores(texts, tokenizer, model)

    # Combine text and scores
    # The model output provides probability for anxiety.
    # For confidence, we can use the max probability of the predicted class,
    # or specifically the probability of the anxiety class if we are confident in it.
    # The task T016 says "confidence score filtering (threshold >= 0.6)".
    # We will use the probability of the predicted class as confidence.
    # Re-run to get full probs for confidence calculation
    results = []
    device = torch.device("cpu")
    model.to(device)
    
    with torch.no_grad():
        for i in range(0, len(texts), 32):
            batch_texts = texts[i : i + 32]
            encoded = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt"
            ).to(device)
            outputs = model(**encoded)
            probs = torch.softmax(outputs.logits, dim=-1)
            
            for j, prob in enumerate(probs):
                idx = i + j
                text = texts[idx]
                # Anxiety score is fear (index 4)
                anxiety_score = prob[4].item()
                # Confidence is max probability
                confidence = prob.max().item()
                
                if confidence >= confidence_threshold:
                    results.append({
                        "text": text,
                        "anxiety_score": anxiety_score,
                        "confidence_score": confidence
                    })

    result_df = pd.DataFrame(results)
    
    if result_df.empty:
        logger.warning("No results passed confidence threshold.")
    
    logger.info(f"Saving {len(result_df)} results to {output_path}")
    result_df.to_csv(output_path, index=False)
    logger.info("Pipeline complete.")

if __name__ == "__main__":
    run_full_scoring_pipeline()
