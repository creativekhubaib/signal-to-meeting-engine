# Root Domain vs. Subdomain Deduplication

- **Root domain vs. subdomain:** A subdomain (log.acme.com or www.acme.co.uk) points to a section or host of a site, whereas the registrable root domain (cme.com or cme.co.uk) identifies the actual organization.
- **Why we dedupe on root domain:** Raw lead lists often contain multiple contacts, regional subdomains, or http/www variants for the same company.
- **Proof from Stage 1:** On our 300-row public sample list, exact row matching caught 0 duplicates, while root-domain normalization (
ormalize_domain in src/cleaner.py) caught 31 duplicate companies before paid enrichment.
