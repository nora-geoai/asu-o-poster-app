"""
ポスター現地調査専用アプリ（レイヤ切り替え機能付き完全版）
Streamlit + Folium + Supabase
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client
import os

# ============================================================
# 初期設定
# ============================================================
st.set_page_config(page_title="ポスター調査マップ", page_icon="📍", layout="wide")

st.markdown("""
<style>
  .login-box {
    background: #f4faf6; border: 1.5px solid #2d6a4f;
    border-radius: 16px; padding: 2rem 1.5rem 1.5rem;
    margin: 3rem auto; max-width: 360px; text-align: center;
  }
</style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# ============================================================
# 🔒 ログイン（合言葉）画面
# ============================================================
if not st.session_state["authenticated"]:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1a472a; margin-bottom: 20px;'>📍 ポスター調査システム</h3>", unsafe_allow_html=True)
    
    password = st.text_input("合言葉を入力してください", type="password")
    
    if st.button("ログイン", type="primary"):
        if password == st.secrets.get("APP_PASSWORD", ""):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("合言葉が違います。")
            
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ============================================================
# 以下、認証成功時のみ実行されるメイン処理
# ============================================================
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("データベースへの接続に失敗しました。")
    st.stop()

def fetch_poster_data():
    response = supabase.table("tbl_poster_management").select("*").execute()
    df = pd.DataFrame(response.data)
    
    if not df.empty:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])
        
        df['poster_condition'] = df['poster_condition'].fillna('未記録').astype(str).str.strip()
        df['poster_condition'] = df['poster_condition'].replace('', '未記録')
        df = df.sort_values(by='poster_id')
    return df

# タイトルから「プロジェクト名」を外してスマートに変更
st.title("📍 ポスター現地調査システム")
st.caption("最新のデータベース（Supabase）とリアルタイムに同期しています。")

with st.spinner("データを読み込んでいます..."):
    df_posters = fetch_poster_data()

if df_posters.empty:
    st.warning("データが見つかりません。")
    st.stop()

# ============================================================
# サイドバー：フィルタリング設定
# ============================================================
st.sidebar.header("🔍 絞り込み表示")
all_cities = sorted(df_posters['city'].unique().tolist())
selected_cities = st.sidebar.multiselect("市町村を選択", options=all_cities, default=all_cities)

status_options = ["承諾", "交渉中", "お断り", "未交渉"]
selected_status = st.sidebar.multiselect("表示するステータス", options=status_options, default=["承諾", "交渉中", "未交渉"])

all_conditions = sorted(df_posters['poster_condition'].unique().tolist())
selected_conditions = st.sidebar.multiselect("ポスター状況を選択", options=all_conditions, default=all_conditions)

df_filtered = df_posters[
    (df_posters['city'].isin(selected_cities)) & 
    (df_posters['status'].isin(selected_status)) &
    (df_posters['poster_condition'].isin(selected_conditions))
]
st.sidebar.markdown("---")
st.sidebar.metric(label="表示中のポスター数", value=f"{len(df_filtered)} / {len(df_posters)} 件")
if st.sidebar.button("ログアウト", type="secondary"):
    st.session_state["authenticated"] = False
    st.rerun()

# ============================================================
# 地図の描画 (Folium + レイヤ切り替え)
# ============================================================
if not df_filtered.empty:
    center_lat = df_filtered['latitude'].mean()
    center_lon = df_filtered['longitude'].mean()
else:
    center_lat = 35.0045
    center_lon = 135.9685

# レイヤを細かくコントロールするため、tiles=None で初期化
m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles=None)

# 🌍 レイヤ1：通常の地図 (OpenStreetMap)
folium.TileLayer('openstreetmap', name='通常地図').add_to(m)

# 🗺️ レイヤ2：航空写真 (国土地理院 シームレス空中写真)
folium.TileLayer(
    tiles='https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg',
    attr='国土地理院',
    name='航空写真',
    overlay=False,
    control=True
).add_to(m)

color_map = {"承諾": "blue", "交渉中": "orange", "お断り": "red", "未交渉": "gray"}

for _, row in df_filtered.iterrows():
    popup_html = f"""
    <div style='font-family: sans-serif; width: 220px; font-size: 12px;'>
        <b style='font-size: 14px; color: #1a472a;'>ID: {row['poster_id']}</b><br>
        <hr style='margin: 4px 0; border: 0; border-top: 1px solid #ccc;'>
        <b>現状:</b> <span style='color: {color_map.get(row['status'], 'black')}; font-weight: bold;'>{row['status']}</span><br>
        <b>住所:</b> {row.get('address_confirmed', 'なし')}<br>
        <b>情報:</b> {row.get('info', 'なし')}<br>
        <b>状況:</b> <b>{row.get('poster_condition', '未記録')}</b><br>
        <b>種類:</b> {row.get('poster_type', 'なし')}
    </div>
    """
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"ID: {row['poster_id']} ({row['status']})",
        icon=folium.Icon(color=color_map.get(row['status'], 'gray'), icon="info-sign")
    ).add_to(m)

# 🛠️ 地図の右上（または左上）にレイヤ切り替えスイッチを配置
folium.LayerControl(position='topright', collapsed=False).add_to(m)

st_folium(m, width="100%", height=550, returned_objects=[])

# ============================================================
# 現場からの即時更新機能
# ============================================================
st.markdown("---")
st.subheader("📝 現場からデータを即時更新")

condition_presets = ["良好", "色あせ", "破れ", "要貼り替え", "未記録"]
all_conditions_for_input = condition_presets.copy()
for c in all_conditions:
    if c not in all_conditions_for_input:
        all_conditions_for_input.append(c)

col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
with col1:
    target_id = st.text_input("対象ID (例: 草津市0001)", placeholder="草津市0001")
with col2:
    new_status = st.selectbox("新しいステータス", options=status_options)
with col3:
    new_condition = st.selectbox("ポスター状況", options=all_conditions_for_input)
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("データベースを更新", type="primary"):
        if not target_id:
            st.error("ポスターIDを入力してください。")
        else:
            try:
                response = supabase.table("tbl_poster_management") \
                    .update({
                        "status": new_status,
                        "poster_condition": new_condition if new_condition != "未記録" else ""
                    }) \
                    .eq("poster_id", target_id.strip()) \
                    .execute()
                
                if len(response.data) > 0:
                    st.success(f"🎉 ID: {target_id} を「{new_status} / {new_condition}」に更新しました！")
                    st.rerun()
                else:
                    st.error(f"⚠️ ID: {target_id} が見つかりませんでした。")
            except Exception as e:
                st.error(f"更新に失敗しました: {e}")

# ============================================================
# データ一覧表
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📊 絞り込みデータの一覧表を確認（全11項目対応）"):
    display_cols = ['poster_id', 'city', 'status', 'address_confirmed', 'info', 'poster_condition', 'poster_type', 'fetch_status']
    st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)