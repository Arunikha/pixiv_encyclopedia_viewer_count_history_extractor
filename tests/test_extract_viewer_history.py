import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest

# --- Make src/ importable as a module -----------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import extract_viewer_history as ev  # noqa: E402


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _build_html_with_next_data(tag_counts: Any) -> str:
    """Build minimal HTML with __NEXT_DATA__ for testing."""
    payload = {
        "props": {
            "pageProps": {
                "swrFallback": {
                    "/some/get_graph_data": {
                        "tagCounts": tag_counts,
                    }
                }
            }
        }
    }
    script = json.dumps(payload, ensure_ascii=False)
    return f"""
    <html>
      <head>
        <script id="__NEXT_DATA__" type="application/json">
        {script}
        </script>
      </head>
      <body></body>
    </html>
    """


# ------------------------------------------------------------------
# extract_viewer_history_from_html
# ------------------------------------------------------------------
def test_extract_viewer_history_from_html_list():
    tag_counts = [
        {"date": "2025-07-01", "count": 141},
        {"date": "2025-07-02", "count": 132},
    ]
    html = _build_html_with_next_data(tag_counts)

    result = ev.extract_viewer_history_from_html(html)

    assert result == tag_counts
    assert all("date" in r and "count" in r for r in result)


def test_extract_viewer_history_from_html_json_string():
    tag_counts = [
        {"date": "2025-08-01", "count": 72},
        {"date": "2025-08-02", "count": 98},
    ]
    html = _build_html_with_next_data(json.dumps(tag_counts, ensure_ascii=False))

    result = ev.extract_viewer_history_from_html(html)

    assert result == tag_counts


def test_extract_viewer_history_from_html_missing_next_data():
    html = "<html><body>No next data</body></html>"

    with pytest.raises(ValueError, match="__NEXT_DATA__ script tag not found"):
        ev.extract_viewer_history_from_html(html)


def test_extract_viewer_history_from_html_missing_tag_counts():
    payload = {
        "props": {
            "pageProps": {
                "swrFallback": {
                    "/some/get_graph_data": {
                    }
                }
            }
        }
    }
    script = json.dumps(payload)
    html = f"""
    <html>
      <head>
        <script id="__NEXT_DATA__" type="application/json">
        {script}
        </script>
      </head>
      <body></body>
    </html>
    """

    with pytest.raises(ValueError, match="tagCounts"):
        ev.extract_viewer_history_from_html(html)


# ------------------------------------------------------------------
# export_to_csv
# ------------------------------------------------------------------
def test_export_to_csv(tmp_path: Path):
    series: List[Dict[str, Any]] = [
        {"date": "2025-07-01", "count": 141},
        {"date": "2025-07-02", "count": 132},
    ]
    csv_path = tmp_path / "out.csv"

    ev.export_to_csv(series, str(csv_path))

    content = csv_path.read_text(encoding="utf-8").splitlines()
    assert content[0] == "date,count"
    assert "2025-07-01,141" in content
    assert "2025-07-02,132" in content


# ------------------------------------------------------------------
# parse_cli_args
# ------------------------------------------------------------------
def test_parse_cli_args_minimal():
    title, csv_path = ev.parse_cli_args(["ブルーアーカイブ"])
    assert title == "ブルーアーカイブ"
    assert csv_path is None


def test_parse_cli_args_with_csv():
    title, csv_path = ev.parse_cli_args(
        ["ブルーアーカイブ", "--csv", "viewer_history.csv"]
    )
    assert title == "ブルーアーカイブ"
    assert csv_path == "viewer_history.csv"


def test_parse_cli_args_missing_required():
    with pytest.raises(ValueError):
        ev.parse_cli_args([])


def test_parse_cli_args_unknown_option_warns(capsys):
    title, csv_path = ev.parse_cli_args(["title", "--unknown", "foo"])
    captured = capsys.readouterr()
    assert "unknown argument ignored" in captured.err
    assert title == "title"
    assert csv_path is None


# ------------------------------------------------------------------
# load_html
# ------------------------------------------------------------------
def test_load_html_uses_local_file_when_exists(tmp_path: Path):
    html_file = tmp_path / "sample.html"
    html_file.write_text("<html>local</html>", encoding="utf-8")

    result = ev.load_html(str(html_file))

    assert result == "<html>local</html>"


def test_load_html_fetches_remote_when_file_not_found(monkeypatch):
    calls = {}

    def fake_get(url, headers=None):
        calls["url"] = url
        calls["headers"] = headers

        class Resp:
            status_code = 200
            apparent_encoding = "utf-8"
            text = "<html>remote</html>"

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setattr(ev.requests, "get", fake_get)

    title = "テスト記事"
    html = ev.load_html(title)

    from urllib.parse import quote

    expected_url = ev.PIXIV_DIC_BASE_URL + quote(title, safe="")
    assert calls["url"] == expected_url
    assert "<html>remote</html>" == html
    # User-Agent 
    assert "User-Agent" in calls["headers"]


# ------------------------------------------------------------------
# main (integration-ish)
# ------------------------------------------------------------------
def test_main_prints_json_and_calls_csv(tmp_path: Path, monkeypatch, capsys):
    fake_series = [{"date": "2025-01-01", "count": 1}]

    monkeypatch.setattr(ev, "load_html", lambda arg: "<html>dummy</html>")
    monkeypatch.setattr(
        ev,
        "extract_viewer_history_from_html",
        lambda html: fake_series,
    )

    csv_calls = {}

    def fake_export_to_csv(series, csv_path):
        csv_calls["series"] = series
        csv_calls["csv_path"] = csv_path

    monkeypatch.setattr(ev, "export_to_csv", fake_export_to_csv)

    csv_path = tmp_path / "out.csv"
    ev.main(["テスト記事", "--csv", str(csv_path)])

    captured = capsys.readouterr()
    assert '{"date": "2025-01-01", "count": 1}' in captured.out
    assert csv_calls["series"] == fake_series
    assert csv_calls["csv_path"] == str(csv_path)
