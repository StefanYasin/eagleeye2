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


def test_site_coverage_expanded():
    """Roadmap #1: coverage grew from 4 to 60+ sites."""
    from eagleeye2.discovery import SITE_RULES
    assert len(SITE_RULES) >= 60
    for required in ("github", "youtube", "reddit", "linkedin", "facebook",
                     "telegram", "twitch", "steam", "spotify", "hackernews",
                     "huggingface", "keybase"):
        assert required in SITE_RULES, f"missing required site: {required}"


def test_all_sites_have_handle_placeholder():
    from eagleeye2.discovery import SITE_RULES
    for site, url in SITE_RULES.items():
        assert "{h}" in url, f"{site} URL missing handle placeholder: {url}"
