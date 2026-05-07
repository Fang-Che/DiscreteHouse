import requests
import json

BASE_RAW = "https://raw.githubusercontent.com/wikihouseproject/Skylark/main"
BASE_API = "https://api.github.com/repos/wikihouseproject/Skylark/contents"

SERIES = {
    "SKYLARK250": {
        "series": "skylark250",
        "folders": ["Walls", "Floors", "Roofs", "Connectors", "Stairs",
                    "Windows and doorways"]
    },
    "SKYLARK200": {
        "series": "skylark200",
        "folders": ["Walls", "Floors", "Roofs", "Connectors",
                    "Windows and doorways"]
    }
}

TYPE_MAP = {
    "Walls": "wall",
    "Floors": "floor",
    "Roofs": "roof",
    "Connectors": "connector",
    "Stairs": "stair",
    "Windows and doorways": "window"
}

def fetch_folder(series_folder, sub_folder):
    url = f"{BASE_API}/{series_folder}/{sub_folder}"
    r = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
    if r.status_code != 200:
        print(f"  無法抓取 {url}: {r.status_code}")
        return []
    return [item["name"] for item in r.json() if item["type"] == "dir"]

def build_block(name, series_folder, sub_folder, series_key):
    cat = TYPE_MAP.get(sub_folder, "other")
    iso_url = f"{BASE_RAW}/{series_folder}/{sub_folder}/{name}/{name}_iso.svg"
    cnc_url = f"{BASE_RAW}/{series_folder}/{sub_folder}/{name}/{name}_cnc.svg"

    # 從名稱解析尺寸資訊
    parts = name.split("_")
    label = name.replace(f"{series_folder}_", "").replace("_", " ")

    return {
        "id": name,
        "series": series_key,
        "category": cat,
        "label": label,
        "description": f"WikiHouse Skylark {series_folder} {sub_folder} block",
        "github_folder": f"{series_folder}/{sub_folder}/{name}",
        "iso_svg_url": iso_url,
        "cnc_svg_url": cnc_url,
        "dimensions": {},
        "performance": {},
        "tags": [series_key, cat, sub_folder.lower().replace(" ", "_")]
    }

blocks = []
total = 0

for series_folder, config in SERIES.items():
    series_key = config["series"]
    print(f"\n抓取 {series_folder}...")

    for sub_folder in config["folders"]:
        print(f"  {sub_folder}...")
        names = fetch_folder(series_folder, sub_folder)
        print(f"    找到 {len(names)} 個 blocks")

        for name in names:
            block = build_block(name, series_folder, sub_folder, series_key)
            blocks.append(block)
            total += 1

print(f"\n共抓取 {total} 個 blocks")

output = {
    "_meta": {
        "version": "2.0",
        "source": "wikihouseproject/Skylark GitHub",
        "total_blocks": total
    },
    "blocks": blocks
}

with open("data/blocks_full.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("已儲存到 data/blocks_full.json")