"""Stage 1: clean a messy company list.

Rule of this file: flag problems, never silently delete rows.
"""

import re
from urllib.parse import urlparse
import pandas as pd

# Two-part public suffixes handled by hand. A production tool would use the
# Public Suffix List (the tldextract library). Limit: unlisted suffixes are wrong.
MULTI_PART_SUFFIXES = {
    "co.uk",
    "org.uk",
    "ac.uk",
    "com.pk",
    "org.pk",
    "net.pk",
    "edu.pk",
    "com.au",
    "co.in",
    "co.nz",
    "com.sg",
    "co.za",
    "com.br",
}

LEGAL_SUFFIXES = {
    "inc",
    "llc",
    "ltd",
    "limited",
    "corp",
    "corporation",
    "co",
    "gmbh",
    "plc",
    "pvt",
    "llp",
}

_HOST_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
)


def is_blank(value):
  """True for None, NaN and empty or whitespace-only text."""
  if value is None:
    return True
  if isinstance(value, float) and pd.isna(value):
    return True
  if value is pd.NA:
    return True
  return str(value).strip() == ""


def normalize_domain(value):
  """Return the root domain, or None when the value is not a usable domain.

  'https://www.blog.Acme.co.uk/about' -> 'acme.co.uk'
  """
  if is_blank(value):
    return None
  text = str(value).strip().lower()
  if "://" not in text:
    text = "http://" + text
  try:
    host = urlparse(text).hostname or ""
  except ValueError:
    return None
  host = host.strip(".")
  if host.startswith("www."):
    host = host[4:]
  if host in MULTI_PART_SUFFIXES or not _HOST_RE.match(host):
    return None
  labels = host.split(".")
  if len(labels) >= 3 and ".".join(labels[-2:]) in MULTI_PART_SUFFIXES:
    return ".".join(labels[-3:])
  return ".".join(labels[-2:])


def clean_name(value):
  """Trim spaces, fix ALL CAPS or lowercase, and strip legal suffixes (Inc, LLC, Ltd)."""
  if is_blank(value):
    return ""
  text = re.sub(r"\s+", " ", str(value)).strip()
  if text.isupper() or text.islower():
    text = text.title()
  words = text.replace(",", " ").split()
  while len(words) > 1 and words[-1].lower().strip(".") in LEGAL_SUFFIXES:
    words.pop()
  return " ".join(words)


def clean_companies(df):
  """Return (cleaned, flagged). Every input row ends up in exactly one of them."""
  missing = {"name", "website"} - set(df.columns)
  if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")
  out = df.copy()
  out["name_clean"] = out["name"].map(clean_name)
  out["domain"] = out["website"].map(normalize_domain)
  seen = set()
  flags = []
  for row in out.itertuples():
    row_flags = []
    if not row.name_clean:
      row_flags.append("missing_name")
    if is_blank(row.website):
      row_flags.append("missing_domain")
    elif pd.isna(row.domain):
      row_flags.append("invalid_domain")
    elif row.domain in seen:
      row_flags.append("duplicate_domain")
    else:
      seen.add(row.domain)
    flags.append(";".join(row_flags))
  out["flag"] = flags
  cleaned = out[out["flag"] == ""].drop(columns="flag").reset_index(drop=True)
  flagged = out[out["flag"] != ""].reset_index(drop=True)
  return cleaned, flagged