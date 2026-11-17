import pandas as pd
import pytest
from src.cleaner import clean_companies, clean_name, normalize_domain


def test_root_domain_from_full_url():
    assert normalize_domain("https://www.blog.Acme.com/about?x=1") == "acme.com"


def test_bare_domain_without_scheme():
    assert normalize_domain("acme.com") == "acme.com"


def test_two_part_suffix_keeps_three_labels():
    assert normalize_domain("https://shop.acme.co.uk") == "acme.co.uk"


@pytest.mark.parametrize(
    "bad",
    [None, "", "   ", "not a url", "localhost", "http://", "co.uk", float("nan")],
)
def test_invalid_values_return_none(bad):
    assert normalize_domain(bad) is None


def test_clean_name_strips_legal_suffix_and_fixes_case():
    assert clean_name("  ACME   GROWTH, INC. ") == "Acme Growth"
    assert clean_name("Northwind Marketing LLC") == "Northwind Marketing"


def test_clean_name_keeps_single_word_even_if_it_looks_like_a_suffix():
    assert clean_name("Limited") == "Limited"


def test_duplicates_are_flagged_not_deleted():
    df = pd.DataFrame({
        "name": ["Acme Inc", "Acme Ltd", "Beta LLC"],
        "website": ["https://acme.com", "http://www.acme.com/contact", "beta.io"],
    })
    cleaned, flagged = clean_companies(df)
    assert len(cleaned) == 2
    assert len(flagged) == 1
    assert flagged.loc[0, "flag"] == "duplicate_domain"
    assert len(cleaned) + len(flagged) == len(df)


def test_missing_and_invalid_websites_are_flagged():
    df = pd.DataFrame({"name": ["A", "B", "C"], "website": [None, "???", "c.com"]})
    cleaned, flagged = clean_companies(df)
    assert list(flagged["flag"]) == ["missing_domain", "invalid_domain"]
    assert list(cleaned["domain"]) == ["c.com"]


def test_missing_name_is_flagged():
    df = pd.DataFrame({"name": ["", "Real Co"], "website": ["a.com", "b.com"]})
    cleaned, flagged = clean_companies(df)
    assert list(flagged["flag"]) == ["missing_name"]


def test_empty_dataframe_does_not_crash():
    df = pd.DataFrame({"name": [], "website": []})
    cleaned, flagged = clean_companies(df)
    assert len(cleaned) == 0 and len(flagged) == 0


def test_missing_required_columns_raises_clear_error():
    with pytest.raises(ValueError, match="Missing required columns"):
        clean_companies(pd.DataFrame({"name": ["A"]}))