import streamlit as st

# 画面のタイトル
st.title("LSPレスキュー：最低出品価格チェッカー")
st.markdown("仕入れ値と目標LSP単価から、メルカリ・eBayで赤字にならない最低出品価格を自動算出します。")

# サイドバー（入力フォーム）
st.sidebar.header("📊 基本設定")
purchase_price = st.sidebar.number_input("入荷価格（税込）", value=4000, step=100)
target_lsp = st.sidebar.number_input("目標LSP単価（円）", value=1000, step=100)
jmp_rate = st.sidebar.number_input("JMPマイル還元率（100円=Xマイル）", value=4.0, step=0.5)

st.sidebar.header("📦 各プラットフォーム設定")
st.sidebar.subheader("メルカリ")
mercari_fee = st.sidebar.slider("メルカリ 手数料(%)", 0, 20, 10)
mercari_ship = st.sidebar.number_input("メルカリ 送料(円)", value=210, step=10)

st.sidebar.subheader("eBay")
usd_jpy_rate = st.sidebar.number_input("為替レート (円/USD)", value=150.0, step=1.0) # ←為替レートを追加
ebay_fee = st.sidebar.slider("eBay 手数料(%)", 0, 30, 15)
ebay_customs = st.sidebar.slider("eBay 関税等(%)", 0, 20, 10)
ebay_ad = st.sidebar.slider("eBay 広告費(%)", 0, 10, 2)
ebay_ship = st.sidebar.number_input("eBay 国際送料(円)", value=4000, step=500)

# --- 計算ロジック ---
# 1. 獲得LSP
card_lsp = (purchase_price * 0.01) / 400
purchase_price_exc_tax = purchase_price / 1.1
jmp_lsp = (purchase_price_exc_tax * (jmp_rate / 100)) / 100
total_lsp = card_lsp + jmp_lsp

# 2. 許容赤字と回収目標
max_loss = total_lsp * target_lsp
target_return = purchase_price - max_loss

# 3. 最低出品価格の逆算
mercari_target = (target_return + mercari_ship) / (1 - (mercari_fee / 100))

ebay_total_rate = (ebay_fee + ebay_customs + ebay_ad) / 100
ebay_target_jpy = (target_return + ebay_ship) / (1 - ebay_total_rate)
ebay_target_usd = ebay_target_jpy / usd_jpy_rate # ←ここでドル換算

# --- メイン画面の表示 ---
st.subheader("💡 シミュレーション結果")
col1, col2 = st.columns(2)
col1.metric("獲得予定LSP", f"{total_lsp:.2f} LSP")
col2.metric("許容できる最大赤字", f"{-max_loss:,.0f} 円")

st.markdown("---")
st.success(f"🟠 メルカリ 最低出品価格: **{mercari_target:,.0f} 円**")
st.info(f"🔵 eBay 最低出品価格: **$ {ebay_target_usd:,.2f}** (約 {ebay_target_jpy:,.0f} 円)") # ←表示をドルに変更

st.caption(f"※どちらの価格で売れても、手元に {target_return:,.0f} 円の現金が戻る計算になっています。")
