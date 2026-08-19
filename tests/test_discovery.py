from eagleeye2.discovery import candidate_handles


def test_handles_two_words():
    handles = candidate_handles("Barack Obama")
    assert "barackobama" in handles
    assert "barack.obama" in handles
    assert "barack_obama" in handles
    assert "barackobama1" in handles


def test_handles_single_name():
    assert candidate_handles("Cher") == ["cher"]


def test_handles_three_words():
    handles = candidate_handles("John Quincy Adams")
    assert "johnadams" in handles  # first + last
    assert "john.adams" in handles


def test_handles_empty():
    assert candidate_handles("") == []
    assert candidate_handles("???") == []


def test_handles_are_sorted_and_unique():
    handles = candidate_handles("John John")
    assert handles == sorted(set(handles))
