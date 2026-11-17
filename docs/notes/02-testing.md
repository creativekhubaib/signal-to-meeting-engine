# Stage 2 Notes: Missing Values, Testing & Self-Check

## 1. The 5 Missing-Value & Testing Questions

1. **Four ways data says "nothing" (and how to catch each):**
   - `None` (Python null object) -> caught with `value is None`.
   - `NaN` or `pd.NA` (pandas float/missing markers) -> caught with `pd.isna(value)`.
   - Empty string `""` -> caught with `value == ""`.
   - Whitespace or placeholder text like `"   "` -> caught with `str(value).strip() == ""`.
   - In our code, `is_blank(value)` checks all four in one place so we don't repeat checks everywhere.

2. **Why `nan == nan` returns `False`:**
   - `NaN` means "Not a Number" (an unknown or undefined value). Since two unknown values aren't guaranteed to be the same thing, Python/pandas treats `float("nan") == float("nan")` as `False`. You always have to use `pd.isna()` instead of `==`.

3. **Why we flag bad rows instead of deleting them:**
   - If you run `dropna()` or silently delete rows, you lose real companies that just had a typo in their website field, and your row counts stop adding up. Flagging keeps them in `flagged.csv` with a clear reason (`missing_domain`, `invalid_domain`, `duplicate_domain`) so a human can fix them.

4. **The test I trust most (and the bug it catches):**
   - `test_duplicates_are_flagged_not_deleted` (specifically `assert len(cleaned) + len(flagged) == len(df)`). It enforces the row-count invariant so if a future edit accidentally drops or double-counts a row, the test fails immediately.

5. **What a passing test proves (and doesn't prove):**
   - It proves the function behaves as expected on the exact inputs and edge cases we wrote in the test file. It does *not* prove the code is 100% bug-free on weird new data formats we haven't thought of yet.

## 2. Quick Self-Check Answers (Section 7)

- **What is an ICP & why rule-based?** An Ideal Customer Profile describes the exact type of company most likely to buy from us. We use rule-based weights right now because we have zero historical reply data—training an ML model without data would just invent fake patterns.
- **Walkthrough of `score_icp()` (size `11-50`, `United Kingdom`, 1 positive keyword):** `parse_size("11-50")` takes the midpoint (`30`), which lands in the near-ideal range (`2-30`) for `+20` points. `United Kingdom` is in the target country list for `+25` points. One positive keyword adds `+7` points. Total = `52`.
- **When size is missing:** `parse_size()` returns `None`, and `_score_size()` gives `0` points with the reason `"size missing (0)"`. It never crashes and never invents a fake size.
- **Three key tests & the bugs they catch:**
  1. `test_two_part_suffix_keeps_three_labels`: stops `.co.uk` or `.com.pk` domains from being cut down to just `co.uk`.
  2. `test_keywords_match_whole_words_only`: stops partial words like `outbounds` or `retailer` from triggering false keyword matches.
  3. `test_changing_the_config_changes_the_score`: proves weights actually come from `config/icp_config.json` and aren't hard-coded.
- **What `cleaned + flagged == input` protects against:** Silent data loss or accidental duplicate row creation during cleaning.
- **`.env.example` vs `.env`:** `.env.example` has blank variable names (`OPENAI_API_KEY=`) so anyone cloning the repo knows what settings are needed. `.env` holds my real private keys on my laptop and is blocked by `.gitignore`.
- **If a client sets a config weight to `500`:** `max(0, min(100, ...))` clamps the final score at `100`, proven by `test_score_is_never_above_100`.
- **What the score does not prove:** It is only an initial prioritization hypothesis, not proof of who will reply or buy.

## 3. My 60-Second Project Explanation

"Agencies burn paid enrichment credits and SDR time on messy lead lists full of duplicates and broken URLs. I built a Python cleaner and config-driven ICP scoring CLI tested with 39 pytest cases. On a real 300-row company list, it isolated 41 bad or duplicate rows (including 31 duplicate root domains) into an audit log and scored the remaining 259 clean companies from 0 to 100 with written reasons. Right now the scoring weights are a rule-based hypothesis rather than a trained model, and next I'm wiring the top-scored domains into an n8n AI research workflow."