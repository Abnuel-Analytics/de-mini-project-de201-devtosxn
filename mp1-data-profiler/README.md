# MP1 Data Profiler

Profiles the Chicago Food Inspections CSV and reports on its quality.

Download [the dataset from Kaggle](https://www.kaggle.com/datasets/chicago/chicago-food-inspections), unzip `food-inspections.csv` into `data/` (gitignored), then:

```bash
pip install -r requirements.txt
python profiler.py data/food-inspections.csv
```

Results are written to `output/profile_results.json`.
