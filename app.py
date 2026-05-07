import streamlit as st
import anthropic
import json
from dotenv import load_dotenv
from utils.block_loader import load_blocks, load_system_rules, load_design_guidance
from utils.prompts import build_system_prompt

load_dotenv()

st.set_page_config(
    page_title="WikiHouse 設計助理",
    page_icon="WH",
    layout="wide"
)

@st.cache_data
def get_data():
    return load_blocks(), load_system_rules(), load_design_guidance()

@st.cache_resource
def get_client():
    return anthropic.Anthropic()

blocks, rules, guidance = get_data()
client = get_client()
system_prompt = build_system_prompt(blocks, rules, guidance)

def render_block_card(block: dict, show_cnc: bool = False):
    iso_url = block.get("iso_svg_url", "")
    cnc_url = block.get("cnc_svg_url", "")

    # 等角圖 + CNC 並排
    col_iso, col_cnc = st.columns(2)
    with col_iso:
        st.caption("等角視圖")
        st.markdown(
            f'<div style="background:white;border-radius:6px;padding:6px;">'
            f'<img src="{iso_url}" style="width:100%;" '
            f'onerror="this.style.display=\'none\'"></div>',
            unsafe_allow_html=True
        )
    with col_cnc:
        st.caption("CNC 切割圖")
        st.markdown(
            f'<div style="background:white;border-radius:6px;padding:6px;">'
            f'<img src="{cnc_url}" style="width:100%;" '
            f'onerror="this.style.display=\'none\'"></div>',
            unsafe_allow_html=True
        )

    # 規格資訊
    details = block.get("details", {})
    materials = block.get("materials", {})

    if details:
        st.caption(f"尺寸：{details.get('dimensions', '-')}")
        cost = details.get("typical_cost", "")
        weight = details.get("typical_weight", "")
        carbon = details.get("typical_carbon", "")
        if cost:   st.caption(f"價格：{cost}")
        if weight: st.caption(f"重量：{weight}")
        if carbon: st.caption(f"碳排：{carbon}")

    if materials:
        st.caption(f"結構材：{materials.get('structure', '-')}")
        st.caption(f"隔熱：{materials.get('insulation', '-')}")
        sheets = materials.get("sheets", "")
        if sheets: st.caption(f"板材用量：{sheets} 張")

    parts = block.get("parts", [])
    if parts:
        with st.expander("Parts 清單"):
            for p in parts:
                st.caption(p)

def extract_block_ids(text: str, all_blocks: list) -> list:
    all_ids = {b["id"] for b in all_blocks}
    return [bid for bid in all_ids if bid in text]

# ── 側邊欄 ──
with st.sidebar:
    st.header("Block Library")
    st.caption(f"共 {len(blocks)} 個 Block")

    series_filter = st.selectbox("系列", ["全部", "skylark250", "skylark200"])
    category_filter = st.selectbox("類型", ["全部", "wall", "floor", "roof",
                                             "window", "stair", "connector"])
    search_text = st.text_input("搜尋 Block 名稱", "")

    filtered = blocks
    if series_filter != "全部":
        filtered = [b for b in filtered if b["series"] == series_filter]
    if category_filter != "全部":
        filtered = [b for b in filtered if b["category"] == category_filter]
    if search_text:
        filtered = [b for b in filtered
                    if search_text.upper() in b["id"].upper()]

    st.caption(f"顯示 {len(filtered)} 個")
    st.divider()

    for block in filtered[:30]:  # 最多顯示 30 個避免太慢
        with st.expander(block["id"]):
            render_block_card(block)

    if len(filtered) > 30:
        st.caption(f"（僅顯示前 30 個，請用搜尋縮小範圍）")

# ── 主區域 ──
st.title("WikiHouse 設計助理")
st.caption("描述你的空間需求，我會從 201 個官方 Block 中找出最適合的配置")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": """你好！我是 WikiHouse Skylark 設計助理，我有完整的 SK250 和 SK200 Block 資料庫（共 201 個 Block）。

請告訴我你的建築需求：
- **面積**：大概幾坪或幾平方公尺？
- **空間**：需要幾間臥室、客廳、廚房、書房等？
- **樓層**：單層還是多層？
- **屋頂**：平頂、斜頂或山牆屋頂？
- **地區**：台灣哪個地區（影響隔熱需求）？

例如：「我想蓋一個 25 坪的兩房一廳平房，位於台灣南部」"""
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("描述你的空間需求..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("分析中..."):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                system=system_prompt,
                messages=st.session_state.messages
            )
            reply = response.content[0].text
            st.markdown(reply)

            # 找出推薦的 Block 並顯示圖片
            rec_ids = extract_block_ids(reply, blocks)
            if rec_ids:
                rec_blocks = [b for b in blocks if b["id"] in rec_ids]
                st.divider()
                st.caption(f"推薦 Block 圖示（共 {len(rec_blocks)} 個）")
                cols = st.columns(min(len(rec_blocks), 4))
                for i, rb in enumerate(rec_blocks):
                    with cols[i % 4]:
                        render_block_card(rb)

    st.session_state.messages.append({"role": "assistant", "content": reply})

st.divider()
if st.button("重新開始"):
    st.session_state.messages = []
    st.rerun()