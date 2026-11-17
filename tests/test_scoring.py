import copy
import pandas as pd
import pytest
from src.scoring import load_config, parse_size, score_dataframe, score_icp


@pytest.fixture
def config():
    return load_config("config/icp_config.json")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("25", 25),
        ("11-50", 30),
        ("11–50", 30),
        ("200+", 200),
        ("1,000", 1000),
        ("51-200 employees", 125),
        ("many", None),
        ("", None),
        (None, None),
        ("0", None),
    ],
)
def test_parse_size(raw, expected):
    assert parse_size(raw) == expected


def test_ideal_company_scores_100(config):
    row = {
        "size": "10",
        "country": "United States",
        "services": "B2B lead generation, outbound and demand generation, growth",
    }
    score, _ = score_icp(row, config)
    assert score == 100  # 40 + 25 + 35 (keyword points are capped)


def test_missing_size_scores_zero_for_size_and_says_so(config):
    score, reasons = score_icp(
        {"size": None, "country": "Pakistan", "services": ""}, config
    )
    assert score == 5  # only the non-target country points
    assert any("size missing" in r for r in reasons)


def test_score_is_never_below_zero(config):
    row = {"size": "5000", "country": "", "services": "b2c ecommerce retail"}
    score, _ = score_icp(row, config)
    assert score == 0


def test_score_is_never_above_100(config):
    big = copy.deepcopy(config)
    big["size"]["points_ideal"] = 500
    score, _ = score_icp({"size": "10", "country": "Canada", "services": "b2b"}, big)
    assert score == 100


def test_negative_keywords_reduce_the_score(config):
    plain = {"size": "10", "country": "Canada", "services": "growth"}
    risky = {"size": "10", "country": "Canada", "services": "growth b2c"}
    assert score_icp(risky, config)[0] == score_icp(plain, config)[0] - 10


def test_keywords_match_whole_words_only(config):
    score, _ = score_icp(
        {"size": "10", "country": "Canada", "services": "outbounds"}, config
    )
    assert score == 65  # 40 + 25, no keyword points


def test_changing_the_config_changes_the_score(config):
    row = {"size": "10", "country": "Canada", "services": ""}
    before = score_icp(row, config)[0]
    config["size"]["points_ideal"] = 10
    assert score_icp(row, config)[0] == before - 30


def test_score_dataframe_keeps_every_row_and_adds_columns(config):
    df = pd.DataFrame({
        "name_clean": ["A", "B"],
        "size": ["10", None],
        "country": ["Canada", None],
        "services": [None, "x"],
    })
    out = score_dataframe(df, config)
    assert len(out) == len(df)
    assert {"icp_score", "icp_reasons"} <= set(out.columns)
    assert out["icp_score"].between(0, 100).all()