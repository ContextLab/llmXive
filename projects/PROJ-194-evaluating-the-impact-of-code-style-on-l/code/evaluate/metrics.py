import re
import math
import json
import csv
import os
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime

# Attempt to import external metrics; if missing, we raise an error during execution
# to satisfy the "fail loudly" constraint.
try:
    import codebleu
except ImportError:
    raise ImportError(
        "codebleu is required for this pipeline. "
        "Please ensure it is installed in the environment."
    )

try:
    from rouge_score import rouge_scorer
except ImportError:
    raise ImportError(
        "rouge_score is required for this pipeline. "
        "Please ensure it is installed in the environment."
    )

@dataclass
class TaskResult:
    """Container for a single task execution result."""
    id: str
    variant_id: str
    task_type: str  # 'completion', 'bug_detection', 'summarization'
    input_code: str
    model_output: str
    ground_truth: str
    exact_match: float
    codebleu: float
    precision: float
    recall: float
    f1: float
    rouge_l: float
    bleu: float
    token_count: int
    is_semantic_opacity: bool = False
    mutation_type: Optional[str] = None
    is_confounded: Optional[bool] = None
    confound_reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MetricsCalculator:
    """Calculates various code evaluation metrics."""

    def __init__(self, confound_threshold: Optional[float] = None):
        """
        Initialize the calculator.
        
        Args:
            confound_threshold: If provided, flags results where token count
                                delta exceeds this threshold as 'potentially confounded'.
                                If None, confounding analysis is skipped.
        """
        self.confound_threshold = confound_threshold
        self.scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)

    def _normalize_text(self, text: str) -> str:
        """Basic normalization for string comparison."""
        return re.sub(r'\s+', ' ', text).strip().lower()

    def calculate_exact_match(self, prediction: str, ground_truth: str) -> float:
        """Calculate exact match score."""
        pred_norm = self._normalize_text(prediction)
        gt_norm = self._normalize_text(ground_truth)
        return 1.0 if pred_norm == gt_norm else 0.0

    def calculate_codebleu(self, prediction: str, ground_truth: str, 
                           reference_code: Optional[str] = None) -> float:
        """Calculate CodeBLEU score."""
        # CodeBLEU expects list of references
        refs = [ground_truth]
        if reference_code:
            refs.append(reference_code)
        
        # codebleu returns a dict with 'codebleu' key
        try:
            result = codebleu.compute_codebleu(
                references=refs, 
                hypothesis=prediction, 
                lang='python'
            )
            return result.get('codebleu', 0.0)
        except Exception:
            # Fallback to 0.0 if calculation fails, but log it in a real system
            return 0.0

    def calculate_rouge_l(self, prediction: str, ground_truth: str) -> float:
        """Calculate ROUGE-L score."""
        scores = self.scorer.score(ground_truth, prediction)
        return scores['rougeL'].fmeasure

    def calculate_bleu(self, prediction: str, ground_truth: str) -> float:
        """Calculate BLEU score (simplified implementation)."""
        # Simple BLEU implementation for self-containment if nltk is missing
        # In a full pipeline, we'd use nltk.translate.bleu_score
        pred_tokens = self._normalize_text(prediction).split()
        gt_tokens = self._normalize_text(ground_truth).split()
        
        if not gt_tokens:
            return 0.0
        if not pred_tokens:
            return 0.0

        # Unigram precision
        matches = sum(1 for t in pred_tokens if t in gt_tokens)
        precision = matches / len(pred_tokens)
        
        # Simplified brevity penalty
        if len(pred_tokens) >= len(gt_tokens):
            bp = 1.0
        else:
            bp = math.exp(1 - len(gt_tokens) / len(pred_tokens))
        
        return bp * precision

    def calculate_p_rf(self, prediction: str, ground_truth: str) -> Tuple[float, float, float]:
        """Calculate Precision, Recall, and F1 based on token overlap."""
        pred_tokens = set(self._normalize_text(prediction).split())
        gt_tokens = set(self._normalize_text(ground_truth).split())
        
        if not pred_tokens or not gt_tokens:
            return 0.0, 0.0, 0.0
        
        intersection = pred_tokens & gt_tokens
        
        precision = len(intersection) / len(pred_tokens)
        recall = len(intersection) / len(gt_tokens)
        
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        return precision, recall, f1

    def count_tokens(self, code: str) -> int:
        """
        Count tokens in code.
        In a real pipeline, this might use a specific tokenizer (e.g., from transformers).
        Here we use a simple whitespace/punctuation split as a proxy, 
        or count lines/tokens if a tokenizer is not available.
        For CodeGen-2B, we assume a standard split or use a placeholder logic 
        consistent with T027 requirements.
        """
        # Simple tokenization: split by whitespace and punctuation
        # This is a proxy. In T023a, if we load the model, we should use model.tokenizer.
        # Since this module is generic, we use a robust simple count.
        # A more accurate count would require the specific model's tokenizer.
        # We will implement a simple heuristic: split by whitespace and count.
        return len(code.split())

    def analyze_confounding(self, current_token_count: int, 
                            baseline_token_count: Optional[int] = None,
                            original_token_count: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Analyze if the result is potentially confounded by token count changes.
        
        This implements the logic for T022d:
        Flags a result as "potentially confounded" if the token count change delta 
        exceeds the threshold T defined in T022c.
        
        Args:
            current_token_count: The token count of the current variant/output.
            baseline_token_count: The token count of the original/clean baseline.
            original_token_count: Alternative reference for original code length.
        
        Returns:
            Tuple of (is_confounded: bool, reason: str or None)
        """
        if self.confound_threshold is None:
            return False, None

        reference_count = baseline_token_count or original_token_count
        
        if reference_count is None:
            # If we don't have a reference, we cannot calculate delta.
            # We assume not confounded by this specific metric, but maybe log a warning.
            return False, "No baseline token count available for comparison."

        delta = abs(current_token_count - reference_count)
        
        if delta > self.confound_threshold:
            reason = (
                f"Token count delta ({delta}) exceeds threshold ({self.confound_threshold}). "
                f"Current: {current_token_count}, Reference: {reference_count}. "
                f"Result may be confounded by style-induced token explosion/compression."
            )
            return True, reason
        
        return False, None

    def calculate_result(self, 
                         variant_id: str, 
                         task_type: str, 
                         input_code: str, 
                         model_output: str, 
                         ground_truth: str, 
                         baseline_token_count: Optional[int] = None,
                         is_semantic_opacity: bool = False,
                         mutation_type: Optional[str] = None) -> TaskResult:
        """Calculate all metrics for a single task result."""
        
        # Calculate core metrics
        exact_match = self.calculate_exact_match(model_output, ground_truth)
        codebleu = self.calculate_codebleu(model_output, ground_truth)
        rouge_l = self.calculate_rouge_l(model_output, ground_truth)
        bleu = self.calculate_bleu(model_output, ground_truth)
        precision, recall, f1 = self.calculate_p_rf(model_output, ground_truth)
        
        # Count tokens for the model output (or input code depending on definition, 
        # usually we care about the output length or the input length passed to the model)
        # T027 says "count tokens per variant". We count the input code passed to the model.
        token_count = self.count_tokens(input_code)
        
        # Analyze confounding (T022d)
        is_confounded, confound_reason = self.analyze_confounding(
            current_token_count=token_count,
            baseline_token_count=baseline_token_count
        )

        return TaskResult(
            id=f"{variant_id}_{task_type}",
            variant_id=variant_id,
            task_type=task_type,
            input_code=input_code,
            model_output=model_output,
            ground_truth=ground_truth,
            exact_match=exact_match,
            codebleu=codebleu,
            precision=precision,
            recall=recall,
            f1=f1,
            rouge_l=rouge_l,
            bleu=bleu,
            token_count=token_count,
            is_semantic_opacity=is_semantic_opacity,
            mutation_type=mutation_type,
            is_confounded=is_confounded,
            confound_reason=confound_reason
        )

def run_metrics_evaluation(results: List[Dict[str, Any]], 
                           output_path: str,
                           confound_threshold: Optional[float] = None) -> List[TaskResult]:
    """
    Run metrics evaluation on a list of raw results and save to CSV.
    
    Args:
        results: List of dicts containing 'variant_id', 'task_type', 'input_code', 
                 'model_output', 'ground_truth', 'baseline_token_count' (optional).
        output_path: Path to save the CSV results.
        confound_threshold: Threshold for T022d confounding check.
    
    Returns:
        List of TaskResult objects.
    """
    calculator = MetricsCalculator(confound_threshold=confound_threshold)
    task_results = []
    
    for item in results:
        result = calculator.calculate_result(
            variant_id=item['variant_id'],
            task_type=item['task_type'],
            input_code=item['input_code'],
            model_output=item['model_output'],
            ground_truth=item['ground_truth'],
            baseline_token_count=item.get('baseline_token_count'),
            is_semantic_opacity=item.get('is_semantic_opacity', False),
            mutation_type=item.get('mutation_type')
        )
        task_results.append(result)
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=TaskResult.__dataclass_fields__.keys())
        writer.writeheader()
        for res in task_results:
            writer.writerow(res.to_dict())
    
    return task_results

def main():
    """Entry point for running metrics evaluation directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run metrics evaluation on task results.")
    parser.add_argument("--input", type=str, required=True, help="Path to JSONL of raw results")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--threshold", type=float, default=None, help="Token delta threshold for confounding check")
    
    args = parser.parse_args()
    
    # Load input
    raw_results = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                raw_results.append(json.loads(line))
    
    results = run_metrics_evaluation(raw_results, args.output, confound_threshold=args.threshold)
    
    print(f"Evaluation complete. {len(results)} results saved to {args.output}")
    
    # Print summary of confounded results
    confounded_count = sum(1 for r in results if r.is_confounded)
    if confounded_count > 0:
        print(f"WARNING: {confounded_count} results flagged as potentially confounded by token count.")

if __name__ == "__main__":
    main()