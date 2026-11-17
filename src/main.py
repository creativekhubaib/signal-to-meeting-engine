"""Command-line entry point: clean, score and save a company list.

Run from the repo root:
    python -m src.main --input data/raw_companies.csv
"""

import argparse
import json
import logging
import sys
from pathlib import Path
import pandas as pd
from src.cleaner import clean_companies
from src.scoring import load_config, score_dataframe

log = logging.getLogger("engine")


def build_parser():
    parser = argparse.ArgumentParser(description="Clean and score a company list.")
    parser.add_argument("--input", required=True, help="path to the raw CSV")
    parser.add_argument("--output-dir", default="data", help="where to write results")
    parser.add_argument("--config", default="config/icp_config.json", help="scoring rules")
    parser.add_argument("--verbose", action="store_true", help="show debug logging")
    return parser


def run(input_path, output_dir, config_path):
    """Clean, score and save. Returns a summary dict."""
    raw = pd.read_csv(input_path, dtype=str)
    config = load_config(config_path)
    cleaned, flagged = clean_companies(raw)
    scored = score_dataframe(cleaned, config).sort_values("icp_score", ascending=False)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scored.to_csv(out_dir / "cleaned_scored.csv", index=False)
    flagged.to_csv(out_dir / "flagged.csv", index=False)

    summary = {
        "rows_in": len(raw),
        "rows_out": len(scored),
        "rows_flagged": len(flagged),
        "flag_reasons": {
            reason: int(count)
            for reason, count in flagged["flag"].str.split(";").explode().value_counts().items()
        },
        "mean_score": round(float(scored["icp_score"].mean()), 1) if len(scored) else None,
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info(
        "rows in=%d rows out=%d rows flagged=%d",
        summary["rows_in"],
        summary["rows_out"],
        summary["rows_flagged"],
    )
    return summary


def main(argv=None):
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        run(args.input, args.output_dir, args.config)
    except FileNotFoundError as err:
        log.error("File not found: %s", err.filename)
        return 2
    except ValueError as err:
        log.error("Bad input: %s", err)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())