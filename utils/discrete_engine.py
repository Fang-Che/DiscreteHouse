"""
WikiHouse Fabrication-Aware Discrete Aggregation Engine
========================================================
Phase 1：Python 離散集合引擎
版本：v2.0（Block 名稱對應 .3dm 圍塊定義）
"""

import numpy as np
import json
from dataclasses import dataclass, field, asdict
from utils.connection_grammar import (
    ASSEMBLY_ORDER,
    validate_configuration,
)

# ══════════════════════════════════════════════
# 常數定義
# ══════════════════════════════════════════════

GRID = 0.6  # 600mm 網格單元

SPAN_GRIDS = {
    "S":    6,
    "M":    8,
    "L":    9,
    "XS":   5,
    "XXXS": 4,
}

WALL_HEIGHT_GRIDS = {
    "S":  3,
    "M":  4,
    "L":  5,
    "XL": 5,
}

WALL_HEIGHT_MM = {
    "S":  2100,
    "M":  2400,
    "L":  2700,
    "XL": 3000,
}

# ── Block 名稱對應表（對應 .3dm 圍塊定義名稱）──
# 格式：程式內部代號 → .3dm 實際圍塊名稱
BLOCK_3DM_NAME = {
    # Floor（XFLOOR 系列）
    "FLOOR_XXXS": "SKYLARK250_XFLOOR-XXS-0",
    "FLOOR_XXS":  "SKYLARK250_XFLOOR-XXS-0",
    "FLOOR_XS":   "SKYLARK250_XFLOOR-XS-0",
    "FLOOR_S":    "SKYLARK250_XFLOOR-S-0",
    "FLOOR_M":    "SKYLARK250_XFLOOR-M-0",
    "FLOOR_L":    "SKYLARK250_XFLOOR-L-0",
    # End
    "END_S":      "SKYLARK250_END-S-0",
    "END_M":      "SKYLARK250_END-M-0",
    "END_L":      "SKYLARK250_END-L-0",
    "END_XS":     "SKYLARK250_END-XS-0",
    "END_XXS":    "SKYLARK250_END-XXS-0",
    # Wall（標準）
    "WALL_S":     "SKYLARK250_WALL-S",
    "WALL_M":     "SKYLARK250_WALL-M",
    "WALL_L":     "SKYLARK250_WALL-L",
    "WALL_XL":    "SKYLARK250_WALL-XL",
    # Corner（SK250 共用 SK200 幾何）
    "CORNER_S":   "SKYLARK200_CORNER-S",
    "CORNER_M":   "SKYLARK200_CORNER-M",
    "CORNER_L":   "SKYLARK200_CORNER-L",
    "CORNER_XL":  "SKYLARK200_CORNER-XL",
    # Door
    "DOOR_S1":    "SKYLARK250_DOOR-S1",
    "DOOR_M1":    "SKYLARK250_DOOR-M1",
    "DOOR_M2":    "SKYLARK250_DOOR-M2",
    "DOOR_L1":    "SKYLARK250_DOOR-L1",
    "DOOR_XL1":   "SKYLARK250_DOOR-XL1",
    # Window
    "WINDOW_S1":  "SKYLARK250_WINDOW-S1",
    "WINDOW_M1":  "SKYLARK250_WINDOW-M1",
    "WINDOW_M2":  "SKYLARK250_WINDOW-M2",
    "WINDOW_M3":  "SKYLARK250_WINDOW-M3",
    "WINDOW_M4":  "SKYLARK250_WINDOW-M4",
    "WINDOW_L1":  "SKYLARK250_WINDOW-L1",
    "WINDOW_XL1": "SKYLARK250_WINDOW-XL1",
    # Roof（平頂/斜頂用 10，山牆用 42）
    "ROOF_S10":   "SKYLARK250_ROOF-S10",
    "ROOF_M10":   "SKYLARK250_ROOF-M10",
    "ROOF_L10":   "SKYLARK250_ROOF-L10",
    "ROOF_XS10":  "SKYLARK250_ROOF-XS10",
    "ROOF_XXS10": "SKYLARK250_ROOF-XXS10",
    "ROOF_S42":   "SKYLARK250_ROOF-S42",
    "ROOF_M42":   "SKYLARK250_ROOF-M42",
    "ROOF_L42":   "SKYLARK250_ROOF-L42",
    # Wall（山牆端牆 G42）
    "WALL_G42_1": "SKYLARK250_WALL-G42-1",
    "WALL_G42_2": "SKYLARK250_WALL-G42-2",
    "WALL_G42_3": "SKYLARK250_WALL-G42-3",
    "WALL_G42_4": "SKYLARK250_WALL-G42-4",
    "WALL_G42_5": "SKYLARK250_WALL-G42-5R",
    "WALL_G42_6": "SKYLARK250_WALL-G42-6",
    # Wall（斜頂 S10）
    "WALL_S10_1": "SKYLARK250_WALL-S10+1",
    "WALL_S10_2": "SKYLARK250_WALL-S10+2",
    "WALL_S10_3": "SKYLARK250_WALL-S10+3",
    "WALL_S10_4": "SKYLARK250_WALL-S10+4",
    "WALL_S10_5": "SKYLARK250_WALL-S10+5",
    # Bowtie
    "BOWTIE_1":   "SKYLARK250_BOWTIE-1",
    "BOWTIE_2":   "SKYLARK250_BOWTIE-2",
}

# Block 類型對應的 category
BLOCK_CATEGORY = {
    "FLOOR": "floor",
    "END":   "end",
    "WALL":  "wall",
    "CORNER":"corner",
    "DOOR":  "window",
    "WINDOW":"window",
    "ROOF":  "roof",
    "BOWTIE":"connector",
}


# ══════════════════════════════════════════════
# 資料結構
# ══════════════════════════════════════════════

@dataclass
class GridPosition:
    x: int
    y: int
    z: int

    def to_mm(self):
        return {
            "x_mm": self.x * 600,
            "y_mm": self.y * 600,
            "z_mm": self.z * 600,
        }

    def to_m(self):
        return {
            "x_m": round(self.x * GRID, 2),
            "y_m": round(self.y * GRID, 2),
            "z_m": round(self.z * GRID, 2),
        }


@dataclass
class PlacedBlock:
    block_id:  str    # .3dm 圍塊定義名稱（例如 SKYLARK250_WALL-M）
    category:  str    # wall / floor / roof / window / corner / end
    series:    str
    name:      str    # 簡短名稱（例如 WALL-M）
    position:  GridPosition
    rotation:  int = 0
    face:      str = ""
    wall_height_mm: int = 2400  # 牆板高度（mm），供 GH 計算 Z offset

    def to_dict(self):
        return {
            "block_id":      self.block_id,
            "category":      self.category,
            "series":        self.series,
            "name":          self.name,
            "position":      asdict(self.position),
            "position_mm":   self.position.to_mm(),
            "position_m":    self.position.to_m(),
            "rotation":      self.rotation,
            "face":          self.face,
            "wall_height_mm": self.wall_height_mm,
        }


@dataclass
class TargetVolume:
    shape:    str
    grids_x:  int
    grids_y:  int
    grids_z:  int
    voxels:   set = field(default_factory=set)

    def contains(self, x, y, z) -> bool:
        return (x, y, z) in self.voxels


# ══════════════════════════════════════════════
# 形體生成器
# ══════════════════════════════════════════════

def make_rectangle(span_str: str, length_grids: int, height_grids: int) -> TargetVolume:
    gx = SPAN_GRIDS.get(span_str, 8)
    gy = length_grids
    gz = height_grids
    voxels = {(x, y, z) for x in range(gx) for y in range(gy) for z in range(gz)}
    return TargetVolume(shape="rectangle", grids_x=gx, grids_y=gy, grids_z=gz, voxels=voxels)


def make_L_shape(span_str: str, length_grids: int,
                 wing_grids_x: int, wing_grids_y: int,
                 height_grids: int) -> TargetVolume:
    gx = SPAN_GRIDS.get(span_str, 8)
    gy = length_grids
    gz = height_grids
    total_x = gx + wing_grids_x
    total_y = max(gy, wing_grids_y)
    voxels = set()
    for x in range(gx):
        for y in range(gy):
            for z in range(gz):
                voxels.add((x, y, z))
    for x in range(gx, total_x):
        for y in range(wing_grids_y):
            for z in range(gz):
                voxels.add((x, y, z))
    return TargetVolume(shape="L", grids_x=total_x, grids_y=total_y, grids_z=gz, voxels=voxels)


def make_U_shape(span_str: str, length_grids: int,
                 court_grids_x: int, court_grids_y: int,
                 height_grids: int) -> TargetVolume:
    gx = SPAN_GRIDS.get(span_str, 8)
    gy = length_grids
    gz = height_grids
    voxels = set()
    cx0 = (gx - court_grids_x) // 2
    cx1 = cx0 + court_grids_x
    cy0 = gy - court_grids_y
    for x in range(gx):
        for y in range(gy):
            for z in range(gz):
                if not (cx0 <= x < cx1 and y >= cy0):
                    voxels.add((x, y, z))
    return TargetVolume(shape="U", grids_x=gx, grids_y=gy, grids_z=gz, voxels=voxels)


def make_arch(span_grids: int, length_grids: int, arch_height_grids: int) -> TargetVolume:
    gx = span_grids
    gy = length_grids
    gz = arch_height_grids
    cx = gx / 2
    r  = gx / 2
    voxels = set()
    for x in range(gx):
        for y in range(gy):
            for z in range(gz):
                dist = ((x + 0.5 - cx) ** 2 + (z + 0.5) ** 2) ** 0.5
                if dist <= r:
                    inner_r = r - 2
                    inner_dist = ((x + 0.5 - cx) ** 2 + (z + 0.5) ** 2) ** 0.5
                    if inner_dist >= inner_r or z == 0:
                        voxels.add((x, y, z))
    return TargetVolume(shape="arch", grids_x=gx, grids_y=gy, grids_z=gz, voxels=voxels)


def make_cross(span_str: str, arm_length: int, height_grids: int) -> TargetVolume:
    gx = SPAN_GRIDS.get(span_str, 8)
    gy = gx
    gz = height_grids
    total_x = gx + arm_length * 2
    total_y = gy + arm_length * 2
    cx0, cx1 = arm_length, arm_length + gx
    cy0, cy1 = arm_length, arm_length + gy
    voxels = set()
    for x in range(total_x):
        for y in range(total_y):
            for z in range(gz):
                if (cx0 <= x < cx1) or (cy0 <= y < cy1):
                    voxels.add((x, y, z))
    return TargetVolume(shape="cross", grids_x=total_x, grids_y=total_y, grids_z=gz, voxels=voxels)


# ══════════════════════════════════════════════
# 離散集合引擎核心
# ══════════════════════════════════════════════

class DiscreteAggregationEngine:

    def __init__(self, series: str = "skylark250",
                 span_str: str = "M",
                 wall_height_str: str = "M",
                 roof_type: str = "flat"):
        self.series          = series
        self.span_str        = span_str
        self.wall_height_str = wall_height_str
        self.roof_type       = roof_type
        self.span_grids      = SPAN_GRIDS.get(span_str, 8)
        self.wall_h_grids    = WALL_HEIGHT_GRIDS.get(wall_height_str, 4)
        self.wall_h_mm       = WALL_HEIGHT_MM.get(wall_height_str, 2400)
        self.placed_blocks:  list = []

    def _get_3dm_name(self, key: str) -> str:
        """取得 .3dm 圍塊定義名稱"""
        name = BLOCK_3DM_NAME.get(key, key)
        return name

    def _get_category(self, key: str) -> str:
        prefix = key.split("_")[0]
        return BLOCK_CATEGORY.get(prefix, "other")

    def _add_block(self, key: str, x: int, y: int, z: int,
                   rotation: int = 0, face: str = ""):
        block_id = self._get_3dm_name(key)
        category = self._get_category(key)
        name     = block_id.replace("SKYLARK250_", "").replace("SKYLARK200_", "")
        self.placed_blocks.append(PlacedBlock(
            block_id=block_id,
            category=category,
            series=self.series,
            name=name,
            position=GridPosition(x, y, z),
            rotation=rotation,
            face=face,
            wall_height_mm=self.wall_h_mm,
        ))

    def generate(self, target: TargetVolume) -> dict:
        self.placed_blocks = []
        self._place_floor(target)
        self._place_walls(target)
        self._place_roof(target)

        bom = self._generate_bom()
        validation_input = [
            {"id": b.block_id, "name": b.name,
             "category": b.category, "series": b.series}
            for b in self.placed_blocks
        ]
        validation = validate_configuration(validation_input, stories=1)

        return {
            "placed_blocks": [b.to_dict() for b in self.placed_blocks],
            "bom":           bom,
            "validation":    validation,
            "target_shape":  target.shape,
            "dimensions": {
                "grids_x":  target.grids_x,
                "grids_y":  target.grids_y,
                "grids_z":  target.grids_z,
                "width_m":  round(target.grids_x * GRID, 2),
                "length_m": round(target.grids_y * GRID, 2),
                "height_m": round(target.grids_z * GRID, 2),
            },
            "config": {
                "series":      self.series,
                "span":        self.span_str,
                "wall_height": self.wall_height_str,
                "roof_type":   self.roof_type,
            }
        }

    def _place_floor(self, target: TargetVolume):
        """Step 1：樓板底盤（XFLOOR + END）"""
        gx = target.grids_x
        gy = target.grids_y
        s  = self.span_str

        floor_key = f"FLOOR_{s}"
        end_key   = f"END_{s}"

        for y in range(gy):
            if any(target.contains(x, y, 0) for x in range(gx)):
                if y == 0 or y == gy - 1:
                    self._add_block(end_key, 0, y, 0, face="floor")
                else:
                    self._add_block(floor_key, 0, y, 0, face="floor")

    def _place_walls(self, target: TargetVolume):
        """Step 2：外牆（Corner → Wall → Door/Window）"""
        gx = target.grids_x
        gy = target.grids_y
        wh = self.wall_height_str

        wall_key   = f"WALL_{wh}"
        corner_key = f"CORNER_{wh}"
        door_key   = f"DOOR_{wh}1"
        win_key    = f"WINDOW_{wh}2"

        corners = set()

        # ── 南面（y=0）──
        for x in range(gx):
            if target.contains(x, 0, 0):
                if x == 0 or x == gx - 1:
                    self._add_block(corner_key, x, 0, 0, rotation=0, face="south")
                    corners.add((x, 0))
                else:
                    mid = gx // 2
                    if x == mid:
                        self._add_block(door_key, x, 0, 0, rotation=0, face="south")
                    else:
                        self._add_block(wall_key, x, 0, 0, rotation=0, face="south")

        # ── 北面（y=gy-1）──
        for x in range(gx):
            if target.contains(x, gy-1, 0):
                if x == 0 or x == gx - 1:
                    if (x, gy-1) not in corners:
                        self._add_block(corner_key, x, gy-1, 0, rotation=180, face="north")
                        corners.add((x, gy-1))
                else:
                    mid = gx // 2
                    if x == mid:
                        self._add_block(win_key, x, gy-1, 0, rotation=180, face="north")
                    else:
                        self._add_block(wall_key, x, gy-1, 0, rotation=180, face="north")

        # ── 西面（x=0）──
        for y in range(1, gy-1):
            if target.contains(0, y, 0) and (0, y) not in corners:
                self._add_block(wall_key, 0, y, 0, rotation=270, face="west")

        # ── 東面（x=gx-1）──
        for y in range(1, gy-1):
            if target.contains(gx-1, y, 0) and (gx-1, y) not in corners:
                total_east = sum(1 for y2 in range(1, gy-1)
                                 if target.contains(gx-1, y2, 0))
                win_positions = {total_east // 3, 2 * total_east // 3}
                rel_y = y - 1
                if rel_y in win_positions:
                    self._add_block(win_key, gx-1, y, 0, rotation=90, face="east")
                else:
                    self._add_block(wall_key, gx-1, y, 0, rotation=90, face="east")

        # ── L/U/Cross 內部邊界 ──
        if target.shape in ["L", "U", "cross"]:
            for x in range(target.grids_x):
                for y in range(target.grids_y):
                    if not target.contains(x, y, 0):
                        continue
                    if not target.contains(x+1, y, 0) and (x, y) not in corners:
                        self._add_block(wall_key, x, y, 0, rotation=90, face="east_inner")
                    if not target.contains(x, y+1, 0) and (x, y) not in corners:
                        self._add_block(wall_key, x, y, 0, rotation=180, face="north_inner")

    def _place_roof(self, target: TargetVolume):
        """Step 3：屋頂"""
        gx = target.grids_x
        gy = target.grids_y
        s  = self.span_str

        if self.roof_type == "gable_42deg":
            roof_key = f"ROOF_{s}42"
        else:
            roof_key = f"ROOF_{s}10"

        for y in range(gy):
            if any(target.contains(x, y, 0) for x in range(gx)):
                self._add_block(roof_key, 0, y, 0, face="top")

    def _generate_bom(self) -> list:
        count_map = {}
        for b in self.placed_blocks:
            key = (b.block_id, b.category, b.series, b.name)
            count_map[key] = count_map.get(key, 0) + 1
        bom = []
        for (block_id, category, series, name), qty in sorted(count_map.items()):
            bom.append({
                "block_id": block_id,
                "category": category,
                "series":   series,
                "name":     name,
                "quantity": qty,
                "assembly_step": ASSEMBLY_ORDER.get(category, {}).get("step", 99),
            })
        bom.sort(key=lambda x: x["assembly_step"])
        return bom


# ══════════════════════════════════════════════
# 便利介面函數
# ══════════════════════════════════════════════

def generate_from_requirements(
    shape: str = "rectangle",
    area_sqm: float = 50.0,
    series: str = "skylark250",
    span_str: str = "M",
    wall_height_str: str = "M",
    roof_type: str = "flat",
    stories: int = 1,
    **kwargs
) -> dict:
    engine = DiscreteAggregationEngine(
        series=series,
        span_str=span_str,
        wall_height_str=wall_height_str,
        roof_type=roof_type,
    )
    span_m = {"S": 3.6, "XS": 3.0, "XXXS": 2.4, "M": 4.8, "L": 5.4}.get(span_str, 4.8)
    length_grids = max(4, round((area_sqm / span_m) / 0.6))
    height_grids = {"S": 3, "M": 4, "L": 5, "XL": 5}.get(wall_height_str, 4)

    if shape == "rectangle":
        target = make_rectangle(span_str, length_grids, height_grids)
    elif shape == "L":
        target = make_L_shape(span_str, length_grids,
                               kwargs.get("wing_grids_x", SPAN_GRIDS.get(span_str, 8) // 2),
                               kwargs.get("wing_grids_y", length_grids // 2),
                               height_grids)
    elif shape == "U":
        target = make_U_shape(span_str, length_grids,
                               kwargs.get("court_grids_x", SPAN_GRIDS.get(span_str, 8) // 2),
                               kwargs.get("court_grids_y", length_grids // 3),
                               height_grids)
    elif shape == "arch":
        target = make_arch(SPAN_GRIDS.get(span_str, 8), length_grids,
                           kwargs.get("arch_height_grids", SPAN_GRIDS.get(span_str, 8) // 2))
    elif shape == "cross":
        target = make_cross(span_str, kwargs.get("arm_length", 4), height_grids)
    else:
        target = make_rectangle(span_str, length_grids, height_grids)

    return engine.generate(target)


def generate_three_schemes(area_sqm: float = 50.0, series: str = "skylark250") -> dict:
    schemes = {}
    configs = [
        ("scheme_a", "S",  "M", "flat",         "方案 A｜保守型", "窄長形、平頂、跨距 3.6m"),
        ("scheme_b", "M",  "M", "sloping_10deg", "方案 B｜標準型", "正方形、斜頂 10°、跨距 4.8m"),
        ("scheme_c", "M",  "M", "gable_42deg",   "方案 C｜進階型", "寬短形、山牆 42°、跨距 4.8m"),
    ]
    for key, span, wh, roof, label, desc in configs:
        result = generate_from_requirements(
            shape="rectangle", area_sqm=area_sqm,
            series=series, span_str=span,
            wall_height_str=wh, roof_type=roof,
        )
        result["label"]       = label
        result["description"] = desc
        result["span"]        = span
        result["roof"]        = roof
        schemes[key] = result
    return schemes


# ══════════════════════════════════════════════
# 測試
# ══════════════════════════════════════════════

if __name__ == "__main__":
    print("=== 測試一：矩形 50m²（SK250 M 跨距 平頂）===")
    result = generate_from_requirements(
        shape="rectangle", area_sqm=50,
        series="skylark250", span_str="M",
        wall_height_str="M", roof_type="flat",
    )
    print(f"尺寸：{result['dimensions']['width_m']}m × {result['dimensions']['length_m']}m")
    print(f"總 Block 數：{len(result['placed_blocks'])}")
    print(f"Grammar 驗證：{'✅' if result['validation']['is_valid'] else '❌'}")
    print("\nBOM（前 10）：")
    for item in result['bom'][:10]:
        print(f"  [{item['assembly_step']}] {item['block_id']} × {item['quantity']}")
    print("\n前 3 個 Block 的 block_id：")
    for p in result['placed_blocks'][:3]:
        print(f"  {p['block_id']} @ {p['position_mm']}")

    print("\n=== 測試四：三方案生成 ===")
    three = generate_three_schemes(area_sqm=50, series="skylark250")
    for key, scheme in three.items():
        valid     = scheme['validation']['is_valid']
        bom_count = sum(b['quantity'] for b in scheme['bom'])
        print(f"  {scheme['label']}：{bom_count} 個 Block，{'✅' if valid else '❌'}")