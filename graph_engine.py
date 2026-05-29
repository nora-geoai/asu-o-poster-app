import networkx as nx

print("🌱 プロトタイプ第2弾：グラフDB変換＆AI検索エンジン 起動\n")

# =========================================================
# 1. コンバーター機能（RDBのテーブルをグラフに変換）
# =========================================================
# 【疑似RDBデータ】 PostgreSQL等のテーブルから取得したと仮定したリスト
table_persons = [
    {"id": "p1", "name": "上野", "role": "GISエンジニア"},
    {"id": "p2", "name": "本永", "role": "データ連携専門家"}
]
table_farms = [
    {"id": "f1", "name": "明日を農園", "status": "稼働中"},
    {"id": "f2", "name": "山間部の遊休農地", "status": "耕作放棄"}
]
table_relations = [
    {"source": "p1", "target": "f1", "relation": "管理する"},
    {"source": "p2", "target": "f2", "relation": "調査する"}
]

def build_graph_from_rdb(persons, farms, relations):
    G = nx.DiGraph()
    
    # 人物テーブルの行をノードに変換
    for p in persons:
        G.add_node(p["id"], type="Person", name=p["name"], role=p["role"])
    
    # 農地テーブルの行をノードに変換
    for f in farms:
        G.add_node(f["id"], type="Farm", name=f["name"], status=f["status"])
    
    # 関係性テーブル（中間テーブル）をエッジに変換
    for r in relations:
        G.add_edge(r["source"], r["target"], label=r["relation"])
    
    return G

# コンバーターを実行
G = build_graph_from_rdb(table_persons, table_farms, table_relations)
print("✅ 1. コンバート完了: テーブルデータをグラフ構造に変換しました。")


# =========================================================
# 2. 編集機能（ノードとエッジの追加・更新）
# =========================================================
def add_or_update_node(G, node_id, **attributes):
    G.add_node(node_id, **attributes)
    print(f"   ✏️ ノード更新: ID={node_id} / プロパティ={attributes}")

def add_or_update_edge(G, source, target, relation):
    G.add_edge(source, target, label=relation)
    print(f"   🔗 エッジ更新: [{source}] --({relation})--> [{target}]")

print("\n✅ 2. 編集機能テスト: 新しいデータと関係性を追加します。")
# 新しい人物と、既存農地への関係性を追加
add_or_update_node(G, "p3", type="Person", name="金澤", role="JSON-LD設計")
add_or_update_edge(G, "p3", "f1", "技術支援する")
add_or_update_edge(G, "p1", "p2", "連携する") # 人と人の関係も作れるのがグラフの強み！


# =========================================================
# 3. AI検索のシミュレーション（プロンプトから結果を得る）
# =========================================================
def ask_ai(G, prompt):
    print(f"\n👤 ユーザーのプロンプト:\n  「{prompt}」")
    print("🤖 AI思考プロセス...")
    
    # ※実際のシステムでは、ここでLLMがプロンプトを解釈し、
    # グラフ検索用のクエリ（CypherやSPARQL）を自動生成してDBに投げます。
    # 今回はその「AIの論理思考」をPythonの条件分岐で再現しています。
    
    if "遊休農地" in prompt and "調査" in prompt:
        print("   👉 グラフ探索: [Target: '山間部の遊休農地'] に向かって ['調査する'] エッジを持つ [Person] ノードを検索します...")
        
        # ①「山間部の遊休農地」ノードを探す
        target_id = None
        for n, data in G.nodes(data=True):
            if data.get("name") == "山間部の遊休農地":
                target_id = n
                break
        
        # ②そこに向かって伸びているエッジ（線）を逆引きする
        if target_id:
            for src, dst, edge_data in G.in_edges(target_id, data=True):
                if edge_data.get("label") == "調査する":
                    person_name = G.nodes[src]["name"]
                    print(f"✨ 回答: その遊休農地を調査しているのは「{person_name}」さんです！")
                    return
    
    if "明日を農園" in prompt and ("関わっている" in prompt or "関係" in prompt):
        print("   👉 グラフ探索: [Target: '明日を農園'] に繋がっているすべての [Person] ノードとその関係性を検索します...")
        
        target_id = "f1" # 明日を農園のID
        results = []
        for src, dst, edge_data in G.in_edges(target_id, data=True):
            person_name = G.nodes[src]["name"]
            relation = edge_data.get("label")
            results.append(f"{person_name}さん（{relation}）")
        
        if results:
            ans = "、".join(results)
            print(f"✨ 回答: 明日を農園には、{ans} が関わっています！")
            return

    print("⚠️ 回答: グラフネットワークの中に該当する関係性が見つかりませんでした。")

print("\n✅ 3. AI検索テスト（プロンプト入力）")
ask_ai(G, "山間部の遊休農地を調査しているのは誰ですか？")
ask_ai(G, "明日を農園に関わっているメンバーを教えて。")

from pyvis.network import Network
import os

# =========================================================
# 4. 可視化機能（画面でグリグリ動かす）の追加
# =========================================================
def visualize_graph(G, output_filename="graph_engine_visual.html"):
    print(f"\n🎨 グラフをブラウザ用に描画しています...")
    
    # キャンバスの設定（背景色などを指定）
    net = Network(height="700px", width="100%", directed=True, bgcolor="#222222", font_color="white")
    
    # NetworkXのグラフデータから、Pyvis用のノードを作成
    for node_id, node_data in G.nodes(data=True):
        node_type = node_data.get("type", "Unknown")
        name = node_data.get("name", node_id)
        
        # ノードのタイプ（人か農地か）によって色とポップアップ情報を自動で変える
        if node_type == "Person":
            color = "#3498db" # 人は青色
            title = f"ID: {node_id}\nタイプ: {node_type}\n役割: {node_data.get('role', 'なし')}"
        elif node_type == "Farm":
            color = "#2ecc71" # 農地は緑色
            title = f"ID: {node_id}\nタイプ: {node_type}\n状況: {node_data.get('status', '不明')}"
        else:
            color = "#95a5a6" # その他はグレー
            title = ""
            
        net.add_node(node_id, label=name, title=title, color=color)
        
    # NetworkXのグラフデータから、Pyvis用のエッジ（関係性の線）を作成
    for source, target, edge_data in G.edges(data=True):
        net.add_edge(source, target, title=edge_data.get("label", ""), label=edge_data.get("label", ""))
        
    # ノードが反発しあって綺麗に広がる物理演算の設定
    net.set_options("""
    var options = {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -15000
        }
      }
    }
    """)
    
    # HTMLファイルとして出力
    net.save_graph(output_filename)
    print(f"✅ 可視化完了！MacのFinderから {output_filename} を開いてください。")

# 作成した可視化関数を実行
visualize_graph(G)
