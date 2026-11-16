from pathlib import Path
import re
import pandas as pd
import tldextract

# File paths & schema constants
RAW_PATH = Path("data/raw/companies_raw.csv")
OUT_DIR = Path("data/processed")
FIELDS = ["name", "website", "size", "country"]

# Offline Public Suffix List extractor (no network calls, deterministic output)
_extract = tldextract.TLDExtract(suffix_list_urls=())


def normalize_domain(raw):
  """Extract the registrable root domain (e.g., 'acme.co.uk') from any messy URL."""
  text = str(raw or "").strip().lower()
  if not text or re.search(r"\s", text):
    return None
  ext = _extract(text)
  if not ext.domain or not ext.suffix:
    return None
  return f"{ext.domain}.{ext.suffix}"



_LEGAL_RE = re.compile(
    r"(?:[\s,]+(?:inc|incorporated|llc|ltd|limited|llp|lp|corp|corporation|gmbh|pvt|plc|pty)\.?)+\s*$",
    re.IGNORECASE,
)


def clean_name(raw):
  """Collapse internal spaces and strip trailing legal entity suffixes."""
  name = re.sub(r"\s+", " ", str(raw or "")).strip()
  stripped = _LEGAL_RE.sub("", name).strip(" ,")
  return stripped or name


def clean_dataframe(df):
  """Separate blank/invalid rows, normalize fields, and deduplicate by root domain."""
  df = df.copy()
  df.columns = [c.strip().lower() for c in df.columns]
  for col in df.columns:
    df[col] = df[col].astype(str).str.strip()

  # 1. Isolate completely blank rows first
  blank_mask = (df == "").all(axis=1)
  blank = df[blank_mask].assign(reason="blank_row")
  work = df[~blank_mask].copy()

  # 2. Compute normalized company name and registrable root domain
  work["name_clean"] = work["name"].apply(clean_name)
  work["domain"] = work["website"].apply(normalize_domain)

  # 3. Separate missing websites from malformed/invalid domains
  missing_mask = work["website"] == ""
  invalid_mask = ~missing_mask & work["domain"].isna()
  missing = work[missing_mask].assign(reason="missing_domain")
  invalid = work[invalid_mask].assign(reason="invalid_domain")
  flagged = pd.concat([blank, missing, invalid])

  # 4. Deduplicate valid candidates (most complete row wins; ties keep earliest)
  candidates = work[~missing_mask & ~invalid_mask].copy()
  candidates["_filled"] = (candidates[FIELDS] != "").sum(axis=1)
  candidates = candidates.sort_values("_filled", ascending=False, kind="stable")
  dup_mask = candidates.duplicated(subset="domain", keep="first")

  dropped = candidates[dup_mask].assign(reason="duplicate_domain")
  clean = candidates[~dup_mask].sort_index()

  clean = clean.drop(columns="_filled")
  dropped = dropped.drop(columns="_filled").sort_index()
  return clean, flagged, dropped



def main():
  df = pd.read_csv(
      RAW_PATH,
      dtype=str,
      keep_default_na=False,
      encoding="utf-8-sig",
      skip_blank_lines=False,
  )
  rows_in = len(df)
  clean, flagged, dropped = clean_dataframe(df)

  OUT_DIR.mkdir(parents=True, exist_ok=True)
  clean.to_csv(OUT_DIR / "cleaned.csv", index=False, encoding="utf-8")
  flagged.to_csv(OUT_DIR / "flagged.csv", index=False, encoding="utf-8")
  dropped.to_csv(
      OUT_DIR / "dropped_duplicates.csv", index=False, encoding="utf-8"
  )

  counts = flagged["reason"].value_counts()
  n_blank = int(counts.get("blank_row", 0))
  n_missing = int(counts.get("missing_domain", 0))
  n_invalid = int(counts.get("invalid_domain", 0))

  print(f"Rows in:           {rows_in}")
  print(f"Blank rows:        {n_blank}")
  print(f"Missing domain:    {n_missing}")
  print(f"Invalid domain:    {n_invalid}")
  print(f"Duplicates:        {len(dropped)}")
  print(f"Rows out (clean):  {len(clean)}")
  print(f"Removed overall:   {100 * (rows_in - len(clean)) / rows_in:.1f}%")

  assert rows_in == len(clean) + len(flagged) + len(
      dropped
  ), "Row arithmetic does not close!"


if __name__ == "__main__":
  main()