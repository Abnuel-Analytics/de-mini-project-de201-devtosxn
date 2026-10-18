# Chicago Food Inspections: Data Quality Report

Is this dataset good enough to load into a database? Yes, with cleaning. The core facts (IDs, dates, results) are reliable once 149 duplicated inspections are removed. Five columns are empty and one is corrupted, so those should not be loaded.

## Dataset summary

| Item | Value |
|------|-------|
| Source | [Kaggle: Chicago Food Inspections](https://www.kaggle.com/datasets/chicago/chicago-food-inspections), file `food-inspections.csv` |
| Rows | 196,825 |
| Columns | 22 |
| File size | 232,867,748 bytes (about 222 MiB) |
| Inspection dates | 2010-01-04 to 2019-12-04 |
| Duplicate rows | 149 |
| Distinct `Inspection ID` | 196,676 |

Every figure below comes from `output/profile_results.json` or from a query on the same file, noted in the Evidence column.

## Data quality issues

| # | Issue | Evidence | Impact |
|---|-------|----------|--------|
| 1 | Duplicate inspections | 149 `Inspection ID` values appear twice (298 rows). In every case the two rows are identical. They are dated 2015-06-11 to 2019-05-02: 72 rows in 2015, 48 in 2016, 40 in 2017, 102 in 2018, 36 in 2019 (profile `duplicate_rows`; query: `duplicated(keep=False)`) | `Inspection ID` cannot be a primary key until they are removed. Counts are inflated by 0.08%. |
| 2 | Five columns are completely empty | `Historical Wards 2003-2015`, `Zip Codes`, `Community Areas`, `Census Tracts` and `Wards` are null in all 196,825 rows and profile as `empty` | Dead weight. Do not load them. |
| 3 | `Location` is corrupted | Stored as a dict-like string such as `{'latitude': '-87.65...', 'longitude': '41.94...'}`. In all 196,135 non-null rows the value labelled `latitude` equals the `Longitude` column, and the value labelled `longitude` equals the `Latitude` column (query: parse with `ast.literal_eval` and compare) | Parsing it would put every point in the wrong place. Use the `Latitude` and `Longitude` columns and drop this one. |
| 4 | `City` has 71 values for mostly one city | `CHICAGO` 195,986; `Chicago` 320; `chicago` 97; `CCHICAGO` 46; `CHicago` 12. 10 rows say `CHESTNUT STREET`, a street name in the city field, for example `Manierre` at `1420 N Hudson (432W)` (profile `top_values`, query on `City`) | Grouping by city undercounts Chicago. Needs upper-casing and fixes. |
| 5 | Categorical text differs only by case | `Inspection Type`: 108 distinct, 96 after lower-casing. `Facility Type`: 491 distinct, 442 after lower-casing (query: `nunique` on `str.lower().str.strip()`) | Inflated category counts, split totals. |
| 6 | `Violations` packs up to 34 findings into one cell | Items joined by ` \| `, 4.4 on average. Length up to 11,620 characters, 1,234.51 on average. 52,266 rows (26.55%) are null (profile) | Not queryable as is. Belongs in a child table. |
| 7 | `License #` uses `0` as a placeholder | 519 rows are `0`, 17 are null. Profile min is `0.0` | A fake licence number can join unrelated businesses. Turn `0` into null. |
| 8 | `Risk` has a value outside the scale | `All` appears 31 times next to `Risk 1 (High)` 141,129, `Risk 2 (Medium)` 38,431, `Risk 3 (Low)` 17,165; 69 are null (profile) | Breaks any ordered or enum column. |
| 9 | Padding and spacing noise | 196,317 of 196,822 non-null `Address` values (99.7%) have leading or trailing spaces; 760 have runs of spaces (query: compare to `str.strip()`) | Equal addresses compare as different. |
| 10 | Same business, several spellings | 884 business names collapse to the same key after removing spaces, punctuation and case (query: group `DBA Name` by upper-cased alphanumerics) | Breaks counts per business. Needs fuzzy matching later. |
| 11 | Codes typed as numbers, names typed as mixed | `Zip` and `License #` profile as `integer`, but a zip is a code (leading zeros, never summed). `DBA Name` has 3 digit-only names, `AKA Name` 19 and `Facility Type` 15, so the profiler types them `mixed` | Types must be declared, not inferred. |

Also noted: 248 rows are identical in every column except `Inspection ID`, which is 99 more than the 149 duplicated IDs. Those 99 are the same inspection recorded under different IDs, and the IDs hide it.

## Checks that came back clean

- `Zip` is clean in this snapshot: all 196,775 non-null values are exactly 5 digits (0 non-digit, 0 of other lengths). The mixed-type zip problem does not appear here, but `Zip` is still a code and is loaded as text.
- Every `Inspection Date` parses, and every one is exactly midnight. The column is a date, not a timestamp.
- Coordinates all fall inside Chicago: latitude 41.64 to 42.02, longitude -87.91 to -87.53.
- `Latitude`, `Longitude` and `Location` are null together on the same 690 rows (0.35%).
- `Violations` is highest of the partly-null columns at 26.55%, and that is expected: it is empty for 100% of `Out of Business` and `Business Not Located` rows, 97% of `Not Ready` and 93% of `No Entry`.
- Only 3 rows are outside `IL` (`IN`, `NY`, `WI`, one each), and 1,439 zips do not start with `606`. They are worth a look but not necessarily wrong.

## Recommended SQL types

PostgreSQL, sized from the profile's maximum lengths with some headroom.

| Column | Profiled as | SQL type | Why |
|--------|-------------|----------|-----|
| `Inspection ID` | integer | `INTEGER` | Max 2,352,738. |
| `DBA Name` | mixed | `VARCHAR(100)` | Longest is 79. Digit-only names are still text. |
| `AKA Name` | mixed | `VARCHAR(100)` | Longest is 79. |
| `License #` | integer | `INTEGER` | Max 9,999,999. |
| `Facility Type` | mixed | `VARCHAR(60)` | Longest is 47. |
| `Risk` | string | `VARCHAR(20)` | Longest is 15. |
| `Address` | string | `VARCHAR(60)` | Longest is 40. |
| `City` | string | `VARCHAR(30)` | Longest is 20. |
| `State` | string | `CHAR(2)` | Always 2 characters. |
| `Zip` | integer | `CHAR(5)` | A code. All 196,775 non-null values are 5 digits. |
| `Inspection Date` | date | `DATE` | Always midnight. |
| `Inspection Type` | string | `VARCHAR(60)` | Longest is 41. |
| `Results` | string | `VARCHAR(30)` | Longest is 20. |
| `Violations` | string | `TEXT` | Up to 11,620 characters. |
| `Latitude` | float | `DOUBLE PRECISION` | About 15 significant digits. |
| `Longitude` | float | `DOUBLE PRECISION` | About 15 significant digits. |
| `Location` | string | not loaded | Swapped coordinates (issue 3). |
| `Historical Wards 2003-2015`, `Zip Codes`, `Community Areas`, `Census Tracts`, `Wards` | empty | not loaded | 100% null (issue 2). |

## Preliminary schema proposal

Two tables. `inspection_violations` is split out because one inspection has up to 34 findings (issue 6). Nullable follows the profile's null counts, after removing the 149 duplicates (issue 1) and the cleaning below.

### Table `inspections` (one row per inspection)

| Column | Type | Nullable | Rationale |
|--------|------|----------|-----------|
| `inspection_id` | `INTEGER` | no | Primary key. 196,676 distinct values once the 149 duplicates are removed. |
| `dba_name` | `VARCHAR(100)` | no | 0 nulls. Trim whitespace on load. |
| `aka_name` | `VARCHAR(100)` | yes | 2,458 nulls (1.25%). |
| `license_no` | `INTEGER` | yes | 17 nulls plus 519 placeholder `0` values, both stored as null (issue 7). |
| `facility_type` | `VARCHAR(60)` | yes | 4,768 nulls (2.42%). Standardise case (issue 5). |
| `risk` | `VARCHAR(20)` | yes | 69 nulls. `All` (31 rows) becomes null (issue 8). |
| `address` | `VARCHAR(60)` | yes | 3 nulls. Trim (issue 9). |
| `city` | `VARCHAR(30)` | yes | 139 nulls. Upper-case and fix typos (issue 4). |
| `state` | `CHAR(2)` | yes | 42 nulls. |
| `zip` | `CHAR(5)` | yes | 50 nulls. Text, so leading zeros survive (issue 11). |
| `inspection_date` | `DATE` | no | 0 nulls. All values are midnight. |
| `inspection_type` | `VARCHAR(60)` | yes | 1 null. Standardise case (issue 5). |
| `results` | `VARCHAR(30)` | no | 0 nulls. Seven distinct values, so it could become a lookup table later. |
| `latitude` | `DOUBLE PRECISION` | yes | 690 nulls, always together with `longitude`. |
| `longitude` | `DOUBLE PRECISION` | yes | Same 690 nulls. |

### Table `inspection_violations` (one row per finding)

| Column | Type | Nullable | Rationale |
|--------|------|----------|-----------|
| `inspection_id` | `INTEGER` | no | Foreign key to `inspections`. |
| `position` | `SMALLINT` | no | Order within the original cell, 1 to 34. Together with `inspection_id` it is the primary key. |
| `description` | `TEXT` | no | One finding, split on ` \| `. Inspections with a null `Violations` cell get no rows here. |

Pulling the numeric violation code out of each description is a follow-up. I have not checked that every finding starts with one.

## Columns not to load as they are

| Column | Why | What to do |
|--------|-----|------------|
| `Historical Wards 2003-2015`, `Zip Codes`, `Community Areas`, `Census Tracts`, `Wards` | 100% null (issue 2). | Drop all five. |
| `Location` | Latitude and longitude are swapped inside it (issue 3). | Drop it. Use `Latitude` and `Longitude`. |
| `Violations` | Up to 34 findings in one cell, up to 11,620 characters (issue 6). | Split into `inspection_violations`. |
| `Inspection ID` | 149 values appear twice (issue 1). | Remove the duplicate rows before using it as a key. |
| `License #` | `0` is a placeholder in 519 rows (issue 7). | Convert `0` to null. |
| `Zip` | A code that profiles as an integer (issue 11). | Load as `CHAR(5)`, never `INT`. |
| `City` | 71 spellings of mostly one city (issue 4). | Upper-case, fix typos. |
| `Risk` | Contains `All` in 31 rows (issue 8). | Convert `All` to null. |
| `Inspection Type`, `Facility Type` | Case-only duplicates (issue 5). | Lower-case and trim for matching, then pick one display form. |
| `Address` | Padding in 99.7% of values (issue 9). | Trim on load. |
