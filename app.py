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

    # ── 模式選擇 ──
    mode = st.radio(
        "選擇模式",
        ["🏠 建築設計模式", "🔬 離散探索模式"],
        index=0
    )
    st.divider()

    # ── Block Library ──
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

    # 說明卡片
    with st.expander("ℹ️ 此模式的特性", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**嚴格驗證**\n所有方案必須通過 Connection Grammar 驗證才顯示")
        with col2:
            st.info("**三方案比較**\n保守型 / 標準型 / 進階型，幾何差異由引擎保證")
        with col3:
            st.info("**製造就緒**\n輸出 BOM 清單、Ties 用量、組裝順序")

    st.divider()

    # 對話歷史
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

            # Grammar 驗證
            last_user_msg = next(
                (m["content"] for m in reversed(st.session_state.design_messages)
                 if m["role"] == "user"), ""
            )
            result = validate_and_format_result(reply, blocks, last_user_msg)

            st.divider()

            # ── 三方案驗證狀態 ──
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

                # ── 建築圖面可視化 ──
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

            # ── 製造資訊 ──
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

            # ── Block 圖示 ──
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
        "選擇目標形體，系統會用 WikiHouse Block 依照組裝邏輯自動填充，"
        "適合探索非標準建築形態或基礎設施尺度的離散配置。"
    )

    with st.expander("ℹ️ 此模式的特性", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**形體自由**\n預設六種形體，未來支援自由繪製")
        with col2:
            st.warning("**探索性驗證**\n顯示違規提示但不強制修正，允許實驗性配置")
        with col3:
            st.info("**任意尺度**\n從住宅到橋梁，Block 作為通用建構單元")

    st.divider()

    # ── 參數設定 ──
    col_params, col_viz = st.columns([1, 2])

    with col_params:
        st.subheader("⚙️ 設計參數")

        target_shape = st.selectbox(
            "目標形體",
            ["rectangle", "L", "U", "arch", "cross"],
            format_func=lambda x: {
                "rectangle": "矩形（住宅標準）",
                "L":         "L 形（轉角配置）",
                "U":         "U 形（院落型）",
                "arch":      "拱形（橋梁/展館）",
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

        # 探索模式驗證選項
        st.divider()
        st.caption("🔬 探索模式設定")
        strict_mode = st.toggle("嚴格驗證模式", value=False,
                                help="開啟：錯誤必須修正。關閉：顯示提示但允許實驗性配置。")

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

            # ── 基本資訊 ──
            dims = result["dimensions"]
            st.markdown(f"""
            **形體**：{target_shape} ｜
            **尺寸**：{dims['width_m']}m × {dims['length_m']}m ｜
            **面積**：{round(dims['width_m'] * dims['length_m'], 1)} m²
            """)

            # ── 驗證狀態（探索模式特有）──
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
                st.warning("⚠️ 實驗性配置（已偵測到規則違反，僅供探索）")
                for e in errors:
                    st.warning(f"[{e['rule_id']}] {e['message']}")

            for w in warnings:
                st.info(f"[{w['rule_id']}] {w['message']}")

            # ── BOM 清單 ──
            bom = result["bom"]
            total_qty = sum(b["quantity"] for b in bom)

            with st.expander(f"📦 BOM 材料清單（{total_qty} 個 Block）", expanded=True):
                bom_data = {
                    "步驟": [b["assembly_step"] for b in bom],
                    "Block ID":  [b["block_id"]  for b in bom],
                    "類型":      [b["category"]  for b in bom],
                    "數量":      [b["quantity"]  for b in bom],
                }
                st.dataframe(bom_data, use_container_width=True)

            # ── Block 位置分佈（探索模式視覺化）──
            placed = result["placed_blocks"]
            with st.expander("📍 Block 位置分佈（俯視圖）", expanded=True):
                import matplotlib
                matplotlib.use("Agg")
                fig, ax = plt.subplots(figsize=(8, 6))
                fig.patch.set_facecolor("#1A1A2E")
                ax.set_facecolor("#1A1A2E")

                color_map = {
                    "floor":     "#D4C5A9",
                    "end":       "#C4B090",
                    "wall":      "#6B8FA3",
                    "corner":    "#4A6F82",
                    "window":    "#A8D8EA",
                    "roof":      "#8FA36B",
                    "connector": "#888888",
                }

                for pb in placed:
                    x = pb["position"]["x"]
                    y = pb["position"]["y"]
                    cat = pb["category"]
                    color = color_map.get(cat, "#CCCCCC")
                    rect = plt.Rectangle(
                        (x, y), 1, 1,
                        facecolor=color, edgecolor="#2A2A4E",
                        linewidth=0.5, alpha=0.85
                    )
                    ax.add_patch(rect)

                ax.set_xlim(-0.5, dims["grids_x"] + 0.5)
                ax.set_ylim(-0.5, dims["grids_y"] + 0.5)
                ax.set_aspect("equal")
                ax.set_title(f"Block 俯視配置圖（{target_shape}）",
                             color="white", fontsize=10)
                ax.tick_params(colors="gray")
                for spine in ax.spines.values():
                    spine.set_edgecolor("#2A2A4E")

                # 圖例
                legend_items = [
                    plt.Rectangle((0,0),1,1, fc=color_map[c], label=c)
                    for c in ["floor","wall","corner","window","roof"]
                ]
                ax.legend(handles=legend_items, loc="upper right",
                          facecolor="#2A2A4E", edgecolor="#4A4A6E",
                          labelcolor="white", fontsize=8)

                st.pyplot(fig)
                plt.close(fig)

            # ── 等角視覺化 ──
            from utils.visualizer import draw_isometric
            with st.expander("🏗️ 等角示意圖", expanded=True):
                fig_iso, ax_iso = plt.subplots(figsize=(8, 6))
                draw_isometric(
                    placed,
                    scheme_label=f"{target_shape} — {span_str} 跨距 — {roof_type}",
                    roof_type=roof_type,
                    span_str=span_str,
                    ax=ax_iso
                )
                st.pyplot(fig_iso)
                plt.close(fig_iso)

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

            # ── JSON 匯出 ──
            st.download_button(
                label="⬇️ 下載配置 JSON",
                data=json.dumps(result, ensure_ascii=False, indent=2),
                file_name=f"wikihouse_{target_shape}_{span_str}_{roof_type}.json",
                mime="application/json"
            )

        else:
            st.info("👈 設定參數後點擊「生成配置」開始")

            # 形體預覽說明
            shape_desc = {
                "rectangle": "📐 矩形：最基本的 WikiHouse 配置，適合住宅",
                "L":         "📐 L 形：轉角配置，適合有院子的住宅",
                "U":         "📐 U 形：院落型，三面圍合的中庭空間",
                "arch":      "📐 拱形：半圓拱，適合橋梁、展館等基礎設施",
                "cross":     "📐 十字形：多翼配置，適合學校、社區中心",
            }
            st.markdown(f"**{shape_desc.get(target_shape, '')}**")