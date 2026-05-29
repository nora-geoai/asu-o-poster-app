import networkx as nx
from pyvis.network import Network
import os

print("🌱 グラフデータ（農地と人）を構築中...")

# 1. ネットワーク（グラフ）の作成
# DiGraph = Directed Graph（矢印の向きがあるグラフ）
G = nx.DiGraph()

# 2. ノード（点）を追加：【人】
# プロパティとして、名前や役割のデータを持たせます
G.add_node("Person_1", label="上野", group="人", title="役割: プロジェクト管理者\nスキル: GIS, Python")
G.add_node("Person_2", label="本永", group="人", title="役割: アグリジオ\n専門: 空間データ連携")
G.add_node("Person_3", label="金澤", group="人", title="役割: アグリジオ\n専門: JSON-LD")

# 3. ノード（点）を追加：【農地】
G.add_node("Farm_A", label="明日を農園（東区画）", group="農地", title="面積: 1500m2\n作物: 米")
G.add_node("Farm_B", label="明日を農園（西区画）", group="農地", title="面積: 800m2\n作物: 野菜")
G.add_node("Farm_C", label="遊休農地（山間部）", group="農地", title="面積: 3000m2\n状況: 耕作放棄地")

# 4. エッジ（線）を追加：【関係性】
# ここがグラフデータベースの心臓部です！
G.add_edge("Person_1", "Farm_A", label="管理する (MANAGES)")
G.add_edge("Person_1", "Farm_B", label="所有する (OWNS)")
G.add_edge("Person_2", "Farm_B", label="データ支援する (SUPPORTS)")
G.add_edge("Person_3", "Farm_C", label="調査する (SURVEYS)")

# （おまけ）農地同士の関係性も定義できます
G.add_edge("Farm_A", "Farm_B", label="隣接している (ADJACENT_TO)")

# 5. グラフを可視化してHTMLに出力する設定
net = Network(height="700px", width="100%", directed=True, bgcolor="#222222", font_color="white")
# グループごとの色分け
net.add_node("Person_1", color="#3498db") # 青（人）
net.add_node("Farm_A", color="#2ecc71")   # 緑（農地）

net.from_nx(G)

# オプション：物理演算（ノードが反発しあって綺麗に並ぶ設定）
net.set_options("""
var options = {
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -15000
    }
  }
}
""")

# HTMLファイルとして保存
output_file = "agri_graph_prototype.html"
net.save_graph(output_file)

print(f"✅ 完了！Macのブラウザで {output_file} を開いてください。")