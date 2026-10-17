import pytest
import pandas as pd
import profiler


def test_load_csv_keeps_text_and_nulls_blanks(tmp_path):
    csv = tmp_path / "in.csv"
    csv.write_text("zip,name\n007,a\n,b\n  ,c\n")

    df = profiler.load_csv(csv)

    assert df["zip"].tolist()[0] == "007"
    assert df["zip"].isna().tolist() == [False, True, True]


def test_profile_column_counts_nulls_and_distinct():
    series = pd.Series(["a", "a", "b", None])

    result = profiler.profile_column(series)

    assert result["null_count"] == 1
    assert result["null_pct"] == 25.0
    assert result["distinct_count"] == 2
    assert result["distinct_pct"] == 66.67
    assert result["top_values"] == {"a": 2, "b": 1}
    assert result["high_null"] is False


def test_profile_column_flags_high_null_only_above_half():
    assert profiler.profile_column(pd.Series(["a", None, None]))["high_null"] is True
    assert (
        profiler.profile_column(pd.Series(["a", "b", None, None]))["high_null"] is False
    )


def test_profile_column_handles_all_null_and_empty():
    all_null = profiler.profile_column(pd.Series([None, None], dtype=object))
    empty = profiler.profile_column(pd.Series([], dtype=object))

    assert all_null["null_pct"] == 100.0
    assert all_null["distinct_count"] == 0
    assert all_null["top_values"] == {}
    assert empty["null_count"] == 0


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([], "empty"),
        (["1", "-20", "007"], "integer"),
        (["1", "2.5"], "float"),
        (["03/14/2012", "2012-03-14"], "date"),
        (["60614", "60614-1234"], "mixed"),
        (["1", "03/14/2012"], "mixed"),
        (["Restaurant", "Grocery Store"], "string"),
    ],
)
def test_infer_type(values, expected):
    assert profiler.infer_type(pd.Series(values, dtype=object)) == expected


def test_profile_column_reports_type():
    assert (
        profiler.profile_column(pd.Series([None, None], dtype=object))["type"]
        == "empty"
    )
    assert (
        profiler.profile_column(pd.Series(["60614", "60614-1234"]))["type"] == "mixed"
    )


def test_profile_column_numeric_stats():
    result = profiler.profile_column(pd.Series(["1", "2", "4", None]))

    assert (result["min"], result["max"], result["median"]) == (1.0, 4.0, 2.0)
    assert result["mean"] == 2.3333
    assert "min_length" not in result


def test_profile_column_string_length_stats():
    result = profiler.profile_column(pd.Series(["ab", "abcd", None]))

    assert (result["min_length"], result["max_length"], result["avg_length"]) == (
        2,
        4,
        3.0,
    )
    assert "min" not in result


def test_profile_column_all_null_has_no_stats():
    result = profiler.profile_column(pd.Series([None, None], dtype=object))

    assert not {"min", "min_length"} & result.keys()
