import pandas as pd
from supabase import create_client
import math

# ============================================================
# Supabase接続情報（secrets.toml または 直書きで設定）
# ============================================================
SUPABASE_URL = "https://ggfmjnksquozqwuiurtu.supabase.co"  # ← 書き換えてください
SUPABASE_KEY = "sb_publishable_IyY5c5AImaEbyLu8X4a7_Q_D9Hkw-4s"                  # ← 書き換えてください
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# データの読み込みと更新処理
# ============================================================
# 今回アップロードした新しいCSVファイルの名前を指定
csv_file = "滋賀第3支部ポスター掲示依頼_全市統合_区分付き.xlsx - 全市統合.csv"
print("データを読み込み中...")
df = pd.read_csv(csv_file)

# 「掲示」の記号をアプリ側の「ステータス」の言葉に変換する辞書
status_map = {"○": "承諾", "△": "交渉中", "×": "お断り"}

success_count = 0
error_count = 0

print("Supabaseへの一括アップデートを開始します...")

for index, row in df.iterrows():
    try:
        # 空行をスキップ
        if pd.isna(row['No']):
            continue
        
        # IDの生成（例: 草津市0001）
        city = str(row['市町村']).strip()
        no = int(row['No'])
        poster_id = f"{city}{no:04d}"
        
        # 掲示 -> status への変換
        keiji = str(row['掲示']).strip()
        status_val = status_map.get(keiji, "未交渉") # 記号がない場合は未交渉に
        
        # 区分の取得
        kubun_val = str(row['区分']).strip()
        if kubun_val == "nan":
            kubun_val = ""
            
        # Supabaseへ送信するデータ
        update_data = {
            "status": status_val,
            "kubun": kubun_val
        }
        
        # IDをキーにしてデータを上書き更新！
        response = supabase.table("tbl_poster_management").update(update_data).eq("poster_id", poster_id).execute()
        
        if len(response.data) > 0:
            print(f"✅ 更新成功: {poster_id} -> ステータス:[{status_val}], 区分:[{kubun_val}]")
            success_count += 1
        else:
            print(f"⚠️ スキップ: {poster_id} はデータベースに見つかりませんでした")
            
    except Exception as e:
        print(f"❌ エラー ({poster_id}): {e}")
        error_count += 1

print("-" * 30)
print(f"🎉 アップデート完了！ 成功: {success_count}件, エラー: {error_count}件")