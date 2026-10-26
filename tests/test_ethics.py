"""Unit tests for the legal/ethical gate — the component every scan passes through.

No network, no deepface, no image files: this is pure logic, so it runs in CI
without the heavy stack.
"""

from eagleeye2.ethics import (
    USE_CASE_DESCRIPTIONS,
    EthicsGate,
    UseCase,
    parse_use_case,
)


def test_affirm_requires_a_purpose():
    """Without --purpose a scan must be rejected (non-interactive default)."""
    assert EthicsGate().affirm(None) is False


def test_affirm_accepts_every_use_case():
    gate = EthicsGate()
    for use_case in UseCase:
        assert gate.affirm(use_case) is True, use_case


def test_auto_accept_skips_the_gate():
    assert EthicsGate(auto_accept=True).affirm(None) is True


def test_notice_states_the_responsibility():
    notice = EthicsGate.notice()
    assert "LEGAL" in notice
    assert "OSINT" in notice
    assert "stalking" in notice


def test_every_use_case_has_a_description():
    """A use case with no help text renders an empty line in the CLI prompt."""
    assert set(USE_CASE_DESCRIPTIONS) == set(UseCase)
    for use_case, description in USE_CASE_DESCRIPTIONS.items():
        assert description.strip(), use_case


def test_parse_use_case_accepts_every_value():
    for use_case in UseCase:
        assert parse_use_case(use_case.value) is use_case


def test_parse_use_case_normalizes_case_and_whitespace():
    assert parse_use_case("  Investigation ") is UseCase.INVESTIGATION
    assert parse_use_case("TRUST_SAFETY") is UseCase.TRUST_SAFETY


def test_parse_use_case_allows_a_missing_value():
    assert parse_use_case(None) is None
    assert parse_use_case("") is None
    assert parse_use_case("   ") is None


def test_parse_use_case_rejects_a_typo_with_the_valid_list():
    try:
        parse_use_case("investgation")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("a typo in --purpose should raise ValueError")
    assert "investgation" in message
    for use_case in UseCase:
        assert use_case.value in message, use_case
