"""
WikiHouse Fabrication-Aware Connection Grammar
===============================================
基於 WikiHouse 官方設計指南的形式化組構規則系統

理論定位：Fabrication-Aware Discrete Design Grammar
研究框架：AI-Assisted Design-Manufacture-Assembly (AI-DMA)

官方文件來源：
- WikiHouse Design Guide: https://www.wikihouse.cc/design/designing-for-wikihouse
- How the Structure Works: https://www.wikihouse.cc/design/how-the-structure-works
- WikiHouse Blocks: https://www.wikihouse.cc/design/wikihouse-blocks
- Engineering Guide: https://www.wikihouse.cc/engineering/what-is-skylark

版本：2.0（基於官方文件修正版）
"""

# ══════════════════════════════════════════════
# 第一層：材料與製造約束
# Material & Fabrication Constraints
# ══════════════════════════════════════════════

FABRICATION_CONSTRAINTS = {
    # 板材規格（官方：18mm OSB3）
    "sheet": {
        "material": "OSB3",
        "thickness_mm": 18,
        "standard_size_mm": {"width": 1220, "height": 2440},
        "cnc_tolerance_mm": 0.1,
    },
    # 固定件
    "fixings": {
        "type": "Brad nails",
        "gauge": "15",
        "length_mm": 35,
    },
    # 組裝安全限制（單人可搬運重量上限）
    "assembly": {
        "max_single_person_weight_kg": 25,
        "connector_type": "Bowtie timber ties",
    },
    # SK250 系列規格（官方）
    "skylark250": {
        "wall_depth_mm": 318,
        "insulation_depth_mm": 250,
        "insulation_type": "Mineral wool",
        "service_zone_mm": 32,
        "max_span_mm": 5400,
        "max_stories": 3,
        "u_value_wm2k": 0.14,
        "grid_unit_mm": 600,
        "wall_heights_mm": {
            "S":  2100,
            "M":  2400,
            "L":  2700,
            "XL": 3000,
        },
        # 跨距對應（官方）
        "floor_spans_mm": {
            "S":    3600,
            "M":    4800,
            "L":    5400,
        },
        # 開口尺寸（官方）
        "opening_widths_mm": {
            "XS": 600,
            "S":  1200,
            "M":  1800,
            "L":  2400,
        },
    },
    # SK200 系列規格（官方）
    "skylark200": {
        "wall_depth_mm": 268,
        "insulation_depth_mm": 200,
        "insulation_type": "Mineral wool",
        "service_zone_mm": 32,
        "max_span_mm": 4200,
        "max_stories": 1,
        "u_value_wm2k": 0.17,
        "grid_unit_mm": 600,
        "wall_heights_mm": {
            "S":  2100,
            "M":  2400,
            "L":  2700,
            "XL": 3000,
        },
        # 跨距對應（官方）
        "floor_spans_mm": {
            "XXXS": 2400,
            "XXS":  3000,
            "XS":   3600,
            "S":    4200,
        },
        "opening_widths_mm": {
            "XS": 600,
            "S":  1200,
            "M":  1800,
            "L":  2400,
        },
    },
}


# ══════════════════════════════════════════════
# 第二層：幾何約束
# Geometric Constraints
# ══════════════════════════════════════════════

GEOMETRIC_CONSTRAINTS = {
    # 平面形式（官方：僅允許正交平面）
    "plan_form": "orthogonal_only",
    "curved_forms": False,
    "angular_layouts": False,

    # 網格單元（官方：600mm × 600mm）
    "grid_mm": 600,

    # 垂直高度增量（官方：300mm 倍數）
    "height_increment_mm": 300,

    # 牆板厚度構成
    "wall_composition": {
        "skylark250": {
            "outer_skin_mm": 18,
            "insulation_mm": 250,
            "inner_skin_mm": 18,
            "service_zone_mm": 32,
            "total_mm": 318,
        },
        "skylark200": {
            "outer_skin_mm": 18,
            "insulation_mm": 200,
            "inner_skin_mm": 18,
            "service_zone_mm": 32,
            "total_mm": 268,
        },
    },
}


# ══════════════════════════════════════════════
# 第三層：結構約束
# Structural Constraints
# Source: WikiHouse Design Guide - How the Structure Works
# ══════════════════════════════════════════════

STRUCTURAL_CONSTRAINTS = {

    # 側向支撐規則（官方明確規定）
    # 抵抗風荷載下的側向彎曲
    "lateral_bracing": {
        "single_storey": {
            "description": "單層建築側向支撐規則",
            "option_a": {
                "min_continuous_solid_wall_mm": 1800,
                "min_blocks": 3,
                "max_spacing_mm": 6000,
                "note": "每 6m 至少一段連續 1.8m（3 個 wall block）實心牆"
            },
            "option_b": {
                "min_solid_wall_mm": 1200,
                "min_blocks": 2,
                "segments_required": 2,
                "max_spacing_mm": 6000,
                "note": "每 6m 至少兩段 1.2m（各 2 個 wall block）實心牆"
            },
        },
        "two_storey": {
            "description": "兩層建築側向支撐規則（地面層）",
            "option_a": {
                "min_continuous_solid_wall_mm": 3600,
                "min_blocks": 6,
                "max_spacing_mm": 6000,
                "note": "每 6m 至少一段連續 3.6m（6 個 wall block）實心牆"
            },
            "option_b": {
                "min_solid_wall_mm": 2400,
                "min_blocks": 4,
                "segments_required": 2,
                "max_spacing_mm": 6000,
                "note": "每 6m 至少兩段 2.4m（各 4 個 wall block）實心牆"
            },
        },
        "three_storey": {
            "description": "三層建築需要結構工程師個別評估",
            "requires_engineer": True,
            "note": "除非是連排建築互相支撐，否則不建議使用 Skylark 建造三層建築"
        },
    },

    # 開口規則（官方）
    "opening_rules": {
        "min_solid_between_openings": 1,
        "note": "任何兩個窗或門之間至少需要一個實心牆板",
        "source": "WikiHouse Design Guide - How the structure works",
        "lintel_required": True,
        "lintel_note": "所有開口上方需要過樑，尺寸由結構工程師指定",
    },

    # 跨距規則（官方）
    "span_rules": {
        "note": "跨距形成建築在一個方向的全寬，另一方向可任意延伸",
        "floor_must_rest_on_wall": True,
        "both_ends_required": True,
        "sk250_max_span_mm": 5400,
        "sk200_max_span_mm": 4200,
        "larger_span_note": "超過標準跨距需要在 block 之間加設額外支撐",
    },

    # 屋頂與牆板的連接規則（官方）
    "roof_wall_connection": {
        "floors_and_roofs_provide_lateral_stability": True,
        "avoid_consecutive_rooflights": True,
        "note": "樓板和屋頂提供整體側向穩定，避免連續設置天窗",
    },

    # 系列限制（官方）
    "series_rules": {
        "sk200_single_storey_only": True,
        "sk250_up_to_3_storey": True,
        "no_mixing_series": True,
        "note": "SK200 和 SK250 不能在同一棟建築中混用",
    },
}


# ══════════════════════════════════════════════
# 第四層：屋頂形式規則
# Roof Type Rules
# Source: WikiHouse Design Guide - Designing for WikiHouse
# ══════════════════════════════════════════════

ROOF_TYPES = {
    "flat": {
        "name": "平頂",
        "actual_pitch_degrees": 0.72,
        "pitch_ratio": "1:80",
        "drainage": "single_side",
        "description": "平頂（預工程化 1:80 坡度排水）",
        "compatible_wall_heights": ["S", "M", "L", "XL"],
        "requires_ridge_beam": False,
        "assembly_note": "平頂易於組裝期間上人維修",
        "available_for": ["skylark250", "skylark200"],
    },
    "roof_terrace": {
        "name": "可上人屋頂露台",
        "actual_pitch_degrees": 0,
        "description": "以上層樓板樑作為屋頂樑，形成可上人平台",
        "requires_waterproofing": True,
        "requires_drainage_detail": True,
        "requires_ridge_beam": False,
        "note": "需仔細處理防水和排水細節",
        "available_for": ["skylark250"],
    },
    "sloping_10deg": {
        "name": "單坡斜頂",
        "actual_pitch_degrees": 10,
        "description": "10 度單坡斜頂，適合傳統屋面材料",
        "wall_pairing": {
            "low_side_wall_height": "M",   # 2400mm
            "high_side_wall_height": "XL", # 3000mm
        },
        "requires_ridge_beam": False,
        "available_for": ["skylark250", "skylark200"],
    },
    "gable_42deg": {
        "name": "山牆屋頂",
        "actual_pitch_degrees": 42,
        "description": "傳統山牆屋頂，42 度坡角",
        "compatible_spans": ["M"],
        "compatible_span_mm": 4800,
        "requires_ridge_beam": True,
        "ridge_beam": {
            "width_mm": 90,
            "material": "glulam or LVL",
            "packer": "18mm OSB or plywood each side",
            "depth_note": "深度由結構工程師依跨距和屋頂重量決定",
        },
        "assembly_method": "兩個半片從建築內部向上抬起安裝，可暫時固定於頂點",
        "alternative": "可考慮以鋼拉桿取代脊樑，但安裝較複雜",
        "available_for": ["skylark250"],
    },
}


# ══════════════════════════════════════════════
# 第五層：Block 類型分類
# Block Category Mapping
# ══════════════════════════════════════════════

# 從 Block 名稱判斷類型
BLOCK_CATEGORY_RULES = {
    "wall":      ["WALL"],
    "corner":    ["CORNER"],
    "floor":     ["FLOOR"],
    "end":       ["END"],
    "roof":      ["ROOF"],
    "window":    ["DOOR", "WINDOW", "SKYLIGHT"],
    "stair":     ["STAIR"],
    "trim":      ["VERGE", "LINTEL"],
    "connector": ["TIES"],
}

def get_block_category(block_name: str) -> str:
    """從 Block 名稱判斷其類型"""
    name_upper = block_name.upper()
    for category, keywords in BLOCK_CATEGORY_RULES.items():
        if any(kw in name_upper for kw in keywords):
            return category
    return "other"


# ══════════════════════════════════════════════
# 第六層：連接規則
# Connection Rules
# ══════════════════════════════════════════════

# 每個 Block 類型在六個面上的連接可能性
# None = 封閉面（不可連接）
# 列表 = 可連接的 Block 類型

CONNECTION_RULES = {

    # 樓板（FLOOR / END）
    # 跨距方向水平放置，兩端必須落在牆板上
    "floor": {
        "top":    ["wall", "corner", "window"],  # 上方接牆板（起立牆面）
        "bottom": [None],                         # 底面為地基，不連接
        "left":   ["floor", "end"],              # 沿延伸方向接下一片樓板
        "right":  ["floor", "end"],
        "front":  [None],                         # 跨距端面由牆板圍合
        "back":   [None],
    },

    # 端板（END）：樓板跨距兩端的收邊板
    "end": {
        "top":    ["wall", "corner", "window"],
        "bottom": [None],
        "left":   ["floor"],
        "right":  ["floor"],
        "front":  [None],
        "back":   [None],
    },

    # 標準牆板（WALL）
    # 外牆為承重牆，所有牆板為 CNC 切割的結構構件
    "wall": {
        "top":    ["roof", "floor"],             # 頂面接屋頂或上層樓板
        "bottom": ["floor", "end"],              # 底面必須在樓板或端板上
        "left":   ["wall", "corner", "window"],  # 側面接相鄰牆板、轉角或開口
        "right":  ["wall", "corner", "window"],
        "front":  [None],                         # 厚度方向封閉
        "back":   [None],
    },

    # 轉角柱（CORNER）
    # 用於建築四個角落，連接兩個方向的牆板
    "corner": {
        "top":    ["roof", "floor"],
        "bottom": ["floor", "end"],
        "left":   ["wall", "window"],            # 兩個側面各接一個方向的牆板
        "right":  ["wall", "window"],
        "front":  [None],
        "back":   [None],
    },

    # 開口板（DOOR / WINDOW / SKYLIGHT）
    # 官方規定：兩個開口之間必須至少有一個實心牆板
    "window": {
        "top":    ["roof", "floor"],
        "bottom": ["floor", "end"],
        "left":   ["wall", "corner"],            # 只能接實心牆或轉角，不能接另一個開口
        "right":  ["wall", "corner"],
        "front":  [None],
        "back":   [None],
    },

    # 屋頂板（ROOF）
    # 提供整體側向穩定，不建議連續設置天窗
    "roof": {
        "top":    [None],                         # 外露面
        "bottom": ["wall", "corner"],            # 必須落在牆板或轉角上
        "left":   ["roof", "trim"],              # 沿延伸方向接下一片屋頂或收邊
        "right":  ["roof", "trim"],
        "front":  [None],
        "back":   [None],
    },

    # 收邊板（VERGE）
    "trim": {
        "top":    [None],
        "bottom": ["wall"],
        "left":   ["roof"],
        "right":  [None],
        "front":  [None],
        "back":   [None],
    },

    # 樓梯（STAIR）
    "stair": {
        "top":    ["floor"],
        "bottom": ["floor"],
        "left":   ["wall"],
        "right":  ["wall"],
        "front":  [None],
        "back":   [None],
    },

    # 連接件（TIES / Bowtie）
    # 不參與空間組構，在製造驗證時單獨計算
    "connector": {
        "top": [None], "bottom": [None],
        "left": [None], "right": [None],
        "front": [None], "back": [None],
    },
}


# ══════════════════════════════════════════════
# 第七層：高度相容規則
# Height Compatibility Rules
# ══════════════════════════════════════════════

# 同一排牆板必須高度一致（讓屋頂水平安裝）
HEIGHT_COMPATIBILITY_GROUPS = {
    "S":  {"height_mm": 2100, "compatible": ["WALL-S",  "CORNER-S"]},
    "M":  {"height_mm": 2400, "compatible": ["WALL-M",  "CORNER-M",
                                              "DOOR-M1", "DOOR-M2",
                                              "WINDOW-M1", "WINDOW-M2"]},
    "L":  {"height_mm": 2700, "compatible": ["WALL-L",  "CORNER-L",
                                              "DOOR-L1", "DOOR-L2",
                                              "WINDOW-L1"]},
    "XL": {"height_mm": 3000, "compatible": ["WALL-XL", "CORNER-XL",
                                              "DOOR-XL1"]},
}

# 斜頂特殊配對（官方：低側 M 牆 + 高側 XL 牆）
SLOPING_ROOF_WALL_PAIRING = {
    "sloping_10deg": {
        "low_side_wall_height":  "M",   # 2400mm
        "high_side_wall_height": "XL",  # 3000mm
        "note": "斜頂低側使用 M 高牆板，高側使用 XL 高牆板",
    }
}


# ══════════════════════════════════════════════
# 第八層：跨距相容規則
# Span Compatibility Rules
# ══════════════════════════════════════════════

SPAN_COMPATIBILITY = {
    # SK250 跨距對應
    "skylark250": {
        "FLOOR-S":  {"span_mm": 3600, "compatible_roof_prefix": "ROOF-S"},
        "FLOOR-M":  {"span_mm": 4800, "compatible_roof_prefix": "ROOF-M"},
        "FLOOR-L":  {"span_mm": 5400, "compatible_roof_prefix": "ROOF-L"},
        "END-S":    {"span_mm": 3600},
        "END-M":    {"span_mm": 4800},
        "END-L":    {"span_mm": 5400},
    },
    # SK200 跨距對應
    "skylark200": {
        "FLOOR-XXXS": {"span_mm": 2400},
        "FLOOR-XXS":  {"span_mm": 3000},
        "FLOOR-XS":   {"span_mm": 3600},
        "FLOOR-S":    {"span_mm": 4200},
    },
}


# ══════════════════════════════════════════════
# 第九層：組裝順序約束
# Assembly Sequence Constraints
# Source: WikiHouse General Assembly Guide
# ══════════════════════════════════════════════

ASSEMBLY_ORDER = {
    # Step 1：地基完成後，安裝樓板底盤
    "floor":     {"step": 1, "label": "安裝樓板底盤（Floor cassettes）"},
    "end":       {"step": 1, "label": "安裝端板（End blocks）"},
    # Step 2：豎立周圍牆板（從角落開始）
    "corner":    {"step": 2, "label": "安裝轉角柱（Corner blocks）"},
    "wall":      {"step": 2, "label": "豎立牆板（Wall blocks）"},
    "window":    {"step": 2, "label": "安裝開口板（Door/Window blocks）"},
    # Step 3：安裝樓梯（若有）
    "stair":     {"step": 3, "label": "安裝樓梯（Stair blocks）"},
    # Step 4：安裝屋頂
    "roof":      {"step": 4, "label": "安裝屋頂板（Roof blocks）"},
    # Step 5：收邊
    "trim":      {"step": 5, "label": "安裝收邊板（Verge blocks）"},
    # Step 6：固定連接件
    "connector": {"step": 6, "label": "固定 Bowtie 連接件（Ties）"},
}


# ══════════════════════════════════════════════
# 第十層：硬性禁止規則
# Forbidden Combinations
# （基於官方文件，不可違反）
# ══════════════════════════════════════════════

FORBIDDEN_RULES = [
    {
        "rule_id": "F01",
        "name": "opening_adjacent_to_opening",
        "source": "WikiHouse Design Guide - How the structure works",
        "description": "兩個開口 Block 之間必須至少有一個實心牆板",
        "severity": "error",
        "check": lambda a, b: (
            a.get("category") == "window" and
            b.get("category") == "window"
        ),
    },
    {
        "rule_id": "F02",
        "name": "floor_direct_to_roof",
        "source": "WikiHouse structural logic",
        "description": "樓板上方不能直接接屋頂，中間必須有牆板",
        "severity": "error",
        "check": lambda a, b: (
            a.get("category") == "floor" and
            b.get("category") == "roof"
        ),
    },
    {
        "rule_id": "F03",
        "name": "corner_adjacent_to_corner",
        "source": "WikiHouse structural logic",
        "description": "兩個轉角柱不能相鄰（結構冗餘且無法連接牆板）",
        "severity": "error",
        "check": lambda a, b: (
            a.get("category") == "corner" and
            b.get("category") == "corner"
        ),
    },
    {
        "rule_id": "F04",
        "name": "mixed_series",
        "source": "WikiHouse Design Guide - 200 and 250 series",
        "description": "SK200 和 SK250 不能在同一建築中混用",
        "severity": "error",
        "check": lambda a, b: (
            a.get("series", "") != b.get("series", "") and
            a.get("series", "") != "" and
            b.get("series", "") != ""
        ),
    },
    {
        "rule_id": "F05",
        "name": "sk200_multi_storey",
        "source": "WikiHouse Design Guide - 200 and 250 series",
        "description": "SK200 系列僅適用於單層建築",
        "severity": "error",
        "check": None,  # 需在 validator 層處理
    },
    {
        "rule_id": "F06",
        "name": "gable_roof_wrong_span",
        "source": "WikiHouse Design Guide - Roof shape",
        "description": "山牆屋頂（42°）目前只支援 M 跨距（4.8m）",
        "severity": "error",
        "check": None,  # 需在 validator 層處理
    },
    {
        "rule_id": "F07",
        "name": "three_storey_without_engineer",
        "source": "WikiHouse Design Guide - Form and height",
        "description": "三層建築需要結構工程師審核，除非是連排建築互相支撐",
        "severity": "warning",
        "check": None,
    },
]


# ══════════════════════════════════════════════
# 核心函數
# Core Functions
# ══════════════════════════════════════════════

def get_connectable_categories(block_category: str, face: str) -> list:
    """
    查詢某個 Block 在某個面上可以連接哪些類型的 Block

    參數：
        block_category: block 的類型
        face: 面的方向（top/bottom/left/right/front/back）
    回傳：
        可連接的 block 類型列表，[None] 表示封閉面
    """
    rules = CONNECTION_RULES.get(block_category, {})
    return rules.get(face, [None])


def is_connection_valid(block_a: dict, face_a: str, block_b: dict) -> tuple:
    """
    檢查兩個 Block 之間的連接是否合法

    回傳：(is_valid: bool, rule_id: str, reason: str)
    """
    cat_a = block_a.get("category", "")
    cat_b = block_b.get("category", "")

    # 檢查連接規則
    connectable = get_connectable_categories(cat_a, face_a)
    if None in connectable:
        return False, "C01", f"{cat_a} 的 {face_a} 面是封閉面，不能連接任何 Block"
    if cat_b not in connectable:
        return False, "C02", f"{cat_a} 的 {face_a} 面不能連接 {cat_b} 類型的 Block"

    # 檢查硬性禁止規則
    for rule in FORBIDDEN_RULES:
        if rule["check"] and rule["check"](block_a, block_b):
            return False, rule["rule_id"], rule["description"]

    return True, None, "連接合法"


def validate_configuration(blocks_list: list, stories: int = 1) -> dict:
    """
    驗證一組 Block 配置的合法性

    參數：
        blocks_list: Block 字典列表
        stories: 建築樓層數（影響側向支撐規則）

    回傳：
        {
            "is_valid": bool,
            "errors": [...],
            "warnings": [...],
            "assembly_order": [...],
            "summary": {...},
            "fabrication_notes": [...],
        }
    """
    errors = []
    warnings = []
    fabrication_notes = []

    # 分類 Block
    floor_blocks   = [b for b in blocks_list if b.get("category") in ["floor", "end"]]
    wall_blocks    = [b for b in blocks_list if b.get("category") == "wall"]
    corner_blocks  = [b for b in blocks_list if b.get("category") == "corner"]
    roof_blocks    = [b for b in blocks_list if b.get("category") == "roof"]
    opening_blocks = [b for b in blocks_list if b.get("category") == "window"]
    all_wall_type  = wall_blocks + corner_blocks + opening_blocks

    # ── 硬性錯誤檢查 ──

    # E01：必須有樓板
    if not floor_blocks:
        errors.append({
            "rule_id": "E01",
            "message": "配置中沒有樓板 Block，無法形成有效結構"
        })

    # E02：必須有牆板
    if not all_wall_type:
        errors.append({
            "rule_id": "E02",
            "message": "配置中沒有任何牆板 Block，無法圍合空間"
        })

    # E03：系列一致性（SK200 / SK250 不能混用）
    series_set = set(
        b.get("series", "") for b in blocks_list if b.get("series")
    )
    if len(series_set) > 1:
        errors.append({
            "rule_id": "E03",
            "message": f"配置混用了不同系列 {series_set}，SK200 和 SK250 不能混用"
        })

    # E04：SK200 不能用於多層建築
    if "skylark200" in series_set and stories > 1:
        errors.append({
            "rule_id": "E04",
            "message": "SK200 系列僅適用於單層建築，多層請改用 SK250"
        })

    # E05：連續開口檢查（兩個開口之間必須至少一個實心牆）
    # 簡化檢查：開口比例不超過 50%
    if all_wall_type:
        opening_ratio = len(opening_blocks) / len(all_wall_type)
        if opening_ratio > 0.5:
            errors.append({
                "rule_id": "E05",
                "message": (
                    f"開口比例過高（{opening_ratio:.0%}），"
                    f"超過牆面 50% 會導致兩個開口相鄰，違反官方規定。"
                    f"任何兩個開口之間需至少一個實心牆板。"
                )
            })

    # ── 軟性警告檢查 ──

    # W01：缺少屋頂
    if not roof_blocks:
        warnings.append({
            "rule_id": "W01",
            "message": "配置中沒有屋頂 Block，需要另行規劃屋頂方案"
        })

    # W02：側向支撐（基於官方規則的近似檢查）
    solid_wall_count = len(wall_blocks)
    bracing = STRUCTURAL_CONSTRAINTS["lateral_bracing"]

    if stories == 1:
        min_solid = bracing["single_storey"]["option_a"]["min_blocks"]
        if solid_wall_count < min_solid:
            warnings.append({
                "rule_id": "W02",
                "message": (
                    f"實心牆板數量偏少（{solid_wall_count} 個）。"
                    f"單層建築每 6m 至少需要連續 3 個（1.8m）實心牆板提供側向支撐。"
                    f"建議由結構工程師確認。"
                )
            })
    elif stories == 2:
        min_solid = bracing["two_storey"]["option_a"]["min_blocks"]
        if solid_wall_count < min_solid:
            warnings.append({
                "rule_id": "W02",
                "message": (
                    f"實心牆板數量偏少（{solid_wall_count} 個）。"
                    f"兩層建築每 6m 至少需要連續 6 個（3.6m）實心牆板提供側向支撐。"
                    f"建議由結構工程師確認。"
                )
            })
    elif stories >= 3:
        warnings.append({
            "rule_id": "W03",
            "message": (
                "三層建築需要個別的結構工程師評估。"
                "除非是連排建築互相支撐，官方不建議使用 Skylark 建造三層建築。"
            )
        })

    # W04：三層建築警告
    if stories >= 3:
        warnings.append({
            "rule_id": "W04",
            "message": "所有配置需由結構工程師審核，三層建築尤其需要專業確認"
        })

    # ── 製造備註 ──
    fabrication_notes.append("所有 Block 使用 18mm OSB3 板材，CNC 切割精度 ±0.1mm")
    fabrication_notes.append("Block 之間使用 Bowtie timber ties 連接固定")
    fabrication_notes.append("隔熱材料：礦棉（Mineral wool），安裝於 Block 內部空腔")
    if any("DOOR" in b.get("name", "").upper() or
           "WINDOW" in b.get("name", "").upper()
           for b in blocks_list):
        fabrication_notes.append("所有開口上方需安裝過樑（Lintel），尺寸由結構工程師指定")
    if roof_blocks and any("G42" in b.get("name", "").upper() for b in roof_blocks):
        fabrication_notes.append(
            "山牆屋頂需要 90mm 寬 glulam 或 LVL 脊樑，深度由結構工程師指定"
        )

    # ── 組裝順序 ──
    def get_step(block):
        cat = block.get("category", "other")
        return ASSEMBLY_ORDER.get(cat, {"step": 99})["step"]

    sorted_blocks = sorted(blocks_list, key=get_step)
    assembly_sequence = []
    seen_steps = {}
    for block in sorted_blocks:
        cat = block.get("category", "other")
        step_info = ASSEMBLY_ORDER.get(cat, {"step": 99, "label": "其他"})
        step = step_info["step"]
        if step not in seen_steps:
            seen_steps[step] = len(assembly_sequence)
            assembly_sequence.append({
                "step": step,
                "label": step_info["label"],
                "blocks": [],
            })
        idx = seen_steps[step]
        assembly_sequence[idx]["blocks"].append(block.get("id", block.get("name", "")))

    # ── 統計 ──
    summary = {
        "total_blocks":   len(blocks_list),
        "floor_count":    len(floor_blocks),
        "wall_count":     len(wall_blocks),
        "corner_count":   len(corner_blocks),
        "roof_count":     len(roof_blocks),
        "opening_count":  len(opening_blocks),
        "stories":        stories,
        "series":         list(series_set),
    }

    return {
        "is_valid":          len(errors) == 0,
        "errors":            errors,
        "warnings":          warnings,
        "assembly_order":    assembly_sequence,
        "summary":           summary,
        "fabrication_notes": fabrication_notes,
    }


def format_validation_report(result: dict) -> str:
    """將驗證結果格式化為人類可讀的報告"""
    lines = []
    lines.append("═" * 50)
    lines.append("WikiHouse 配置驗證報告")
    lines.append("═" * 50)

    status = "✅ 合法（可製造）" if result["is_valid"] else "❌ 不合法（需修正）"
    lines.append(f"狀態：{status}")
    lines.append("")

    if result["errors"]:
        lines.append("【錯誤 - 必須修正】")
        for e in result["errors"]:
            lines.append(f"  [{e['rule_id']}] {e['message']}")
        lines.append("")

    if result["warnings"]:
        lines.append("【警告 - 建議確認】")
        for w in result["warnings"]:
            lines.append(f"  [{w['rule_id']}] {w['message']}")
        lines.append("")

    lines.append("【統計】")
    s = result["summary"]
    lines.append(f"  總 Block 數：{s['total_blocks']}")
    lines.append(f"  樓板：{s['floor_count']} | 牆板：{s['wall_count']} | "
                 f"轉角：{s['corner_count']} | 屋頂：{s['roof_count']} | "
                 f"開口：{s['opening_count']}")
    lines.append(f"  樓層：{s['stories']} | 系列：{s['series']}")
    lines.append("")

    lines.append("【組裝順序】")
    for step in result["assembly_order"]:
        lines.append(f"  步驟 {step['step']}：{step['label']}")
        lines.append(f"    Blocks：{', '.join(step['blocks'][:5])}"
                     + ("..." if len(step["blocks"]) > 5 else ""))
    lines.append("")

    lines.append("【製造備註】")
    for note in result["fabrication_notes"]:
        lines.append(f"  • {note}")

    lines.append("═" * 50)
    lines.append("⚠️  最終設計必須由結構工程師審核")
    lines.append("═" * 50)

    return "\n".join(lines)


# ══════════════════════════════════════════════
# 測試
# ══════════════════════════════════════════════

if __name__ == "__main__":

    print("\n=== 測試一：合法的單層兩房配置（SK250）===")
    config_valid = [
        {"id": "SKYLARK250_FLOOR-M-0", "name": "FLOOR-M-0", "category": "floor",   "series": "skylark250"},
        {"id": "SKYLARK250_FLOOR-M-0", "name": "FLOOR-M-0", "category": "floor",   "series": "skylark250"},
        {"id": "SKYLARK250_END-M-0",   "name": "END-M-0",   "category": "end",     "series": "skylark250"},
        {"id": "SKYLARK250_END-M-0",   "name": "END-M-0",   "category": "end",     "series": "skylark250"},
        {"id": "SKYLARK250_CORNER-M",  "name": "CORNER-M",  "category": "corner",  "series": "skylark250"},
        {"id": "SKYLARK250_CORNER-M",  "name": "CORNER-M",  "category": "corner",  "series": "skylark250"},
        {"id": "SKYLARK250_CORNER-M",  "name": "CORNER-M",  "category": "corner",  "series": "skylark250"},
        {"id": "SKYLARK250_CORNER-M",  "name": "CORNER-M",  "category": "corner",  "series": "skylark250"},
        {"id": "SKYLARK250_WALL-M",    "name": "WALL-M",    "category": "wall",    "series": "skylark250"},
        {"id": "SKYLARK250_WALL-M",    "name": "WALL-M",    "category": "wall",    "series": "skylark250"},
        {"id": "SKYLARK250_WALL-M",    "name": "WALL-M",    "category": "wall",    "series": "skylark250"},
        {"id": "SKYLARK250_WALL-M",    "name": "WALL-M",    "category": "wall",    "series": "skylark250"},
        {"id": "SKYLARK250_DOOR-M1",   "name": "DOOR-M1",   "category": "window",  "series": "skylark250"},
        {"id": "SKYLARK250_WINDOW-M1", "name": "WINDOW-M1", "category": "window",  "series": "skylark250"},
        {"id": "SKYLARK250_ROOF-M10",  "name": "ROOF-M10",  "category": "roof",    "series": "skylark250"},
        {"id": "SKYLARK250_ROOF-M10",  "name": "ROOF-M10",  "category": "roof",    "series": "skylark250"},
    ]
    result1 = validate_configuration(config_valid, stories=1)
    print(format_validation_report(result1))

    print("\n=== 測試二：不合法配置（混用系列 + 開口比例過高）===")
    config_invalid = [
        {"id": "SKYLARK250_FLOOR-M-0", "name": "FLOOR-M-0", "category": "floor",  "series": "skylark250"},
        {"id": "SKYLARK200_WALL-M",    "name": "WALL-M",    "category": "wall",   "series": "skylark200"},
        {"id": "SKYLARK250_DOOR-M1",   "name": "DOOR-M1",   "category": "window", "series": "skylark250"},
        {"id": "SKYLARK250_DOOR-M1",   "name": "DOOR-M1",   "category": "window", "series": "skylark250"},
        {"id": "SKYLARK250_DOOR-M1",   "name": "DOOR-M1",   "category": "window", "series": "skylark250"},
    ]
    result2 = validate_configuration(config_invalid, stories=1)
    print(format_validation_report(result2))

    print("\n=== 測試三：連接合法性檢查 ===")
    wall_block   = {"name": "WALL-M",   "category": "wall",   "series": "skylark250"}
    window_block = {"name": "DOOR-M1",  "category": "window", "series": "skylark250"}
    roof_block   = {"name": "ROOF-M10", "category": "roof",   "series": "skylark250"}
    floor_block  = {"name": "FLOOR-M",  "category": "floor",  "series": "skylark250"}

    tests = [
        (wall_block,   "top",    roof_block,   "牆板頂面 → 屋頂"),
        (wall_block,   "left",   window_block, "牆板側面 → 開口板"),
        (window_block, "left",   window_block, "開口板側面 → 開口板（應違規）"),
        (floor_block,  "top",    roof_block,   "樓板頂面 → 屋頂（應違規）"),
        (wall_block,   "front",  roof_block,   "牆板前面 → 屋頂（封閉面，應違規）"),
    ]

    for a, face, b, desc in tests:
        valid, rule_id, reason = is_connection_valid(a, face, b)
        status = "✅" if valid else "❌"
        print(f"  {status} {desc}")
        if not valid:
            print(f"     → [{rule_id}] {reason}")