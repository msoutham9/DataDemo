# DataDemo

## Journal Entry Sample Analysis

This repository includes an Excel file (`je_samples.xlsx`) that can be analyzed via
GitHub Actions. The workflow generates basic summary outputs (row counts, date ranges,
and descriptive statistics) and stores them in the `outputs/` directory.

### Run locally

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/analyze_je.py
```

### Run via GitHub Actions

1. Open the **Actions** tab in GitHub.
2. Select **JE Sample Analysis**.
3. Click **Run workflow**.

The workflow uploads the `outputs/` folder as an artifact named
`je-analysis-outputs`. Download it from the workflow run summary to view the
generated `summary.json` and `summary.md` files.
