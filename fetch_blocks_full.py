import requests
import json
import time
import re
from bs4 import BeautifulSoup

BASE = "https://www.wikihouse.cc"
RAW = "https://raw.githubusercontent.com/wikihouseproject/Skylark/main"

SERIES_URLS = {
    "skylark250": (f"{BASE}/blocks/skylark-250", "SKYLARK250"),
    "skylark200": (f"{BASE}/blocks/skylark-200", "SKYLARK200"),
}

CAT_FOLDER = {
    "wall":   "Walls",
    "floor":  "Floors",
    "roof":   "Roofs",
    "window": "Windows and doorways",
    "stair":  "Stairs",
    "trim":   "Verges",
    "other":  "Connectors",
}

def detect_category(name):
    n = name.upper()
    if any(x in n for x in ["WALL", "CORNER"]): return "wall"
    if any(x in n for x in ["FLOOR", "END"]):   return "floor"
    if "ROOF" in n:                              return "roof"
    if any(x in n for x in ["DOOR","WINDOW","SKYLIGHT"]): return "window"
    if "STAIR" in n:                             return "stair"
    if any(x in n for x in ["VERGE","LINTEL"]): return "trim"
    return "other"

def parse_list_page(url, series_key, series_folder):
    print(f"\n抓取列表：{url}")
    r = requests.get(url, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    blocks = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not re.match(r"/(skylark-250|skylark-200)/\S+", href):
            continue
        text = a.get_text(" ", strip=True)
        if not text:
            continue

        slug = href.split("/")[-1]

        # 第一個 token 是 Block 名稱（全大寫字母+數字+符號，無小寫）
        tokens = text.split()
        name = tokens[0]

        # 確認名稱合理（不含小寫字母）
        if re.search(r"[a-z]", name):
            continue
        # 跳過重複
        if any(b["name"] == name and b["series"] == series_key for b in blocks):
            continue

        # 解析尺寸：w318 l918 h1482 或 l600h2400
        dims = {}
        for token in tokens[1:]:
            m = re.match(r"w(\d+)", token)
            if m: dims["width_mm"] = int(m.group(1))
            m = re.match(r"l(\d+)h(\d+)", token)
            if m:
                dims["length_mm"] = int(m.group(1))
                dims["height_mm"] = int(m.group(2))
                continue
            m = re.match(r"l(\d+)", token)
            if m: dims["length_mm"] = int(m.group(1))
            m = re.match(r"h(\d+)", token)
            if m: dims["height_mm"] = int(m.group(1))

        # 描述（去掉名稱和尺寸 token）
        desc_tokens = [t for t in tokens[1:]
                       if not re.match(r"[wlh]\d+", t)]
        description = " ".join(desc_tokens)

        cat = detect_category(name)
        cat_folder = CAT_FOLDER[cat]
        gh_name = f"{series_folder}_{name}"

        # 屋頂相容性
        roof_compat = []
        if "G42" in name.upper(): roof_compat = ["gable_42deg"]
        elif "S10" in name.upper(): roof_compat = ["sloping_10deg"]

        block = {
            "id": gh_name,
            "name": name,
            "series": series_key,
            "category": cat,
            "description": description,
            "slug": slug,
            "page_url": f"{BASE}/skylark-{'250' if '250' in series_key else '200'}/{slug}",
            "dimensions": dims,
            "roof_compatibility": roof_compat,
            "iso_svg_url": f"{RAW}/{series_folder}/{cat_folder}/{gh_name}/{gh_name}_iso.svg",
            "cnc_svg_url": f"{RAW}/{series_folder}/{cat_folder}/{gh_name}/{gh_name}_cnc.svg",
            "download_dxf": f"https://github.wikihouse.cc/Skylark/blob/main/{series_folder}/{cat_folder}/{gh_name}/{gh_name}_cnc.dxf",
            "materials": {},
            "details": {},
            "parts": [],
        }
        blocks.append(block)

    print(f"  解析到 {len(blocks)} 個 blocks")
    return blocks


def fetch_block_detail(block):
    url = block["page_url"]
    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        text_lines = [l.strip() for l in soup.get_text("\n").split("\n") if l.strip()]

        # Parts（格式：WALL-M/A x1）
        parts, in_parts = [], False
        for line in text_lines:
            if line == "Parts": in_parts = True; continue
            if line == "Materials" and in_parts: break
            if in_parts and re.match(r"\S+/\S+\s+x\d+", line):
                parts.append(line)
        block["parts"] = parts

        # Materials
        mat = {}
        for i, line in enumerate(text_lines):
            if line == "Structure"   and i+1 < len(text_lines): mat["structure"]   = text_lines[i+1]
            if line == "Fixings"     and i+1 < len(text_lines): mat["fixings"]     = text_lines[i+1]
            if line == "Insulation"  and i+1 < len(text_lines): mat["insulation"]  = text_lines[i+1]
            if line == "Num"         and i+2 < len(text_lines): mat["sheets"]      = text_lines[i+1]
            if line == "Packs"       and i+1 < len(text_lines): mat["fixings_packs"] = text_lines[i+1]
            if line == "Area"        and i+1 < len(text_lines): mat["insulation_area_m2"] = text_lines[i+1]
        block["materials"] = mat

        # Details
        det = {}
        for i, line in enumerate(text_lines):
            if line == "System"        and i+1 < len(text_lines): det["system"]       = text_lines[i+1]
            if line == "Typical cost"  and i+1 < len(text_lines): det["cost"]         = text_lines[i+1]
            if line == "Typical weight"and i+1 < len(text_lines): det["weight_kg"]    = text_lines[i+1]
            if line == "Typical carbon"and i+1 < len(text_lines): det["carbon_kgco2"] = text_lines[i+1]
        block["details"] = det

    except Exception as e:
        print(f"    錯誤 {block['name']}: {e}")

    return block


# ── 主程式 ──
all_blocks = []

for series_key, (url, series_folder) in SERIES_URLS.items():
    blocks = parse_list_page(url, series_key, series_folder)
    print(f"開始抓取 {series_key} 詳細資料...")
    for i, block in enumerate(blocks):
        print(f"  {i+1}/{len(blocks)} {block['name']}")
        block = fetch_block_detail(block)
        all_blocks.append(block)
        time.sleep(0.3)

output = {
    "_meta": {
        "version": "3.1",
        "source": "wikihouse.cc + github.com/wikihouseproject/Skylark",
        "total_blocks": len(all_blocks)
    },
    "blocks": all_blocks
}

with open("data/blocks_full.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n完成！共 {len(all_blocks)} 個 blocks 儲存至 data/blocks_full.json")