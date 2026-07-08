# API Documentation: `code/utils.py`

This module provides utility functions for calculating linguistic complexity metrics and managing random seeds for reproducibility.

## Functions

### `pin_random_seed(seed: int = 42) -> None`

Pins the random seeds for Python's `random` module and `numpy` to ensure reproducible results across runs.

**Parameters:**
- `seed` (int): The seed value to use. Defaults to 42.

**Returns:**
- `None`

**Side Effects:**
- Sets `random.seed(seed)`
- Sets `numpy.random.seed(seed)`

---

### `calculate_mtld(text: str, threshold: float = 0.72) -> float`

Calculates the Measure of Textual Lexical Diversity (MTLD).

MTLD is a measure of lexical diversity that calculates the length of text segments needed to reach a specific Type-Token Ratio (TTR) threshold.

**Parameters:**
- `text` (str): The input text string to analyze.
- `threshold` (float): The TTR threshold to use. Defaults to 0.72 (standard value).

**Returns:**
- `float`: The calculated MTLD value. Returns `0.0` if the text is empty, contains fewer than 10 words, or if calculation fails.

**Implementation Details:**
- Uses `textstat.mtld()` internally.
- Validates that the input text is non-empty and has sufficient length.
- Handles exceptions gracefully by returning 0.0.

---

### `calculate_flesch_kincaid(text: str) -> float`

Calculates the Flesch-Kincaid Grade Level for a given text.

**Parameters:**
- `text` (str): The input text string to analyze.

**Returns:**
- `float`: The calculated Flesch-Kincaid grade level. Returns `0.0` if the text is empty or if calculation fails.

**Implementation Details:**
- Uses `textstat.flesch_kincaid_grade()` internally.
- Handles exceptions gracefully.

---

### `calculate_average_sentence_length(text: str) -> float`

Calculates the average sentence length in words.

**Parameters:**
- `text` (str): The input text string to analyze.

**Returns:**
- `float`: The average number of words per sentence. Returns `0.0` if the text is empty or contains no sentences.

**Implementation Details:**
- Splits text by sentence endings (`.`, `!`, `?`).
- Counts words in each sentence using regex `\b\w+\b`.
- Calculates the mean length.

---

### `get_all_metrics(text: str) -> dict`

Calculates all available linguistic complexity metrics for a given text.

**Parameters:**
- `text` (str): The input text string to analyze.

**Returns:**
- `dict`: A dictionary containing the following keys:
 - `"flesch_kincaid"` (float): Flesch-Kincaid grade level.
 - `"mtld"` (float): Measure of Textual Lexical Diversity.
 - `"avg_sentence_length"` (float): Average sentence length in words.

**Example:**
```python
from utils import get_all_metrics

text = "This is a sample text. It has two sentences."
metrics = get_all_metrics(text)
print(metrics)
# Output: {'flesch_kincaid': 4.5, 'mtld': 12.3, 'avg_sentence_length': 4.0}
```

## Dependencies

- `random` (standard library)
- `re` (standard library)
- `numpy`
- `textstat`
- `typing` (standard library)
