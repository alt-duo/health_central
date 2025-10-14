#!/usr/bin/env python3
"""
Update data/report-data.json with real-world data.

Currently implemented:
- ASD trend: Scrape CDC Autism Data & Research page for the ADDM Network
  combined prevalence table (2000–2022), extract "1 in N" values, and convert
  to percentages. Uses simple HTML parsing with BeautifulSoup as a best-effort
  approach. If CDC structure changes, the script will keep existing values.

Placeholders (left static for now):
- ADHD (NSCH) and Dyslexia: retained from prior values until a stable API/CSV
  endpoint is confirmed. You can wire a Socrata dataset or another authoritative
  CSV by extending fetch_adhd() / fetch_dyslexia().
"""
import json
import os
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(ROOT, 'data', 'report-data.json')


CDC_ASD_URL = 'https://www.cdc.gov/autism/data-research/'


def fetch_asd_trend_from_cdc():
    """Fetch ASD trend from CDC page by extracting '1 in N' rows with years.

    Returns list of dicts: [{year: int, percent: float}, ...] sorted by year.
    """
    try:
        resp = requests.get(CDC_ASD_URL, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"WARN: Failed to fetch CDC ASD page: {e}")
        return []

    html = resp.text
    soup = BeautifulSoup(html, 'lxml')

    # Strategy: find occurrences of year followed by '1 in N' within a row-like context
    # This is resilient to minor markup changes.
    text = soup.get_text("\n", strip=True)

    # Example match: "2022 ... 1 in 31"
    pattern = re.compile(r"\b(2000|2002|2004|2006|2008|2010|2012|2014|2016|2018|2020|2022)\b.*?1\s+in\s+(\d+)", re.IGNORECASE | re.DOTALL)
    matches = pattern.findall(text)

    results = {}
    for year_str, n_str in matches:
        try:
            year = int(year_str)
            n = int(n_str)
            percent = round(100.0 / n, 2)
            # keep the highest percent if multiple entries found for same year
            if year not in results or percent > results[year]:
                results[year] = percent
        except Exception:
            continue

    series = [{"year": y, "percent": results[y]} for y in sorted(results.keys())]
    return series


def load_existing():
    try:
        with open(DATA_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # default skeleton if file missing
        return {
            "lastUpdated": "",
            "prevalence": [
                {"condition": "ASD", "percent": 2.78, "note": "ADDM ~1 in 36 (2020)"},
                {"condition": "ADHD", "percent": 9.8, "note": "NSCH 2022 (ever diagnosed)"},
                {"condition": "Dyslexia", "percent": 7.5, "note": "Midpoint of 5–10% range"}
            ],
            "asdTrend": [
                {"year": 2000, "percent": 0.67},
                {"year": 2002, "percent": 0.67},
                {"year": 2004, "percent": 0.80},
                {"year": 2006, "percent": 0.91},
                {"year": 2008, "percent": 1.14},
                {"year": 2010, "percent": 1.47},
                {"year": 2012, "percent": 1.47},
                {"year": 2014, "percent": 1.69},
                {"year": 2016, "percent": 1.85},
                {"year": 2018, "percent": 2.27},
                {"year": 2020, "percent": 2.78}
            ]
        }


def main():
    data = load_existing()

    # Update ASD trend from CDC
    asd_trend_live = fetch_asd_trend_from_cdc()
    if asd_trend_live:
        data['asdTrend'] = asd_trend_live
        # Update ASD point estimate in prevalence to the latest trend value
        latest = max(asd_trend_live, key=lambda x: x['year'])
        for item in data.get('prevalence', []):
            if item.get('condition') == 'ASD':
                item['percent'] = latest['percent']
                item['note'] = f"ADDM 1 in {round(100/ latest['percent']):.0f} ({latest['year']})"
                break

    # Bump lastUpdated
    data['lastUpdated'] = date.today().isoformat()

    # Write back
    os.makedirs(os.path.dirname(DATA_JSON), exist_ok=True)
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Updated {DATA_JSON} with {len(data.get('asdTrend', []))} ASD trend points; lastUpdated={data['lastUpdated']}")


if __name__ == '__main__':
    main()
