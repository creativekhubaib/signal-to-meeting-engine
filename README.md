# Signal-to-Meeting Engine: Stage 1 Cleaner

Cleans and deduplicates a company list before paid enrichment, so credits are not wasted on junk or repeat rows.

## Data
- Source(s): Combined multi-source company-level records from public B2B/GTM agency directories (`outbound_agency_directory`, `scaliq_directory`, `clutch_manifest_pk`, `pseb_public_directory`, `techbehemoths_pk`, `agency_web_directory`), open Y Combinator B2B dataset exports (`kaggle_yc_dataset`, `yc_public_directory_mirror`), plus 5 deliberate edge-case rows labeled `synthetic` and 1 blank row.
- Rows in raw file: 300
- Company-level data only, no personal data.

## How to run
    python -m venv .venv  (then activate it)
    pip install -r requirements.txt
    python -m src.cleaner
    python -m pytest

## Outputs (data/processed/)
- cleaned.csv: name, website, size, country, source, name_clean, domain
- flagged.csv: same columns plus reason (blank_row, missing_domain, invalid_domain)
- dropped_duplicates.csv: same columns plus reason (duplicate_domain)

## Rules
- Domain = registrable root domain via tldextract.
- Duplicate key = domain. Keep rule: most complete row wins, ties go to the earliest row.
- Legal suffixes are stripped only at the end of a name.
- Nothing is deleted silently; every removed row is logged with a reason.

## Known limitations
- Variants like L.L.C. or non-English legal suffixes are not stripped.
- Companies with several domains are treated as separate companies.
- Different companies sharing a domain would be merged.

## Results (this run)
Rows in 300, blank 1, Missing 8, Invalid 1, Duplicates 31, Rows out 25