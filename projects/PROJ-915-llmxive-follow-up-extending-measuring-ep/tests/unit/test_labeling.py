import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from labeling import apply_label_logic, detect_safety_refusal

def test_apply_label_logic():
    assert apply_label_logic(0.7, 0.5, False) == 1
    assert apply_label_logic(0.5, 0.7, False) == 0
    assert apply_label_logic(0.5, 0.5, True) == 2

def test_detect_safety_refusal():
    assert detect_safety_refusal("I cannot answer that.") == True
    assert detect_safety_refusal("Here is the answer.") == False