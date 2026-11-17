import json
import pandas as pd
from src.main import main, run


def _write_raw(path):
    pd.DataFrame({
        "name": ["Acme Inc", "ACME LTD", "Beta Growth LLC", "Gamma", "Delta"],
        "website": ["https://acme.com", "www.acme.com", "beta.io", "", "???"],
        "size": ["10", "10", "30", "5", "8"],
        "country": ["United States", "United States", "Canada", "Canada", "Canada"],
        "services": ["b2b outbound", "b2b outbound", "growth", "growth", "growth"],
    }).to_csv(path, index=False)


def test_run_writes_outputs_and_counts_add_up(tmp_path):
    raw = tmp_path / "raw.csv"
    _write_raw(raw)
    summary = run(raw, tmp_path / "out", "config/icp_config.json")
    assert summary["rows_in"] == 5
    assert summary["rows_out"] + summary["rows_flagged"] == 5
    assert summary["flag_reasons"] == {
        "duplicate_domain": 1,
        "missing_domain": 1,
        "invalid_domain": 1,
    }
    assert (tmp_path / "out" / "cleaned_scored.csv").exists()
    assert json.loads((tmp_path / "out" / "run_summary.json").read_text())["rows_in"] == 5


def test_cli_returns_2_for_missing_input_file(tmp_path):
    code = main(["--input", str(tmp_path / "nope.csv"), "--output-dir", str(tmp_path)])
    assert code == 2


def test_cli_returns_0_on_success(tmp_path):
    raw = tmp_path / "raw.csv"
    _write_raw(raw)
    assert main(["--input", str(raw), "--output-dir", str(tmp_path / "o")]) == 0