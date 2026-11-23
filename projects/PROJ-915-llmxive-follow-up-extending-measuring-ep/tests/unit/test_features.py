import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features import count_modal_verbs, count_citations

def test_count_modal_verbs():
    text = "You should consider this. We might do that."
    assert count_modal_verbs(text) == 2

def test_count_citations():
    text = "See [1] and (Author, 2020)."
    assert count_citations(text) == 2