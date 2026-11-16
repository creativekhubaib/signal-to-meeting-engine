import pandas as pd
import pytest
from src.cleaner import clean_dataframe, clean_name, normalize_domain


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("https://www.blog.Acme.co.uk/about?x=1", "acme.co.uk"),
        ("www.acme.com", "acme.com"),
        ("  ACME.com/ ", "acme.com"),
        ("company.com.pk", "company.com.pk"),
        ("acme", None),
        ("", None),
        (None, None),
        ("192.168.1.1", None),
        ("not a domain", None),
    ],
)
def test_normalize_domain(raw, expected):
  assert normalize_domain(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Acme Inc.", "Acme"),
        ("Acme, LLC", "Acme"),
        ("Acme Pvt. Ltd.", "Acme"),
        ("Incorta", "Incorta"),
        ("Lincoln Group", "Lincoln Group"),
        ("  Acme   Corp ", "Acme"),
        ("Inc", "Inc"),
    ],
)
def test_clean_name(raw, expected):
  assert clean_name(raw) == expected


def test_arithmetic_closes_and_keeps_most_complete():
  df = pd.DataFrame({
      "name": ["Acme Inc", "Acme", "", "Beta", "Gamma"],
      "website": ["www.acme.com", "https://acme.com/", "", "", "gamma"],
      "size": ["", "50", "", "10", "5"],
      "country": ["", "US", "", "PK", "PK"],
      "source": ["a", "b", "", "a", "a"],
  })
  clean, flagged, dropped = clean_dataframe(df)
  assert len(df) == len(clean) + len(flagged) + len(dropped)
  assert list(clean["domain"]) == ["acme.com"]
  assert clean.iloc[0]["size"] == "50"  # most complete row won
  assert set(flagged["reason"]) == {
      "blank_row",
      "missing_domain",
      "invalid_domain",
  }
  assert list(dropped["reason"]) == ["duplicate_domain"]