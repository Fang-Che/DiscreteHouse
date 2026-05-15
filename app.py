import streamlit as st
import anthropic
import json
import os
import re
import matplotlib.pyplot as plt
from pathlib import Path
from utils.block_loader import load_blocks, load_system_rules, load_design_guidance
from utils.prompts import build_system_prompt
from utils.design_validator import validate_and_format_result
from utils.visualizer import draw_three_schemes
from utils.discrete_engine import generate_three_schemes, generate_from_requirements

# ── 讀取 .env ──
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

st.set_page_config(
    page_title="WikiHouse AI Design Platform",
    page_icon="WH",
    layout="wide"
)

@st.cache_data
def get_data():
    return load_blocks(), load_system_rules(), load_design_guidance()

def get_client():
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

blocks, rules, guidance = get_data()
client = get_client()
system_prompt = build_system_prompt(blocks, rules, guidance)

def clean_reply(text: str) -> str:
    text = re.sub(r"<DESIGN_JSON>[\s\S]*?</DESIGN_JSON>", "", text)
    text = re.sub(r"```json[\s\S]*?```", "", text)
    text = re.sub(r"```[\s\S]*?```", "", text)
    return text.strip()

def render_block_card(block: dict):
    iso_url = block.get("iso_svg_url", "")
    cnc_url = block.get("cnc_svg_url", "")
    col_iso, col_cnc = st.columns(2)
    with col_iso:
        st.caption("等角視圖")
        st.markdown(
            f'<div style="background:white;border-radius:6px;padding:6px;">'
            f'<img src="{iso_url}" style="width:100%;" onerror="this.style.display=\'none\'"></div>',
            unsafe_allow_html=True
        )
    with col_cnc:
        st.caption("CNC 切割圖")
        st.markdown(
            f'<div style="background:white;border-radius:6px;padding:6px;">'
            f'<img src="{cnc_url}" style="width:100%;" onerror="this.style.display=\'none\'"></div>',
            unsafe_allow_html=True
        )
    materials = block.get("materials", {})
    if materials:
        st.caption(f"結構材：{materials.get('structure', '-')}")
        st.caption(f"隔熱：{materials.get('insulation', '-')}")
        if materials.get("sheets"):
            st.caption(f"板材用量：{materials['sheets']} 張")
    parts = block.get("parts", [])
    if parts:
        with st.expander("Parts 清單"):
            for p in parts:
                st.caption(p)


# ══════════════════════════════════════════════
# 側邊欄：模式選擇 + Block Library
# ══════════════════════════════════════════════

with st.sidebar:
    st.title("WikiHouse AI")
    st.divider()

    mode = st.radio(
        "選擇模式",
        ["🏠 建築設計模式", "🔬 離散探索模式"],
        index=0
    )
    st.divider()

    st.header("Block Library")
    st.caption(f"共 {len(blocks)} 個 Block")
    series_filter   = st.selectbox("系列", ["全部", "skylark250", "skylark200"])
    category_filter = st.selectbox("類型", ["全部", "wall", "floor", "roof",
                                             "window", "stair", "connector"])
    search_text = st.text_input("搜尋", "")
    filtered = blocks
    if series_filter   != "全部": filtered = [b for b in filtered if b["series"]   == series_filter]
    if category_filter != "全部": filtered = [b for b in filtered if b["category"] == category_filter]
    if search_text: filtered = [b for b in filtered if search_text.upper() in b["id"].upper()]
    st.caption(f"顯示 {len(filtered)} 個")
    st.divider()
    for block in filtered[:20]:
        with st.expander(block["id"]):
            render_block_card(block)
    if len(filtered) > 20:
        st.caption("（僅顯示前 20 個）")


# ══════════════════════════════════════════════
# 模式 A：建築設計模式
# ══════════════════════════════════════════════

if mode == "🏠 建築設計模式":

    st.title("🏠 建築設計模式")
    st.caption(
        "輸入自然語言需求，系統會生成三個符合 WikiHouse 製造規範的建築設計方案，"
        "並進行 Fabrication-Aware Grammar 驗證。"
    )

    with st.expander("ℹ️ 此模式的特性", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**嚴格驗證**\n所有方案必須通過 Connection Grammar 驗證才顯示")
        with col2:
            st.info("**三方案比較**\n保守型 / 標準型 / 進階型，幾何差異由引擎保證")
        with col3:
            st.info("**製造就緒**\n輸出 BOM 清單、Ties 用量、組裝順序")

    st.divider()

    if "design_messages" not in st.session_state:
        st.session_state.design_messages = []
        st.session_state.design_messages.append({
            "role": "assistant",
            "content": """你好！我是 WikiHouse Skylark 建築設計助理。

請告訴我你的建築需求：
- **面積**：大概幾坪或幾平方公尺？
- **空間**：需要幾間臥室、客廳、廚房、書房等？
- **樓層**：單層還是多層？
- **屋頂**：平頂、斜頂或山牆屋頂？
- **地區**：台灣哪個地區（影響隔熱需求）？

例如：「我想蓋一個 25 坪的兩房一廳平房，位於台灣南部」"""
        })

    for msg in st.session_state.design_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("描述你的空間需求...", key="design_input"):
        st.session_state.design_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        reply = ""
        reply_display = ""

        with st.chat_message("assistant"):
            with st.spinner("AI 分析需求中..."):
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4000,
                    system=system_prompt,
                    messages=st.session_state.design_messages
                )
                reply = response.content[0].text

            reply_display = clean_reply(reply)
            st.markdown(reply_display)

            last_user_msg = next(
                (m["content"] for m in reversed(st.session_state.design_messages)
                 if m["role"] == "user"), ""
            )
            result = validate_and_format_result(reply, blocks, last_user_msg)

            st.divider()

            if result.get("has_json"):
                scheme_results = result.get("scheme_results", {})
                scheme_names = {
                    "scheme_a": "方案 A｜保守型",
                    "scheme_b": "方案 B｜標準型",
                    "scheme_c": "方案 C｜進階型",
                }
                cols = st.columns(3)
                for i, (key, label) in enumerate(scheme_names.items()):
                    sr = scheme_results.get(key, {})
                    with cols[i]:
                        if sr.get("is_valid"):
                            st.success(f"✅ {label}\nGrammar 驗證通過")
                        else:
                            st.error(f"❌ {label}")
                            for e in sr.get("validation", {}).get("errors", []):
                                st.caption(f"[{e['rule_id']}] {e['message']}")

                if result.get("all_valid"):
                    st.success("✅ 三個方案均通過 Fabrication-Aware Grammar 驗證")
                else:
                    st.warning("⚠️ 部分方案需修正")
                    if st.button("🔄 AI 自動修正", key="design_fix"):
                        st.session_state.design_messages.append({
                            "role": "user",
                            "content": result.get("correction_prompt", "")
                        })
                        st.rerun()

                if scheme_results:
                    st.divider()
                    st.subheader("📐 建築設計圖面")
                    import matplotlib
                    matplotlib.use("Agg")
                    viz_fig = draw_three_schemes(scheme_results)
                    st.pyplot(viz_fig)
                    plt.close(viz_fig)

            else:
                if result.get("is_valid"):
                    st.success("✅ 配置合法（Grammar 驗證通過）")
                else:
                    st.error("❌ 配置需要修正")
                    for e in result.get("validation", {}).get("errors", []):
                        st.error(f"[{e['rule_id']}] {e['message']}")

            ties = result.get("ties", {})
            if ties and ties.get("total", 0) > 0:
                with st.expander("🔩 Bowtie Ties 用量"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Floor-Floor", f"{ties.get('floor_to_floor', 0)} 個")
                        st.metric("Floor-Wall",  f"{ties.get('floor_to_wall', 0)} 個")
                    with col2:
                        st.metric("Wall-Wall", f"{ties.get('wall_to_wall', 0)} 個")
                        st.metric("Wall-Roof", f"{ties.get('wall_to_roof', 0)} 個")
                    st.info(f"總計：**{ties.get('total', 0)} 個** Bowtie Ties")

            assembly = result.get("validation", {}).get("assembly_order", [])
            if assembly:
                with st.expander("📋 組裝順序"):
                    for step in assembly:
                        st.write(f"**步驟 {step['step']}**：{step['label']}")
                        st.caption(", ".join(step["blocks"][:5])
                                   + ("..." if len(step["blocks"]) > 5 else ""))

            rec_blocks = result.get("recommended_blocks", [])
            if rec_blocks:
                block_map = {b["id"]: b for b in blocks}
                display_blocks = [block_map[rb["id"]] for rb in rec_blocks
                                  if rb.get("id") in block_map]
                if display_blocks:
                    st.caption(f"推薦 Block 圖示（{len(display_blocks)} 個）")
                    cols = st.columns(min(len(display_blocks), 4))
                    for i, rb in enumerate(display_blocks):
                        with cols[i % 4]:
                            render_block_card(rb)

        st.session_state.design_messages.append({
            "role": "assistant", "content": reply_display
        })

    st.divider()
    if st.button("🔄 重新開始", key="design_reset"):
        st.session_state.design_messages = []
        st.rerun()


# ══════════════════════════════════════════════
# 模式 B：離散探索模式
# ══════════════════════════════════════════════

else:
    st.title("🔬 離散探索模式")
    st.caption(
        "選擇目標形體與參數，系統自動生成 WikiHouse Block 配置，"
        "並輸出 output_placement.json 供 Grasshopper 讀取。"
    )

    with st.expander("ℹ️ 此模式的特性", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**形體自由**\n矩形、L 形、U 形、十字形")
        with col2:
            st.warning("**探索性驗證**\n顯示違規提示但不強制修正")
        with col3:
            st.info("**Grasshopper 整合**\n直接輸出 JSON 供 Rhino 讀取")

    st.divider()

    col_params, col_viz = st.columns([1, 2])

    with col_params:
        st.subheader("⚙️ 設計參數")

        target_shape = st.selectbox(
            "目標形體",
            ["rectangle", "L", "U", "cross"],
            format_func=lambda x: {
                "rectangle": "矩形（住宅標準）",
                "L":         "L 形（轉角配置）",
                "U":         "U 形（院落型）",
                "cross":     "十字形（多翼配置）",
            }[x]
        )

        area_sqm = st.slider("目標面積（m²）", 20, 300, 50, 5)

        series = st.selectbox(
            "Block 系列",
            ["skylark250", "skylark200"],
            format_func=lambda x: {
                "skylark250": "SK250（多層、高隔熱）",
                "skylark200": "SK200（單層、輕量）",
            }[x]
        )

        span_str = st.selectbox(
            "跨距",
            ["S", "M", "L"],
            index=1,
            format_func=lambda x: {
                "S": "S — 3.6m（小型）",
                "M": "M — 4.8m（標準）",
                "L": "L — 5.4m（大跨距）",
            }[x]
        )

        wall_height = st.selectbox(
            "牆板高度",
            ["S", "M", "L", "XL"],
            index=1,
            format_func=lambda x: {
                "S":  "S — 2100mm",
                "M":  "M — 2400mm（標準）",
                "L":  "L — 2700mm",
                "XL": "XL — 3000mm",
            }[x]
        )

        roof_type = st.selectbox(
            "屋頂形式",
            ["flat", "sloping_10deg", "gable_42deg"],
            format_func=lambda x: {
                "flat":         "平頂",
                "sloping_10deg":"單坡斜頂 10°",
                "gable_42deg":  "山牆屋頂 42°",
            }[x]
        )

        st.divider()
        strict_mode = st.toggle("嚴格驗證模式", value=False)

        # Grasshopper JSON 輸出路徑
        gh_json_path = st.text_input(
            "Grasshopper JSON 路徑",
            value=r"D:\GitHub_Projects\DiscreteHouse\output_placement.json",
            help="生成後自動寫入此路徑，Grasshopper Recompute 即可讀取"
        )

        generate_btn = st.button("🚀 生成配置", type="primary", use_container_width=True)

    with col_viz:
        st.subheader("📊 配置結果")

        if generate_btn:
            with st.spinner("離散集合引擎運算中..."):
                result = generate_from_requirements(
                    shape=target_shape,
                    area_sqm=area_sqm,
                    series=series,
                    span_str=span_str,
                    wall_height_str=wall_height,
                    roof_type=roof_type,
                )

            # ── 寫入 Grasshopper JSON ──
            placed_blocks = result["placed_blocks"]
            try:
                with open(gh_json_path, "w", encoding="utf-8") as f:
                    json.dump(placed_blocks, f, ensure_ascii=False, indent=2)
                st.success(f"✅ 已寫入 {gh_json_path}（{len(placed_blocks)} 個 Block）")
            except Exception as e:
                st.warning(f"⚠️ 無法寫入 JSON：{e}")

            # ── 基本資訊 ──
            dims = result["dimensions"]
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("形體", target_shape)
            with col_b:
                st.metric("尺寸", f"{dims['width_m']}m × {dims['length_m']}m")
            with col_c:
                st.metric("Block 總數", len(placed_blocks))

            # ── 驗證狀態 ──
            validation = result["validation"]
            is_valid   = validation["is_valid"]
            errors     = validation.get("errors", [])
            warnings   = validation.get("warnings", [])

            if is_valid:
                st.success("✅ 配置合法（符合 WikiHouse 製造規範）")
            elif strict_mode:
                st.error("❌ 配置不合法（嚴格模式）")
                for e in errors:
                    st.error(f"[{e['rule_id']}] {e['message']}")
            else:
                st.warning("⚠️ 實驗性配置（已偵測到規則違反）")
                for e in errors:
                    st.warning(f"[{e['rule_id']}] {e['message']}")

            for w in warnings:
                st.info(f"[{w['rule_id']}] {w['message']}")

            # ── BOM 清單 ──
            bom = result["bom"]
            total_qty = sum(b["quantity"] for b in bom)

            with st.expander(f"📦 BOM 材料清單（{total_qty} 個 Block）", expanded=True):
                bom_data = {
                    "步驟":     [b["assembly_step"] for b in bom],
                    "Block ID": [b["block_id"]  for b in bom],
                    "類型":     [b["category"]  for b in bom],
                    "數量":     [b["quantity"]  for b in bom],
                }
                st.dataframe(bom_data, use_container_width=True)

            # ── Block 俯視配置圖 ──
            with st.expander("📍 Block 俯視配置圖", expanded=True):
                # 建築尺寸：東西向=跨距方向(grids_x), 南北向=長度方向(grids_y)
                # 但注意：gx=8格對應的實際建築寬度 = 4236mm，gy=16格 = 9036mm
                bldg_w = dims["grids_x"] * 600 - 564   # 東西向(寬) mm
                bldg_h = dims["grids_y"] * 600 - 564   # 南北向(長) mm

                # SVG 畫布（東西向=水平，南北向=垂直）
                # 讓寬高比例正確
                SVG_W = 680
                ratio = bldg_h / bldg_w
                SVG_H = int(SVG_W * ratio * 0.6) + 120
                SVG_H = min(max(SVG_H, 350), 700)
                PL, PR, PT, PB = 50, 70, 40, 80
                cw = SVG_W - PL - PR   # 畫布有效寬
                ch = SVG_H - PT - PB   # 畫布有效高

                # px/py: mm → SVG 座標
                # 東西向(W)對應 SVG X，南北向(H)對應 SVG Y（北在上）
                def px(w): return PL + w / bldg_w * cw
                def py(h): return PT + (1 - h / bldg_h) * ch

                Tw = 318 / bldg_w * cw   # WALL厚(東西向) px
                Th = 318 / bldg_h * ch   # WALL厚(南北向) px

                BC = {"corner":"#D85A30","wall":"#6B8FA3","door":"#D4A843","window":"#4ABFA8"}
                def bc(b):
                    n = b["name"]
                    if "DOOR" in n: return BC["door"]
                    if "WINDOW" in n: return BC["window"]
                    return BC["wall"]

                rects = []

                # 南面（圖下方）: 從 x=318mm 開始，沿東西向排列
                # block 寬度：WALL=600, DOOR/WINDOW=1200
                cur = 318  # mm，從 CORNER 右邊緣開始
                for b in sorted([b for b in placed_blocks if b["face"]=="south"],
                                 key=lambda b: b["position_mm"]["x_mm"]):
                    w = 1200 if ("DOOR" in b["name"] or "WINDOW" in b["name"]) else 600
                    bx = px(cur); bw = w / bldg_w * cw
                    by = py(0) - Th; c = bc(b)
                    lbl = "DOOR" if "DOOR" in b["name"] else "WIN" if "WINDOW" in b["name"] else "W"
                    rects += [f'<rect x="{bx:.1f}" y="{by:.1f}" width="{max(bw,2):.1f}" height="{Th:.1f}" fill="{c}" stroke="#0D1117" stroke-width="0.8" rx="2"/>',
                              f'<text x="{bx+bw/2:.1f}" y="{by+Th/2+4:.1f}" fill="white" font-size="9" font-family="sans-serif" text-anchor="middle">{lbl}</text>']
                    cur += w

                # 北面（圖上方）
                cur = 318
                for b in sorted([b for b in placed_blocks if b["face"]=="north"],
                                 key=lambda b: b["position_mm"]["x_mm"]):
                    w = 1200 if "WINDOW" in b["name"] else 600
                    bx = px(cur); bw = w / bldg_w * cw
                    by = py(bldg_h); c = bc(b)
                    lbl = "WIN" if "WINDOW" in b["name"] else "W"
                    rects += [f'<rect x="{bx:.1f}" y="{by:.1f}" width="{max(bw,2):.1f}" height="{Th:.1f}" fill="{c}" stroke="#0D1117" stroke-width="0.8" rx="2"/>',
                              f'<text x="{bx+bw/2:.1f}" y="{by+Th/2+4:.1f}" fill="white" font-size="9" font-family="sans-serif" text-anchor="middle">{lbl}</text>']
                    cur += w

                # 西面（圖左側）: 從 y=318mm 開始，沿南北向排列
                cur = 318
                for b in sorted([b for b in placed_blocks if b["face"]=="west"],
                                 key=lambda b: b["position_mm"]["y_mm"]):
                    h = 1200 if "WINDOW" in b["name"] else 600
                    bx = px(0); by = py(cur + h); bh = h / bldg_h * ch
                    c = bc(b)
                    rects.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{Tw:.1f}" height="{max(bh,2):.1f}" fill="{c}" stroke="#0D1117" stroke-width="0.8" rx="2"/>')
                    cur += h

                # 東面（圖右側）
                cur = 318
                for b in sorted([b for b in placed_blocks if b["face"]=="east"],
                                 key=lambda b: b["position_mm"]["y_mm"]):
                    h = 1200 if "WINDOW" in b["name"] else 600
                    bx = px(bldg_w) - Tw; by = py(cur + h); bh = h / bldg_h * ch
                    c = bc(b)
                    rects.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{Tw:.1f}" height="{max(bh,2):.1f}" fill="{c}" stroke="#0D1117" stroke-width="0.8" rx="2"/>')
                    if "WINDOW" in b["name"]:
                        rects.append(f'<text x="{bx+Tw/2:.1f}" y="{by+bh/2+4:.1f}" fill="white" font-size="9" font-family="sans-serif" text-anchor="middle">W</text>')
                    cur += h

                # CORNER 四角
                for ew, ns in [(0,0),(bldg_w,0),(0,bldg_h),(bldg_w,bldg_h)]:
                    bx = px(ew) - (Tw if ew>0 else 0)
                    by = py(ns) - (0 if ns>0 else Th) + (0 if ns>0 else 0)
                    if   ew==0     and ns==0:      bx,by = px(0),       py(0)-Th
                    elif ew>0      and ns==0:      bx,by = px(bldg_w)-Tw, py(0)-Th
                    elif ew==0     and ns>0:       bx,by = px(0),       py(bldg_h)
                    else:                          bx,by = px(bldg_w)-Tw, py(bldg_h)
                    rects += [f'<rect x="{bx:.1f}" y="{by:.1f}" width="{Tw:.1f}" height="{Th:.1f}" fill="{BC["corner"]}" stroke="#0D1117" stroke-width="0.8" rx="2"/>',
                              f'<text x="{bx+Tw/2:.1f}" y="{by+Th/2+4:.1f}" fill="white" font-size="9" font-family="sans-serif" text-anchor="middle">C</text>']

                # 尺寸標註
                anno = [
                    f'<line x1="{px(0):.1f}" y1="{SVG_H-42}" x2="{px(bldg_w):.1f}" y2="{SVG_H-42}" stroke="#555" stroke-width="1"/>',
                    f'<line x1="{px(0):.1f}" y1="{SVG_H-47}" x2="{px(0):.1f}" y2="{SVG_H-37}" stroke="#555" stroke-width="1"/>',
                    f'<line x1="{px(bldg_w):.1f}" y1="{SVG_H-47}" x2="{px(bldg_w):.1f}" y2="{SVG_H-37}" stroke="#555" stroke-width="1"/>',
                    f'<text x="{(px(0)+px(bldg_w))/2:.1f}" y="{SVG_H-26}" fill="#aaa" font-size="11" font-family="sans-serif" text-anchor="middle">東西 {bldg_w}mm</text>',
                    f'<line x1="{SVG_W-28}" y1="{py(0):.1f}" x2="{SVG_W-28}" y2="{py(bldg_h):.1f}" stroke="#555" stroke-width="1"/>',
                    f'<line x1="{SVG_W-33}" y1="{py(0):.1f}" x2="{SVG_W-23}" y2="{py(0):.1f}" stroke="#555" stroke-width="1"/>',
                    f'<line x1="{SVG_W-33}" y1="{py(bldg_h):.1f}" x2="{SVG_W-23}" y2="{py(bldg_h):.1f}" stroke="#555" stroke-width="1"/>',
                    f'<text x="{SVG_W-12}" y="{(py(0)+py(bldg_h))/2:.1f}" fill="#aaa" font-size="11" font-family="sans-serif" text-anchor="middle" transform="rotate(-90,{SVG_W-12},{(py(0)+py(bldg_h))/2:.1f})">南北 {bldg_h}mm</text>',
                ]

                # 圖例
                leg = []
                for i,(lc,ll) in enumerate([(BC["corner"],"CORNER"),(BC["wall"],"WALL"),(BC["door"],"DOOR"),(BC["window"],"WINDOW")]):
                    lx = PL + i*155
                    leg += [f'<rect x="{lx}" y="{SVG_H-16}" width="12" height="12" fill="{lc}" rx="2"/>',
                            f'<text x="{lx+16}" y="{SVG_H-5}" fill="#ccc" font-size="11" font-family="sans-serif">{ll}</text>']

                svg = f'''<svg width="{SVG_W}" height="{SVG_H}" xmlns="http://www.w3.org/2000/svg" style="background:#0D1117;border-radius:8px;display:block;">
                  <text x="{SVG_W//2}" y="25" fill="white" font-size="13" font-family="sans-serif" text-anchor="middle">{target_shape} — 東西 {round(bldg_w/1000,3)}m x 南北 {round(bldg_h/1000,3)}m</text>
                  {"".join(rects)}{"".join(anno)}{"".join(leg)}
                </svg>'''
                st.markdown(svg, unsafe_allow_html=True)

                # Block 清單
                st.caption("**各面 Block 配置：**")
                for fk, fl in [("south","南面"),("north","北面"),("east","東面"),("west","西面"),("corner","CORNER")]:
                    fb = [b for b in placed_blocks if b["face"]==fk]
                    if not fb: continue
                    items = []
                    for b in fb:
                        n = b["name"]
                        if "DOOR" in n: dim="1200mm"
                        elif "WINDOW" in n: dim="1200mm"
                        elif "CORNER" in n: dim="318x318mm"
                        else: dim="600mm"
                        items.append(f"{n}({dim})")
                    st.caption(f"**{fl}**：{'  |  '.join(items)}")

            # ── Ties 計算 ──
            ties = validation.get("ties", {})
            if ties and ties.get("total", 0) > 0:
                with st.expander("🔩 Bowtie Ties 用量"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Floor-Floor", f"{ties.get('floor_to_floor',0)} 個")
                        st.metric("Floor-Wall",  f"{ties.get('floor_to_wall',0)} 個")
                    with c2:
                        st.metric("Wall-Wall", f"{ties.get('wall_to_wall',0)} 個")
                        st.metric("Wall-Roof", f"{ties.get('wall_to_roof',0)} 個")
                    st.info(f"總計：**{ties.get('total',0)} 個**")

            # ── 下載 JSON ──
            st.download_button(
                label="⬇️ 下載配置 JSON",
                data=json.dumps(placed_blocks, ensure_ascii=False, indent=2),
                file_name=f"wikihouse_{target_shape}_{span_str}_{roof_type}.json",
                mime="application/json"
            )

        else:
            st.info("👈 設定參數後點擊「生成配置」開始")
            shape_desc = {
                "rectangle": "📐 矩形：最基本的 WikiHouse 配置，適合住宅",
                "L":         "📐 L 形：轉角配置，適合有院子的住宅",
                "U":         "📐 U 形：院落型，三面圍合的中庭空間",
                "cross":     "📐 十字形：多翼配置，適合學校、社區中心",
            }
            st.markdown(f"**{shape_desc.get(target_shape, '')}**")