# Signal-to-Meeting Engine (Stages 1-2)

A deterministic Python CLI pipeline that normalizes company names and root domains, flags duplicates and invalid records without silent row loss, and assigns a config-driven 0-100 Ideal Customer Profile (ICP) score prior to paid enrichment.

## Architecture (Stages 1-2)

```text
+-------------------+      +------------------------------------+      +-----------------------------+
|   Raw Company CSV | ---> | Stage 1: Cleaner (src/cleaner.py)  | ---> | flagged.csv (Audit Trail)   |
| (Messy lead list) |      | - Strip legal suffixes (Inc, LLC)  |      +-----------------------------+
+-------------------+      | - Normalize root domain            |                    |
                           | - Flag missing/invalid/duplicates  |                    v (Clean rows only)
                           +------------------------------------+      +-----------------------------+
                                                                       | Stage 2: Scorer (scoring.py)|
                                                                       | - Config-driven ICP (0-100) |
                                                                       | - Outputs cleaned_scored.csv|
                                                                       +-----------------------------+
```

## 1. How to Run

```bash
git clone https://github.com/creativekhubaib/signal-to-meeting-engine.git
cd signal-to-meeting-engine
pip install -r requirements.txt
python -m src.main --input data/raw_companies.csv --output-dir data/processed
pytest -v
```

## 2. Sample Output (cleaned_scored.csv)

*Synthetic sample rows illustrating normalized fields, ICP scoring, and explainable reason strings (no real emails):*

| name | name_clean | website | domain | size | country | icp_score | icp_reasons |
|---|---|---|---|---|---|---|---|
| ACME GROWTH, INC. | Acme Growth | https://www.blog.acme.com/about | acme.com | 15 | United States | 95 | size 15 is in the ideal range (+40); country United States is a target (+25); keywords [b2b, outbound, lead generation] (+30) |
| Northwind Media Ltd | Northwind Media | http://northwind.co.uk | northwind.co.uk | 45 | United Kingdom | 75 | size 45 is near the ideal range (+20); country United Kingdom is a target (+25); keywords [demand generation, growth] (+30) |
| Cedar Retail Corp | Cedar Retail | https://cedarretail.com | cedarretail.com | 500 | Canada | 15 | size 500 is outside the range (0); country Canada is a target (+25); negative keywords [retail] (-10) |

## 3. Measured Results & Enrichment Savings Formula

Measured on public sample dataset (`data/raw_companies.csv`):

- **Rows In:** 300
- **Rows Kept (Cleaned & Scored):** 259
- **Rows Flagged / Removed Total:** 41
- **Share of Rows Removed:** 13.7%
- **Mean ICP Score (Kept Rows):** 35.6 / 100
- **Duplicate Root Domains (duplicate_domain):** 31 *(includes 0 exact full-row duplicates)*
- **Missing Website (missing_domain):** 8
- **Invalid / Unparseable Domain (invalid_domain):** 1
- **Missing Company Name (missing_name):** 0
- **Multi-Flag Rows (combined flags):** 1

**Enrichment Savings Formula:**

```text
Estimated Credits Saved = Rows Removed (41) x Cost Per Enrichment Row
```

- **Cost Per Enrichment Row:** Assumption — to be measured Nov 21 during Clay sample run.
- **Estimated Credits Saved:** Pending Nov 21 measurement.

## 4. Data Source & Known Limits

- **Data Source:** Public sample company list (`data/raw_companies.csv`, 300 rows) containing company attributes only (no personal contact emails).
- **Public Suffix List Coverage:** `src/cleaner.py` uses `urllib.parse` with 13 hardcoded two-part suffixes (co.uk, com.pk, com.au, etc.) rather than the full Public Suffix List; unlisted country-code second-level domains may normalize to two labels instead of three.
- **Syntactic Validation Only:** Validates hostname syntax and root-domain uniqueness, not live DNS/MX records or SMTP inbox deliverability.
- **No Cross-Domain Entity Resolution:** Does not merge parent and subsidiary companies operating under separate root domains.
