"""Stage 2: a rule-based ICP score (0 to 100) driven by a config file.

ICP means ideal customer profile. The rules live in config/icp_config.json,
not in this code, so you can change the rules without touching the code.
"""

import json
import re
from pathlib import Path
import pandas as pd
from src.cleaner import is_blank


def load_config(path):
    """Read the scoring rules from a JSON file."""
    with open(Path(path), encoding="utf-8") as handle:
        return json.load(handle)


def parse_size(value):
    """Turn a size cell into one number, or None.

    '25' -> 25 | '11-50' -> 30 (midpoint) | '200+' -> 200 | '1,000' -> 1000 | 'many' -> None
    """
    if is_blank(value):
        return None
    numbers = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", str(value))]
    numbers = [n for n in numbers if n > 0]
    if not numbers:
        return None
    if len(numbers) == 1:
        return numbers[0]
    return (numbers[0] + numbers[1]) // 2


def _score_size(size, cfg):
    if size is None:
        return 0, "size missing (0)"
    if cfg["ideal_min"] <= size <= cfg["ideal_max"]:
        return cfg["points_ideal"], f"size {size} is in the ideal range (+{cfg['points_ideal']})"
    if cfg["near_min"] <= size <= cfg["near_max"]:
        return cfg["points_near"], f"size {size} is near the ideal range (+{cfg['points_near']})"
    return 0, f"size {size} is outside the range (0)"


def _score_country(country, cfg):
    if is_blank(country):
        return 0, "country missing (0)"
    targets = {c.lower() for c in cfg["target"]}
    if str(country).strip().lower() in targets:
        return cfg["points_target"], f"country {country} is a target (+{cfg['points_target']})"
    return cfg["points_other"], f"country {country} is not a target (+{cfg['points_other']})"


def _contains(text, keyword):
    return re.search(r"\b" + re.escape(keyword.lower()) + r"\b", text) is not None


def _score_keywords(text, cfg):
    text = text.lower()
    hits = [k for k in cfg["positive"] if _contains(text, k)]
    misses = [k for k in cfg["negative"] if _contains(text, k)]
    points = min(len(hits) * cfg["points_each"], cfg["max_points"])
    points -= len(misses) * cfg["penalty_each"]
    reasons = []
    if hits:
        reasons.append(f"keywords {hits} (+{min(len(hits) * cfg['points_each'], cfg['max_points'])})")
    if misses:
        reasons.append(f"negative keywords {misses} (-{len(misses) * cfg['penalty_each']})")
    if not hits and not misses:
        reasons.append("no keyword signal (0)")
    return points, reasons


def score_icp(row, config):
    """Return (score, reasons) for one company. Score is an int from 0 to 100.

    `row` can be a dict or a pandas row. It may have: size, country, services, name_clean.
    """
    size_pts, size_reason = _score_size(parse_size(row.get("size")), config["size"])
    country_pts, country_reason = _score_country(row.get("country"), config["country"])
    parts = [row.get("name_clean"), row.get("services")]
    text = " ".join(str(p) for p in parts if not is_blank(p))
    kw_pts, kw_reasons = _score_keywords(text, config["keywords"])
    score = max(0, min(100, size_pts + country_pts + kw_pts))
    return score, [size_reason, country_reason, *kw_reasons]


def score_dataframe(df, config):
    """Add icp_score and icp_reasons columns. Row count never changes."""
    out = df.copy()
    results = [score_icp(row, config) for row in out.to_dict("records")]
    out["icp_score"] = [score for score, _ in results]
    out["icp_reasons"] = ["; ".join(reasons) for _, reasons in results]
    return out