import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import matplotlib

# 🔤 日本語フォント設定（macOS向け）
matplotlib.rcParams['font.family'] = 'Hiragino Sans'

# タイトル
st.title("政党支持率入力 & 集計ツール")

# ==============================
# 📝 支持率の手動入力・CSV保存
# ==============================

st.header("📝 支持率を手動で入力してCSV保存")

source = st.selectbox(
    "📰 データソースを選択してください", 
    ["NHK", "朝日新聞", "FNN", "JNN", "選挙ドットコム（電話）", "選挙ドットコム（ネット）", "その他"]
)

survey_date = st.date_input("📅 調査日を入力してください", value=date.today())

manual_parties = [
    "自民党", "立憲民主党", "日本維新の会", "公明党", "共産党", 
    "国民民主党", "れいわ新選組", "社民党", "参政党", "日本保守党", 
    "みんなでつくる党", "支持なし"
]
auto_party = "その他"

st.subheader("各政党の支持率を入力してください（％）")
support_rates = {}
for party in manual_parties:
    rate = st.number_input(
        f"{party} の支持率（％）", 
        min_value=0.0, max_value=100.0, step=0.1,
        key=f"rate_{party}"
    )
    support_rates[party] = rate

# 「その他」の自動計算
total_manual = sum(support_rates.values())
st.markdown(f"🔢 **現在の合計支持率（その他を除く）**：{total_manual:.1f}％")

if total_manual > 100:
    st.error("⚠️ 入力値の合計が100％を超えています。「その他」は自動計算できません。")
    support_rates[auto_party] = "エラー"
else:
    support_rates[auto_party] = round(100 - total_manual, 1)

# 表示
df = pd.DataFrame({
    "政党": list(support_rates.keys()),
    "支持率": list(support_rates.values())
})

def format_support(val):
    return val if isinstance(val, str) else f"{val:.1f}%"

st.subheader("📊 入力内容の確認")
st.dataframe(df.style.format({"支持率": format_support}))

# CSV保存
df_export = df.copy()
df_export["データソース"] = source
df_export["調査日"] = survey_date.strftime("%Y-%m-%d")
csv = df_export.to_csv(index=False, encoding="utf-8-sig")

if support_rates[auto_party] == "エラー":
    st.warning("⚠️ 「その他」が計算できないため、CSVは保存できません。")
else:
    st.download_button(
        label="💾 入力内容をCSVとして保存",
        data=csv,
        file_name=f"支持率_{source}_{survey_date.strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ==============================
# 📂 平均値算出 + グラフ表示
# ==============================

st.markdown("---")
st.header("📂 複数CSVから平均支持率を算出")

uploaded_files = st.file_uploader(
    "複数のCSVファイルを選択してください",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    combined_df = pd.DataFrame()
    
    for file in uploaded_files:
        df = pd.read_csv(file)
        df = df[df["支持率"].apply(lambda x: str(x).replace('.', '', 1).isdigit())]
        df["支持率"] = df["支持率"].astype(float)
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    
    avg_df = combined_df.groupby("政党")["支持率"].mean().reset_index()

    # 並び順・色指定
    desired_order = [
        "自民党", "公明党", "立憲民主党", "日本維新の会", "国民民主党", 
        "参政党", "れいわ新選組", "共産党", "日本保守党", "社民党", 
        "みんなでつくる党", "その他", "支持なし"
    ]
    party_colors = {
        "自民党": "red",
        "公明党": "navy",
        "立憲民主党": "blue",
        "日本維新の会": "yellowgreen",
        "国民民主党": "gold",
        "参政党": "orange",
        "れいわ新選組": "deeppink",
        "共産党": "firebrick",
        "日本保守党": "skyblue",
        "社民党": "mediumorchid",
        "みんなでつくる党": "purple",
        "その他": "black",
        "支持なし": "gray"
    }

    avg_df["政党"] = pd.Categorical(avg_df["政党"], categories=desired_order, ordered=True)
    avg_df = avg_df.sort_values("政党")

    st.subheader("📊 政党別 平均支持率")
    st.dataframe(avg_df.style.format({"支持率": "{:.2f}%"}))

    # グラフ表示（カスタム色 + 並び順）
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(
        avg_df["政党"],
        avg_df["支持率"],
        color=[party_colors.get(p, "#888888") for p in avg_df["政党"]]
    )

    ax.set_title("政党別 平均支持率", fontsize=16)
    ax.set_ylabel("支持率（％）", fontsize=12)
    ax.set_ylim(0, max(avg_df["支持率"]) * 1.15)
    ax.tick_params(axis='x', rotation=45)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    st.pyplot(fig)
else:
    st.info("上で保存したCSVファイルを複数アップロードしてください。")

# ---------------------
# 📈 時系列グラフセクション
# ---------------------
st.header("📈 時系列支持率グラフ")

# アップロードエリア（CSVまたはExcel）
time_series_file = st.file_uploader(
    "📂 時系列グラフに使用するCSVまたはExcelファイルをアップロードしてください",
    type=["csv", "xlsx"]
)

if time_series_file:
    # ファイル読み込み
    if time_series_file.name.endswith("xlsx"):
        df_ts = pd.read_excel(time_series_file)
    else:
        df_ts = pd.read_csv(time_series_file)
    
    # 前処理
    df_ts = df_ts.dropna(subset=["支持率"])
    df_ts["調査日"] = pd.to_datetime(df_ts["調査日"])

    # 政党選択
    all_parties = [
        "自民党", "公明党", "立憲民主党", "日本維新の会", "国民民主党",
        "参政党", "れいわ新選組", "共産党", "日本保守党", "社民党",
        "みんなでつくる党", "その他", "支持なし"
    ]

    selected_parties = st.multiselect(
        "表示する政党を選択してください（複数可）",
        options=all_parties,
        default=["自民党", "立憲民主党", "日本維新の会"]
    )

    # データ整形
    pivot_df = df_ts[df_ts["政党"].isin(selected_parties)].pivot_table(
        index="調査日", columns="政党", values="支持率", aggfunc="mean"
    ).sort_index()

    # 色と順序の定義
    party_colors = {
        "自民党": "red", "公明党": "navy", "立憲民主党": "blue",
        "日本維新の会": "yellowgreen", "国民民主党": "gold", "参政党": "orange",
        "れいわ新選組": "pink", "共産党": "brown", "日本保守党": "skyblue",
        "社民党": "gray", "みんなでつくる党": "purple", "その他": "black",
        "支持なし": "lightgray"
    }

    party_order = [
        "自民党", "公明党", "立憲民主党", "日本維新の会", "国民民主党",
        "参政党", "れいわ新選組", "共産党", "日本保守党", "社民党",
        "みんなでつくる党", "その他", "支持なし"
    ]

    # グラフ描画
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'Hiragino Sans'  # Mac用フォント指定

    fig, ax = plt.subplots(figsize=(12, 6))
    for party in party_order:
        if party in selected_parties and party in pivot_df.columns:
            ax.plot(pivot_df.index, pivot_df[party], label=party, color=party_colors.get(party, None))
    
    ax.set_title("政党別 支持率の推移", fontsize=16)
    ax.set_xlabel("調査日")
    ax.set_ylabel("支持率（%）")
    ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1))
    ax.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)

else:
    st.info("CSVまたはExcelファイルをアップロードしてください。")
