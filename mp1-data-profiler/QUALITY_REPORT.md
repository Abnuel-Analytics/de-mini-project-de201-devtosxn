# Chicago Food Inspections: Data Quality Report

**Can we load this file into a database?** Yes, but not as it is. Most of the inspection details are reliable. A few columns are empty or wrong, 149 inspections are listed twice, and some text needs tidying first.

## About the file

| | |
|---|---|
| Source | [Kaggle: Chicago Food Inspections](https://www.kaggle.com/datasets/chicago/chicago-food-inspections) (`food-inspections.csv`) |
| Rows | 196,825 (one row per inspection) |
| Columns | 22 |
| File size | 232,867,748 bytes (about 222 MB) |
| Inspection dates | 4 Jan 2010 to 4 Dec 2019 |

In this report, "blank" means the cell has no value. Every number comes from `output/profile_results.json`, or from a quick check on the same file that is named in the text.

## The 8 biggest problems

### 1. 149 inspections appear twice

- **What was found:** 149 `Inspection ID` values show up two times, so 298 rows. In every case the two rows are exact copies. They are all from June 2015 to May 2019. Another 99 rows match some other row in every column except the ID.
- **Rationale:** An ID should be unique. With copies in the data, counts are too high and the ID cannot be used as the table's key.
- **What to do:** Keep one copy of each.

### 2. The `Location` column has latitude and longitude swapped

- **What was found:** Each value looks like this (shortened): `{'latitude': '-87.65', 'longitude': '41.94'}`. Chicago's latitude is about 41.9 and its longitude about -87.6, so the labels are the wrong way round. We checked all 196,135 filled rows and every one is swapped. The correct values are already in the `Latitude` and `Longitude` columns.
- **Rationale:** Anyone who trusted this column would plot every restaurant in the wrong place.
- **What to do:** Do not load `Location`. Use `Latitude` and `Longitude`.

### 3. Five columns are completely empty

- **What was found:** `Historical Wards 2003-2015`, `Zip Codes`, `Community Areas`, `Census Tracts` and `Wards` are blank in all 196,825 rows.
- **Rationale:** They add size and confusion and no information.
- **What to do:** Do not load them.

### 4. All the violations are squeezed into one cell

- **What was found:** The `Violations` cell holds every finding for an inspection, separated by ` | `. The average is 4.4 findings and the most is 34. Some cells are 11,620 characters long. 52,266 rows (26.55%) are blank, which looks normal: it is blank for 100% of "Out of Business" inspections and 93% of "No Entry" ones, where no real inspection could take place.
- **Rationale:** You cannot count or search for a single violation, such as "how many inspections found rodents".
- **What to do:** Split it into its own table with one row per finding.

### 5. The city is spelled many different ways

- **What was found:** `City` has 71 different values, but nearly all are Chicago: `CHICAGO` (195,986), `Chicago` (320), `chicago` (97), `CCHICAGO` (46), `CHicago` (12). Ten rows have `CHESTNUT STREET`, which is a street name and not a city.
- **Rationale:** Counting inspections per city would split Chicago into several groups.
- **What to do:** Make it all upper case and fix the typos.

### 6. The same word appears in different capital letters

- **What was found:** `Inspection Type` has 108 values, but only 96 once capitals are ignored (for example `Canvass` and `CANVASS`). `Facility Type` has 491 values, but only 442 once capitals are ignored.
- **Rationale:** Counts for one category get split across several.
- **What to do:** Compare them in lower case and pick one spelling to show.

### 7. A licence number of `0` is not a real number

- **What was found:** 519 rows have `0` in `License #`, and 17 more are blank.
- **Rationale:** Unrelated businesses would look like they share a licence.
- **What to do:** Treat `0` as blank.

### 8. `Risk` has a value that is not a risk level

- **What was found:** Most rows are `Risk 1 (High)` (141,129), `Risk 2 (Medium)` (38,431) or `Risk 3 (Low)` (17,165). But 31 rows say `All`, and 69 are blank.
- **Rationale:** `All` is not a level, so it breaks any sorting or grouping by risk.
- **What to do:** Treat `All` as blank.

## Things that checked out fine

- Every inspection date is a real date, and none has a time of day.
- Every zip code is exactly 5 digits (all 196,775 that are filled in).
- All coordinates are in the Chicago area (latitude 41.64 to 42.02, longitude -87.91 to -87.53).
- `Latitude`, `Longitude` and `Location` are blank on the same 690 rows, so they agree with each other.
- Only 3 rows are outside Illinois.

One more small clean-up: almost all addresses (196,317 of 196,822, or 99.7%) have extra spaces at the start or end. Trim spaces from all text columns when loading.

## Recommended SQL type for each column

For PostgreSQL. Sizes come from the longest value in each column, with some room to spare.

| Column | SQL type | Why |
|--------|----------|-----|
| `Inspection ID` | `INTEGER` | Largest value is 2,352,738. |
| `DBA Name` | `VARCHAR(100)` | Longest is 79 characters. A few names are only digits, so keep it as text. |
| `AKA Name` | `VARCHAR(100)` | Longest is 79. |
| `License #` | `INTEGER` | Largest is 9,999,999. |
| `Facility Type` | `VARCHAR(60)` | Longest is 47. |
| `Risk` | `VARCHAR(20)` | Longest is 15. |
| `Address` | `VARCHAR(60)` | Longest is 40. |
| `City` | `VARCHAR(30)` | Longest is 20. |
| `State` | `CHAR(2)` | Always 2 letters. |
| `Zip` | `CHAR(5)` | A zip code is a label, not a number to add up, so keep it as text. |
| `Inspection Date` | `DATE` | No times of day. |
| `Inspection Type` | `VARCHAR(60)` | Longest is 41. |
| `Results` | `VARCHAR(30)` | Longest is 20. |
| `Violations` | `TEXT` | Up to 11,620 characters. |
| `Latitude` | `DOUBLE PRECISION` | A decimal number. |
| `Longitude` | `DOUBLE PRECISION` | A decimal number. |
| `Location` | not loaded | Swapped values (problem 2). |
| The 5 empty columns | not loaded | Always blank (problem 3). |

## Proposed tables

Two tables. Violations get their own table because one inspection can have up to 34 of them (problem 4). "Nullable" means the column is allowed to be blank. The blank counts below are what the file has today.

### `inspections` (one row per inspection)

| Column | Type | Nullable | Note |
|--------|------|----------|------|
| `inspection_id` | `INTEGER` | no | The key. 196,676 different values once the copies are removed. |
| `dba_name` | `VARCHAR(100)` | no | Never blank. |
| `aka_name` | `VARCHAR(100)` | yes | 2,458 blank. |
| `license_no` | `INTEGER` | yes | 17 blank, plus the 519 zeros turned into blanks (problem 7). |
| `facility_type` | `VARCHAR(60)` | yes | 4,768 blank. Fix capitals (problem 6). |
| `risk` | `VARCHAR(20)` | yes | 69 blank, plus the 31 `All` turned into blanks (problem 8). |
| `address` | `VARCHAR(60)` | yes | 3 blank. |
| `city` | `VARCHAR(30)` | yes | 139 blank. Clean up spelling (problem 5). |
| `state` | `CHAR(2)` | yes | 42 blank. |
| `zip` | `CHAR(5)` | yes | 50 blank. |
| `inspection_date` | `DATE` | no | Never blank. |
| `inspection_type` | `VARCHAR(60)` | yes | 1 blank. Fix capitals (problem 6). |
| `results` | `VARCHAR(30)` | no | Never blank. Only 7 different values. |
| `latitude` | `DOUBLE PRECISION` | yes | 690 blank. |
| `longitude` | `DOUBLE PRECISION` | yes | The same 690 blank. |

### `inspection_violations` (one row per finding)

| Column | Type | Nullable | Note |
|--------|------|----------|------|
| `inspection_id` | `INTEGER` | no | Links to `inspections`. |
| `finding_number` | `SMALLINT` | no | 1 to 34. With `inspection_id`, this is the key. |
| `description` | `TEXT` | no | One finding, cut out of the `Violations` cell at each ` \| `. |

Inspections with a blank `Violations` cell get no rows here. Pulling the violation number out of each description is a later job, and we have not checked that every finding starts with one.

## Columns not to load as they are

| Column | Problem | What to do |
|--------|---------|------------|
| The 5 empty columns | Always blank (problem 3) | Leave out. |
| `Location` | Swapped values (problem 2) | Leave out. Use `Latitude` and `Longitude`. |
| `Violations` | Many findings in one cell (problem 4) | Split into `inspection_violations`. |
| `Inspection ID` | 149 repeated (problem 1) | Remove the copies first. |
| `License #` | `0` is not a real number (problem 7) | Turn `0` into blank. |
| `City` | Many spellings (problem 5) | Upper case, fix typos. |
| `Risk` | Contains `All` (problem 8) | Turn `All` into blank. |
| `Inspection Type`, `Facility Type` | Capital-letter duplicates (problem 6) | Compare in lower case, pick one spelling. |
