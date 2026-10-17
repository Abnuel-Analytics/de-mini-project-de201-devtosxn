import profiler


def test_load_csv_keeps_text_and_nulls_blanks(tmp_path):
    csv = tmp_path / "in.csv"
    csv.write_text("zip,name\n007,a\n,b\n  ,c\n")

    df = profiler.load_csv(csv)

    assert df["zip"].tolist()[0] == "007"
    assert df["zip"].isna().tolist() == [False, True, True]
