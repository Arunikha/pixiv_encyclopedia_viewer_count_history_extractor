# [Pixiv Encyclopedia Viewer History Extractor](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor "Pixiv Encyclopedia Viewer History Extractor")

[![Python](https://img.shields.io/badge/python-3.9|%203.10%20|%203.11|%203.12|%203.13-blue)](https://www.python.org/)
[![OS](https://img.shields.io/badge/OS-Linux%20%7C%20macOS%20%7C%20Windows-blue)]
[![CodeQL Advanced](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor/actions/workflows/codeql.yml/badge.svg)](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor/actions/workflows/codeql.yml)
[![Python Lint](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor/actions/workflows/lint.yml/badge.svg)](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor/actions/workflows/lint.yml)
[![Pytest](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor/actions/workflows/pytest.yml/badge.svg)](https://github.com/europanite/pixiv_encyclopedia_viewer_count_history_extractor/actions/workflows/pytest.yml)

!["web_ui"](./assets/images/web_ui.png)

An Extraction Tool for Pixiv Encyclopedia Viewer Count History

## Japanese README

日本語版はこちら [`README.ja.md`](README.ja.md).

---

## Overview

Extract daily view history data from a [Pixiv Encyclopedia (pixiv百科事典)](https://dic.pixiv.net/) article.

Pixiv Encyclopedia viewer history is a nice real-world time-series dataset.

It often shows:
- Weekly seasonality (weekday vs weekend traffic)
- Occasional spikes caused by events or social media buzz

You can use the extracted CSV as sample data for:
- Time-series visualization and smoothing
- Seasonal decomposition
- Forecasting models (ARIMA, Prophet, etc.)


> ⚠️ **Unofficial tool**  
> This project is not affiliated with or endorsed by Pixiv.  
> Please follow Pixiv's Terms of Use and robots.txt when using this script.

## Features

- Fetch by **article title** (e.g., `"ブルーアーカイブ"`) directly from Pixiv Encyclopedia
- Or read from a **local HTML file**
- Output **JSON Lines** to stdout  
  (one `{"date": "...","count": ...}` per line)
- Optional **CSV export** via `--csv output.csv`

---

## Requirements

- Python 3.9+
- Dependencies:
  - `requests`
  - `beautifulsoup4`

---

## Usage

### 0. Create virtual environment

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 1. Fetch by article title

```bash
python src/extract_viewer_history.py "ブルーアーカイブ"
```

This will:

- Download `https://dic.pixiv.net/a/ブルーアーカイブ`
- Parse the embedded JSON
- Print one JSON object per line to stdout:

```json
{"date": "2025-07-01", "count": 9454605}
{"date": "2025-07-02", "count": 9331510}
{"date": "2025-07-03", "count": 8884117}
...
```

You can redirect it to a file:

```bash
python src/extract_viewer_history.py "ブルーアーカイブ" > ブルーアーカイブ.jsonl
```

### 2. Export as CSV

Use the `--csv` option to write a CSV file while still printing JSON to stdout:

```bash
python src/extract_viewer_history.py "ブルーアーカイブ" --csv ブルーアーカイブ.csv
```

Example CSV content:

```csv
date,count
2025-07-01,9454605
2025-07-02,9331510
2025-07-03,8884117
...
```

### 3. Use a local HTML file

If you have already saved the article HTML:

```bash
python src/extract_viewer_history.py ブルーアーカイブ.html
python src/extract_viewer_history.py ブルーアーカイブ.html --csv ブルーアーカイブ.csv
```

The script will detect that `ブルーアーカイブ.html` is a file and will parse it instead of fetching from the web.

---

### 4. Test

```bash
pip install -r requirements.test.txt
pytest
```

### 5. Deactivate environment

```bash
deactivate
```

---

## Notes / Limitations

- No rate limiting is implemented; please:
  - Use it responsibly
  - Avoid sending many requests in a short time
- This is a simple utility script, primarily intended for personal analysis or research.

---

## License
- Apache License 2.0
