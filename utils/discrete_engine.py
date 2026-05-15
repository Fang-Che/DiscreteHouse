"""
WikiHouse Fabrication-Aware Discrete Aggregation Engine
========================================================
版本：v4.1（修正實際建築尺寸計算）

尺寸修正（BoundingBox 實測確認）：
  實際建築寬度 = gx×600 - 2×(600-318) = gx×600 - 564mm
  實際建築長度 = gy×600 - 564mm
  東面 x_mm   = gx×600 - 564
  北面 y_mm   = gy×600 - 564
  length_grids 計算需扣掉兩端 CORNER（各318mm）

插入點規律（BoundingBox 實測確認）：
  WALL   rot=0/180 : insert_x = 格點左邊緣 + 300（中心），z = -wall_h
  WALL   rot=90/270: insert_y = 格點左邊緣 + 300（中心），z = -wall_h
  DOOR   rot=0     : insert_x = 格點右邊緣（+1200），y = +318，z = -300
  WINDOW rot=90    : insert_y = 格點左邊緣 + 600（中心），z = -wall_h

CORNER 旋轉與偏移（實測確認）：
  rotation=0  (南面左/西面下): (+268, +25)
  rotation=90 (南面右/東面下): (-589, +268)
  rotation=180(北面右/東面上): (-832, -589)
  rotation=270(北面左/西面上): (+25,  -268)
"""

import json
from dataclasses import dataclass, field
from utils.connection_grammar import ASSEMBLY_ORDER, validate_configuration

# ══════════════════════════════════════════════
# 常數
# ══════════════════════════════════════════════

GRID = 0.6

SPAN_GRIDS     = {"S": 6, "M": 8, "L": 9, "XS": 5, "XXXS": 4}
WALL_HEIGHT_MM = {"S": 2100, "M": 2400, "L": 2700, "XL": 3000}
WALL_HEIGHT_GRIDS = {"S": 3, "M": 4, "L": 5, "XL": 5}

BLOCK_3DM_NAME = {
    "FLOOR_XXXS": "SKYLARK250_XFLOOR-XXS-0",
    "FLOOR_XXS":  "SKYLARK250_XFLOOR-XXS-0",
    "FLOOR_XS":   "SKYLARK250_XFLOOR-XS-0",
    "FLOOR_S":    "SKYLARK250_XFLOOR-S-0",
    "FLOOR_M":    "SKYLARK250_XFLOOR-M-0",
    "FLOOR_L":    "SKYLARK250_XFLOOR-L-0",
    "END_S":      "SKYLARK250_END-S-0",
    "END_M":      "SKYLARK250_END-M-0",
    "END_L":      "SKYLARK250_END-L-0",
    "END_XS":     "SKYLARK250_END-XS-0",
    "END_XXS":    "SKYLARK250_END-XXS-0",
    "WALL_S":     "SKYLARK250_WALL-S",
    "WALL_M":     "SKYLARK250_WALL-M",
    "WALL_L":     "SKYLARK250_WALL-L",
    "WALL_XL":    "SKYLARK250_WALL-XL",
    "CORNER_S":   "SKYLARK200_CORNER-S",
    "CORNER_M":   "SKYLARK200_CORNER-M",
    "CORNER_L":   "SKYLARK200_CORNER-L",
    "CORNER_XL":  "SKYLARK200_CORNER-XL",
    "DOOR_S1":    "SKYLARK250_DOOR-S1",
    "DOOR_M1":    "SKYLARK250_DOOR-M1",
    "DOOR_M2":    "SKYLARK250_DOOR-M2",
    "DOOR_L1":    "SKYLARK250_DOOR-L1",
    "DOOR_XL1":   "SKYLARK250_DOOR-XL1",
    "WINDOW_S1":  "SKYLARK250_WINDOW-S1",
    "WINDOW_M1":  "SKYLARK250_WINDOW-M1",
    "WINDOW_M2":  "SKYLARK250_WINDOW-M2",
    "WINDOW_M3":  "SKYLARK250_WINDOW-M3",
    "WINDOW_M4":  "SKYLARK250_WINDOW-M4",
    "WINDOW_L1":  "SKYLARK250_WINDOW-L1",
    "WINDOW_XL1": "SKYLARK250_WINDOW-XL1",
    "ROOF_S10":   "SKYLARK250_ROOF-S10",
    "ROOF_M10":   "SKYLARK250_ROOF-M10",
    "ROOF_L10":   "SKYLARK250_ROOF-L10",
    "ROOF_XS10":  "SKYLARK250_ROOF-XS10",
    "ROOF_XXS10": "SKYLARK250_ROOF-XXS10",
    "ROOF_S42":   "SKYLARK250_ROOF-S42",
    "ROOF_M42":   "SKYLARK250_ROOF-M42",
    "ROOF_L42":   "SKYLARK250_ROOF-L42",
    "WALL_G42_1": "SKYLARK250_WALL-G42-1",
    "WALL_G42_5": "SKYLARK250_WALL-G42-5R",
    "BOWTIE_1":   "SKYLARK250_BOWTIE-1",
    "BOWTIE_2":   "SKYLARK250_BOWTIE-2",
}

BLOCK_CATEGORY = {
    "FLOOR": "floor", "END": "end", "WALL": "wall", "CORNER": "corner",
    "DOOR": "window", "WINDOW": "window", "ROOF": "roof", "BOWTIE": "connector",
}

BLOCK_INSERT = {
    "WALL_S":     {"w": 600,  "off": 300},
    "WALL_M":     {"w": 600,  "off": 300},
    "WALL_L":     {"w": 600,  "off": 300},
    "WALL_XL":    {"w": 600,  "off": 300},
    "DOOR_S1":    {"w": 1200, "off": 1200, "y_off": 318, "z_off": -300},
    "DOOR_M1":    {"w": 1200, "off": 1200, "y_off": 318, "z_off": -300},
    "DOOR_M2":    {"w": 2400, "off": 2400, "y_off": 318, "z_off": -300},
    "DOOR_L1":    {"w": 1200, "off": 1200, "y_off": 318, "z_off": -300},
    "DOOR_XL1":   {"w": 1200, "off": 1200, "y_off": 318, "z_off": -300},
    "WINDOW_S1":  {"w": 600,  "off": 300,  "z_off": -2400},
    "WINDOW_M1":  {"w": 600,  "off": 300,  "z_off": -2400},
    "WINDOW_M2":  {"w": 1200, "off": 600,  "z_off": -2400},
    "WINDOW_M3":  {"w": 600,  "off": 300,  "z_off": -2400},
    "WINDOW_M4":  {"w": 1200, "off": 600,  "z_off": -2400},
    "WINDOW_L1":  {"w": 600,  "off": 300,  "z_off": -2400},
    "WINDOW_XL1": {"w": 1200, "off": 600,  "z_off": -2400},
}

# CORNER 插入點偏移（以牆面端點格點座標 mm 為基準，實測確認）
CORNER_OFFSET = {
    0:   (+268, +25),   # 南面左角 / 西面下角
    90:  (-25,  +268),  # 南面右角 / 東面下角
    180: (-268, -25),   # 北面右角 / 東面上角
    270: (+25,  -268),  # 北面左角 / 西面上角
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
        return {"x_mm": self.x, "y_mm": self.y, "z_mm": self.z}

    def to_m(self):
        return {"x_m": round(self.x/1000,3), "y_m": round(self.y/1000,3), "z_m": round(self.z/1000,3)}


@dataclass
class PlacedBlock:
    block_id: str
    category: str
    series:   str
    name:     str
    position: GridPosition
    rotation: int = 0
    face:     str = ""
    wall_height_mm: int = 2400

    def to_dict(self):
        return {
            "block_id":       self.block_id,
            "category":       self.category,
            "series":         self.series,
            "name":           self.name,
            "position_mm":    self.position.to_mm(),
            "position_m":     self.position.to_m(),
            "rotation":       self.rotation,
            "face":           self.face,
            "wall_height_mm": self.wall_height_mm,
        }


@dataclass
class TargetVolume:
    shape:   str
    grids_x: int
    grids_y: int
    grids_z: int
    voxels:  set = field(default_factory=set)

    def contains(self, x, y, z) -> bool:
        return (x, y, z) in self.voxels


# ══════════════════════════════════════════════
# 形體生成器
# ══════════════════════════════════════════════

def make_rectangle(span_str, length_grids, height_grids):
    gx = SPAN_GRIDS.get(span_str, 8)
    voxels = {(x,y,z) for x in range(gx) for y in range(length_grids) for z in range(height_grids)}
    return TargetVolume("rectangle", gx, length_grids, height_grids, voxels)


def make_L_shape(span_str, length_grids, wing_grids_x, wing_grids_y, height_grids):
    gx = SPAN_GRIDS.get(span_str, 8)
    total_x = gx + wing_grids_x
    total_y = max(length_grids, wing_grids_y)
    voxels = set()
    for x in range(gx):
        for y in range(length_grids):
            for z in range(height_grids): voxels.add((x,y,z))
    for x in range(gx, total_x):
        for y in range(wing_grids_y):
            for z in range(height_grids): voxels.add((x,y,z))
    return TargetVolume("L", total_x, total_y, height_grids, voxels)


def make_U_shape(span_str, length_grids, court_grids_x, court_grids_y, height_grids):
    gx = SPAN_GRIDS.get(span_str, 8)
    cx0 = (gx - court_grids_x) // 2
    cx1 = cx0 + court_grids_x
    cy0 = length_grids - court_grids_y
    voxels = set()
    for x in range(gx):
        for y in range(length_grids):
            for z in range(height_grids):
                if not (cx0 <= x < cx1 and y >= cy0):
                    voxels.add((x,y,z))
    return TargetVolume("U", gx, length_grids, height_grids, voxels)


def make_cross(span_str, arm_length, height_grids):
    gx = SPAN_GRIDS.get(span_str, 8)
    total = gx + arm_length * 2
    cx0, cx1 = arm_length, arm_length + gx
    voxels = set()
    for x in range(total):
        for y in range(total):
            for z in range(height_grids):
                if (cx0 <= x < cx1) or (cx0 <= y < cx1):
                    voxels.add((x,y,z))
    return TargetVolume("cross", total, total, height_grids, voxels)


# ══════════════════════════════════════════════
# 離散集合引擎
# ══════════════════════════════════════════════

class DiscreteAggregationEngine:

    def __init__(self, series="skylark250", span_str="M",
                 wall_height_str="M", roof_type="flat"):
        self.series          = series
        self.span_str        = span_str
        self.wall_height_str = wall_height_str
        self.roof_type       = roof_type
        self.span_grids      = SPAN_GRIDS.get(span_str, 8)
        self.wall_h_grids    = WALL_HEIGHT_GRIDS.get(wall_height_str, 4)
        self.wall_h_mm       = WALL_HEIGHT_MM.get(wall_height_str, 2400)
        self.placed_blocks   = []

    # ── 內部工具 ──────────────────────────────────

    def _get_3dm_name(self, key):
        return BLOCK_3DM_NAME.get(key, key)

    def _get_category(self, key):
        return BLOCK_CATEGORY.get(key.split("_")[0], "other")

    def _add(self, key, x, y, z=0, rotation=0, face=""):
        block_id = self._get_3dm_name(key)
        category = self._get_category(key)
        name = block_id.replace("SKYLARK250_","").replace("SKYLARK200_","")
        self.placed_blocks.append(PlacedBlock(
            block_id=block_id, category=category, series=self.series,
            name=name, position=GridPosition(int(x), int(y), int(z)),
            rotation=rotation, face=face, wall_height_mm=self.wall_h_mm,
        ))

    # ── 主入口 ────────────────────────────────────

    def generate(self, target):
        self.placed_blocks = []
        self._place_floor(target)
        self._place_walls(target)
        self._place_roof(target)

        bom = self._generate_bom()
        vi  = [{"id": b.block_id, "name": b.name,
                "category": b.category, "series": b.series}
               for b in self.placed_blocks]
        validation = validate_configuration(vi, stories=1)

        return {
            "placed_blocks": [b.to_dict() for b in self.placed_blocks],
            "bom": bom,
            "validation": validation,
            "target_shape": target.shape,
            "dimensions": {
                "grids_x": target.grids_x, "grids_y": target.grids_y, "grids_z": target.grids_z,
                "width_m":  round(target.grids_x * GRID, 2),
                "length_m": round(target.grids_y * GRID, 2),
                "height_m": round(target.grids_z * GRID, 2),
            },
            "config": {
                "series": self.series, "span": self.span_str,
                "wall_height": self.wall_height_str, "roof_type": self.roof_type,
            }
        }

    # ── Step 1：樓板 ──────────────────────────────

    def _place_floor(self, target):
        gx, gy = target.grids_x, target.grids_y
        s = self.span_str
        for y in range(gy):
            if any(target.contains(x, y, 0) for x in range(gx)):
                key = f"END_{s}" if (y == 0 or y == gy-1) else f"FLOOR_{s}"
                self._add(key, 0, y*600, 0, face="floor")

    # ── Step 2：外牆（v4.0 Voxel 邊界偵測）────────

    def _place_walls(self, target):
        wh       = self.wall_height_str
        wall_key = f"WALL_{wh}"
        door_key = f"DOOR_{wh}1"
        win_key  = f"WINDOW_{wh}2"
        corn_key = f"CORNER_{wh}"

        G  = 600      # 格點 mm
        CW = 318      # CORNER 幾何寬度 mm
        wz = -self.wall_h_mm
        DW = BLOCK_INSERT.get(door_key, {}).get("w", 1200)
        WW = BLOCK_INSERT.get(win_key,  {}).get("w", 1200)

        # ── 偵測外牆段 ──────────────────────────────
        # x_segs: (gy_wall, gx_start, gx_end, direction)  南/北面
        # y_segs: (gx_wall, gy_start, gy_end, direction)  東/西面
        x_segs, y_segs = [], []

        for gy_i in range(target.grids_y):
            # 南面：格點存在且南鄰不存在
            seg = None
            for gx_i in range(target.grids_x):
                if target.contains(gx_i, gy_i, 0) and not target.contains(gx_i, gy_i-1, 0):
                    if seg is None: seg = gx_i
                    end = gx_i + 1
                else:
                    if seg is not None:
                        x_segs.append((gy_i, seg, end, 'south'))
                        seg = None
            if seg is not None: x_segs.append((gy_i, seg, end, 'south'))

            # 北面：格點存在且北鄰不存在
            seg = None
            for gx_i in range(target.grids_x):
                if target.contains(gx_i, gy_i, 0) and not target.contains(gx_i, gy_i+1, 0):
                    if seg is None: seg = gx_i
                    end = gx_i + 1
                else:
                    if seg is not None:
                        x_segs.append((gy_i+1, seg, end, 'north'))
                        seg = None
            if seg is not None: x_segs.append((gy_i+1, seg, end, 'north'))

        for gx_i in range(target.grids_x):
            # 西面：格點存在且西鄰不存在
            seg = None
            for gy_i in range(target.grids_y):
                if target.contains(gx_i, gy_i, 0) and not target.contains(gx_i-1, gy_i, 0):
                    if seg is None: seg = gy_i
                    end = gy_i + 1
                else:
                    if seg is not None:
                        y_segs.append((gx_i, seg, end, 'west'))
                        seg = None
            if seg is not None: y_segs.append((gx_i, seg, end, 'west'))

            # 東面：格點存在且東鄰不存在
            seg = None
            for gy_i in range(target.grids_y):
                if target.contains(gx_i, gy_i, 0) and not target.contains(gx_i+1, gy_i, 0):
                    if seg is None: seg = gy_i
                    end = gy_i + 1
                else:
                    if seg is not None:
                        y_segs.append((gx_i+1, seg, end, 'east'))
                        seg = None
            if seg is not None: y_segs.append((gx_i+1, seg, end, 'east'))

        # ── 主南面（放 DOOR 的牆段）──────────────────
        s0 = [(gy_i,s,e,d) for gy_i,s,e,d in x_segs if d=='south' and gy_i==0]
        main_south = max(s0, key=lambda t: t[2]-t[1]) if s0 else None

        # ── CORNER 去重 ──────────────────────────────
        placed_corners = set()

        def corner_once(x_mm, y_mm, rotation):
            dx, dy = CORNER_OFFSET.get(rotation, (0,0))
            key = (int(x_mm+dx), int(y_mm+dy), rotation)
            if key not in placed_corners:
                placed_corners.add(key)
                self._add(corn_key, x_mm+dx, y_mm+dy, wz, rotation=rotation, face="corner")

        # ── 沿 X 排列（南/北面）──────────────────────
        def fill_x(gy_i, gx_s, gx_e, direction, with_door=False, with_win=False):
            # 北面實際 y = gy*G - 2*(G-CW) = gy*G - 564
            # 南面 y = 0
            if direction == 'north':
                y_mm = gy_i * G - 2 * (G - CW)
            else:
                y_mm = gy_i * G
            rot  = 0 if direction == 'south' else 180
            xs   = gx_s * G + CW
            xe   = gx_e * G - 2*(G-CW) - CW  # 實際東西向 = gx*G-564，有效範圍扣掉右端 CORNER
            iw   = xe - xs

            okey, ow = None, 0
            if with_door and iw >= DW: okey, ow = door_key, DW
            elif with_win  and iw >= WW: okey, ow = win_key,  WW

            ol = xs + ((iw - ow) // 2 // G) * G if okey else -1

            x, placed = xs, False
            while x < xe:
                rem = xe - x
                if okey and not placed and x >= ol and rem >= ow:
                    info = BLOCK_INSERT.get(okey, {})
                    self._add(okey,
                              x + info.get("off", ow),
                              y_mm + info.get("y_off", 0),
                              info.get("z_off", wz),
                              rotation=rot, face=direction)
                    x += ow; placed = True
                elif rem >= G:
                    self._add(wall_key, x+300, y_mm, wz, rotation=rot, face=direction)
                    x += G
                else:
                    break

            # CORNER 兩端
            rl = 0   if direction == 'south' else 270
            rr = 90  if direction == 'south' else 180
            corner_once(gx_s * G, y_mm, rl)
            corner_once(gx_e * G - 2*(G-CW), y_mm, rr)

        # ── 沿 Y 排列（東/西面）──────────────────────
        def fill_y(gx_i, gy_s, gy_e, direction, with_win=False, n_win=1):
            # 東面實際 x = 格點數×600 - 2×(600-318) = 實測建築寬度
            x_mm = gx_i * G - 2*(G-CW) if direction == 'east' else 0
            rot  = 90 if direction == 'east' else 270
            ys   = gy_s * G + CW
            ye   = gy_e * G - 2*(G-CW) - CW  # 實際南北向 = gy*G-564，有效範圍扣掉兩端 CORNER
            ih   = ye - ys

            ops = []
            if with_win and ih >= WW:
                if n_win == 1:
                    ops = [ys + ((ih - WW) // 2 // G) * G]
                elif n_win == 2 and ih >= WW * 2:
                    seg = ih // 3
                    ops = [
                        ys + (seg - WW//2) // G * G,
                        ys + (seg*2 - WW//2) // G * G,
                    ]

            done_ops, y = set(), ys
            while y < ye:
                rem = ye - y
                did = False
                for op in ops:
                    if op not in done_ops and y >= op and rem >= WW:
                        info = BLOCK_INSERT.get(win_key, {})
                        self._add(win_key, x_mm,
                                  y + info.get("off", WW//2),
                                  info.get("z_off", wz),
                                  rotation=rot, face=direction)
                        y += WW; done_ops.add(op); did = True; break
                if not did:
                    if rem >= G:
                        self._add(wall_key, x_mm, y+300, wz, rotation=rot, face=direction)
                        y += G
                    else:
                        break

            # CORNER 兩端（使用實際 y 座標）
            rb = 90  if direction == 'east' else 0
            rt = 180 if direction == 'east' else 270
            corner_once(x_mm, gy_s * G, rb)
            corner_once(x_mm, gy_e * G - 2*(G-CW), rt)

        # ── 執行 ─────────────────────────────────────
        for gy_i, gx_s, gx_e, d in x_segs:
            is_main = (main_south is not None
                       and gy_i==main_south[0]
                       and gx_s==main_south[1]
                       and gx_e==main_south[2])
            fill_x(gy_i, gx_s, gx_e, d,
                   with_door=is_main,
                   with_win=(d=='north'))

        for gx_i, gy_s, gy_e, d in y_segs:
            fill_y(gx_i, gy_s, gy_e, d,
                   with_win=(d=='east'),
                   n_win=2 if d=='east' else 1)

    # ── Step 3：屋頂 ──────────────────────────────

    def _place_roof(self, target):
        gx, gy = target.grids_x, target.grids_y
        s = self.span_str
        key = f"ROOF_{s}42" if self.roof_type == "gable_42deg" else f"ROOF_{s}10"
        for y in range(gy):
            if any(target.contains(x, y, 0) for x in range(gx)):
                self._add(key, 0, y*600, 0, face="top")

    def _generate_bom(self):
        count_map = {}
        for b in self.placed_blocks:
            k = (b.block_id, b.category, b.series, b.name)
            count_map[k] = count_map.get(k, 0) + 1
        bom = []
        for (block_id, category, series, name), qty in sorted(count_map.items()):
            bom.append({
                "block_id": block_id, "category": category,
                "series": series, "name": name, "quantity": qty,
                "assembly_step": ASSEMBLY_ORDER.get(category, {}).get("step", 99),
            })
        bom.sort(key=lambda x: x["assembly_step"])
        return bom


# ══════════════════════════════════════════════
# 便利介面
# ══════════════════════════════════════════════

def generate_from_requirements(
    shape="rectangle", area_sqm=50.0, series="skylark250",
    span_str="M", wall_height_str="M", roof_type="flat",
    stories=1, **kwargs
):
    engine = DiscreteAggregationEngine(
        series=series, span_str=span_str,
        wall_height_str=wall_height_str, roof_type=roof_type,
    )
    span_m = {"S": 3.6, "XS": 3.0, "XXXS": 2.4, "M": 4.8, "L": 5.4}.get(span_str, 4.8)
    # 扣掉兩端 CORNER 佔用（各 318mm = 0.636m）再計算格數
    lg = max(4, round(((area_sqm / span_m) - 0.636) / 0.6))
    hg = {"S": 3, "M": 4, "L": 5, "XL": 5}.get(wall_height_str, 4)

    if shape == "rectangle":
        target = make_rectangle(span_str, lg, hg)
    elif shape == "L":
        target = make_L_shape(span_str, lg,
                              kwargs.get("wing_grids_x", SPAN_GRIDS.get(span_str,8)//2),
                              kwargs.get("wing_grids_y", lg//2), hg)
    elif shape == "U":
        target = make_U_shape(span_str, lg,
                              kwargs.get("court_grids_x", SPAN_GRIDS.get(span_str,8)//2),
                              kwargs.get("court_grids_y", lg//3), hg)
    elif shape == "cross":
        target = make_cross(span_str, kwargs.get("arm_length", 4), hg)
    else:
        target = make_rectangle(span_str, lg, hg)

    return engine.generate(target)


def generate_three_schemes(area_sqm=50.0, series="skylark250"):
    schemes = {}
    configs = [
        ("scheme_a", "S", "M", "flat",        "方案 A｜保守型", "窄長形、平頂"),
        ("scheme_b", "M", "M", "flat",        "方案 B｜標準型", "正方形、平頂"),
        ("scheme_c", "M", "L", "gable_42deg", "方案 C｜進階型", "山牆 42°"),
    ]
    for key, span, wh, roof, label, desc in configs:
        r = generate_from_requirements(
            shape="rectangle", area_sqm=area_sqm,
            series=series, span_str=span, wall_height_str=wh, roof_type=roof,
        )
        r["label"] = label; r["description"] = desc
        r["span"] = span;   r["roof"] = roof
        schemes[key] = r
    return schemes


# ══════════════════════════════════════════════
# 測試
# ══════════════════════════════════════════════

if __name__ == "__main__":
    for shape in ["rectangle", "L", "U", "cross"]:
        r = generate_from_requirements(shape=shape, area_sqm=50, span_str="M", wall_height_str="M")
        blocks  = r["placed_blocks"]
        corners = [b for b in blocks if b["face"]=="corner"]
        south   = [b for b in blocks if b["face"]=="south"]
        print(f"{shape:12s}: {len(blocks):3d} blocks, {len(corners):2d} corners, "
              f"south={[(b['name'], b['position_mm']['x_mm']) for b in south]}")