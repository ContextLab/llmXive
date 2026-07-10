"""
Metrics calculation module for LLM code evaluation.

Implements calculation for:
- Exact Match
- CodeBLEU
- Precision, Recall, F1 (token-based)
- ROUGE-L
- BLEU
"""
import re
import math
import json
import csv
import os
from typing import List, Dict, Any, Optional, Tuple, Union
from collections import Counter

# Try to import optional heavy libraries, fallback to pure python if missing
try:
    from codebleu import calc_codebleu
    HAS_CODEBLEU = True
except ImportError:
    HAS_CODEBLEU = False

try:
    from rouge_score import rouge_scorer
    HAS_ROUGE = True
except ImportError:
    HAS_ROUGE = False

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    import nltk
    # Ensure punkt is available if using nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

class MetricsCalculator:
    """Calculates various metrics between reference and generated code."""

    def __init__(self):
        self.smoothing_function = SmoothingFunction() if HAS_NLTK else None

    def _tokenize_code(self, code: str) -> List[str]:
        """Basic tokenization for code metrics."""
        # Replace common operators and delimiters with spaces to separate them
        # This is a simplified tokenizer suitable for general code comparison
        # In a production setting, a proper AST-based tokenizer would be preferred
        # but we stick to regex for portability if nltk is unavailable.
        if HAS_NLTK:
            # Use NLTK word tokenizer if available
            return nltk.word_tokenize(code)
        else:
            # Fallback regex tokenizer
            # Split on whitespace and keep operators as separate tokens
            tokens = re.findall(r'\w+|[^\s\w]', code)
            return tokens

    def calculate_exact_match(self, reference: str, candidate: str) -> float:
        """Calculate Exact Match (normalized string equality)."""
        ref_norm = re.sub(r'\s+', ' ', reference.strip())
        cand_norm = re.sub(r'\s+', ' ', candidate.strip())
        return 1.0 if ref_norm == cand_norm else 0.0

    def calculate_bleu(self, reference: str, candidate: str) -> float:
        """Calculate BLEU score."""
        if not HAS_NLTK:
            # Fallback: 0.0 if NLTK not available
            return 0.0

        ref_tokens = self._tokenize_code(reference)
        cand_tokens = self._tokenize_code(candidate)

        if not cand_tokens:
            return 0.0

        # Calculate BLEU-4
        try:
            score = sentence_bleu(
                [ref_tokens], 
                cand_tokens, 
                smoothing_function=self.smoothing_function.method1
            )
            return score
        except Exception:
            return 0.0

    def calculate_rouge_l(self, reference: str, candidate: str) -> float:
        """Calculate ROUGE-L F1 score."""
        if not HAS_ROUGE:
            # Fallback: 0.0 if rouge_score not available
            return 0.0

        try:
            scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=False)
            scores = scorer.score(reference, candidate)
            return scores['rougeL'].fmeasure
        except Exception:
            return 0.0

    def _calculate_precision_recall_f1(self, reference: str, candidate: str) -> Tuple[float, float, float]:
        """Calculate Precision, Recall, and F1 based on token overlap."""
        ref_tokens = set(self._tokenize_code(reference))
        cand_tokens = set(self._tokenize_code(candidate))

        if not cand_tokens:
            return 0.0, 0.0, 0.0
        if not ref_tokens:
            return 0.0, 0.0, 0.0

        intersection = ref_tokens & cand_tokens
        
        precision = len(intersection) / len(cand_tokens)
        recall = len(intersection) / len(ref_tokens)
        
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        return precision, recall, f1

    def calculate_codebleu(self, reference: str, candidate: str, lang: str = 'python') -> float:
        """Calculate CodeBLEU score."""
        if not HAS_CODEBLEU:
            # Fallback: 0.0 if codebleu not available
            return 0.0

        try:
            # codebleu expects a list of references and a candidate string
            # It returns a dict with 'codebleu' key
            result = calc_codebleu([reference], candidate, lang=lang)
            return result['codebleu']
        except Exception:
            return 0.0

    def calculate_all_metrics(self, reference: str, candidate: str) -> Dict[str, float]:
        """Calculate all metrics and return as a dictionary."""
        metrics = {
            'exact_match': self.calculate_exact_match(reference, candidate),
            'bleu': self.calculate_bleu(reference, candidate),
            'rouge_l': self.calculate_rouge_l(reference, candidate),
            'codebleu': self.calculate_codebleu(reference, candidate)
        }
        
        p, r, f1 = self._calculate_precision_recall_f1(reference, candidate)
        metrics['precision'] = p
        metrics['recall'] = r
        metrics['f1'] = f1
        
        return metrics

def run_metrics_evaluation(
    input_path: str, 
    output_path: str, 
    reference_column: str = 'reference_code', 
    candidate_column: str = 'generated_code'
) -> None:
    """
    Run metrics evaluation on a dataset file and save results.
    
    Args:
        input_path: Path to input CSV/JSON containing reference and candidate code.
        output_path: Path to save the results CSV.
        reference_column: Name of the column containing reference code.
        candidate_column: Name of the column containing generated code.
    """
    calculator = MetricsCalculator()
    results = []
    
    # Determine file type and load data
    if input_path.endswith('.json'):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            rows = data
        else:
            # Assume it's a dict with a list inside
            rows = data.get('data', [])
    elif input_path.endswith('.csv'):
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    else:
        raise ValueError(f"Unsupported input file format: {input_path}")
    
    for i, row in enumerate(rows):
        ref = row.get(reference_column, "")
        cand = row.get(candidate_column, "")
        
        if not isinstance(ref, str):
            ref = str(ref)
        if not isinstance(cand, str):
            cand = str(cand)
        
        metrics = calculator.calculate_all_metrics(ref, cand)
        
        result_row = {
            'row_id': i,
            **metrics
        }
        
        # Preserve original row data for context
        for key, value in row.items():
            if key not in result_row:
                result_row[key] = value
                
        results.append(result_row)
    
    # Save results
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    fieldnames = list(results[0].keys()) if results else []
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Metrics evaluation complete. Results saved to {output_path}")

def main():
    """Main entry point for running metrics evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate metrics for code generation tasks.")
    parser.add_argument('--input', type=str, required=True, help='Input file (CSV or JSON)')
    parser.add_argument('--output', type=str, required=True, help='Output file (CSV)')
    parser.add_argument('--ref-col', type=str, default='reference_code', help='Reference code column name')
    parser.add_argument('--cand-col', type=str, default='generated_code', help='Candidate code column name')
    
    args = parser.parse_args()
    
    run_metrics_evaluation(
        args.input, 
        args.output, 
        args.ref_col, 
        args.cand_col
    )

if __name__ == "__main__":
    main()
