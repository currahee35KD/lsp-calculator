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

st.sidebar.subheader("eBay / Payoneer")
usd_jpy_rate = st.sidebar.number_input("基準為替レート (円/USD)", value=159.0, step=1.0)
payoneer_fee = st.sidebar.number_input("Payoneer為替手数料 (%)", value=2.5, step=0.1)
ebay_fee = st.sidebar.slider("eBay 手数料(%)", 0, 30, 15)
ebay_customs = st.sidebar.slider("eBay 関税等(%)", 0, 20, 10)
ebay_ad = st.sidebar.slider("eBay 広告費(%)", 0, 10, 2)
ebay_ship = st.sidebar.number_input("eBay 国際送料(円)", value=4000, step=500)

# --- 計算ロジック ---
# 1. 獲得LSPの計算
card_lsp = (purchase_price * 0.01) / 400
purchase_price_exc_tax = purchase_price / 1.1
jmp_lsp = (purchase_price_exc_tax * (jmp_rate / 100)) / 100
total_lsp = card_lsp + jmp_lsp

# eBayの共通計算用変数
effective_rate = usd_jpy_rate * (1 - (payoneer_fee / 100))
ebay_total_rate = (ebay_fee + ebay_customs + ebay_ad) / 100

# ==========================================
# 2A. 【利益10%ライン】の計算
# ==========================================
target_return_profit = purchase_price * 1.1 # 仕入れ値 + 10%利益

mercari_target_profit = (target_return_profit + mercari_ship) / (1 - (mercari_fee / 100))
ebay_target_jpy_profit = (target_return_profit + ebay_ship) / (1 - ebay_total_rate)
ebay_target_usd_profit = ebay_target_jpy_profit / effective_rate

# ==========================================
# 2B. 【トントンライン】の計算（損失0円）
# ==========================================
target_return_zero = purchase_price # 仕入れ値をそのまま回収する

mercari_target_zero = (target_return_zero + mercari_ship) / (1 - (mercari_fee / 100))
ebay_target_jpy_zero = (target_return_zero + ebay_ship) / (1 - ebay_total_rate)
ebay_target_usd_zero = ebay_target_jpy_zero / effective_rate

# ==========================================
# 2C. 【目標LSP単価ライン】の計算（許容赤字）
# ==========================================
max_loss = total_lsp * target_lsp
target_return_loss = purchase_price - max_loss # 赤字を許容した回収目標

mercari_target_loss = (target_return_loss + mercari_ship) / (1 - (mercari_fee / 100))
ebay_target_jpy_loss = (target_return_loss + ebay_ship) / (1 - ebay_total_rate)
ebay_target_usd_loss = ebay_target_jpy_loss / effective_rate


# --- メイン画面の表示 ---
st.subheader("💡 獲得予定のLSP")
st.info(f"合計: **{total_lsp:.2f} LSP** （カード分 {card_lsp:.2f} ＋ JMP分 {jmp_lsp:.2f}）")

st.markdown("---")

# 表示ブロック1：利益10%ライン
st.subheader("🚀 利益10%ライン（LSP無料 ＋ 現金利益）")
st.caption(f"手元に現金 {target_return_profit:,.0f} 円が戻り、純利益も出る理想ラインです。")
col1, col2 = st.columns(2)
with col1:
    st.error(f"メルカリ: **{mercari_target_profit:,.0f} 円**") # 難易度が高いので赤色
with col2:
    st.error(f"eBay: **$ {ebay_target_usd_profit:,.2f}**")

st.markdown("<br>", unsafe_allow_html=True)

# 表示ブロック2：トントンライン
st.subheader("👑 トントンライン（損失0円 / LSP完全無料）")
st.caption(f"手元に現金 {target_return_zero:,.0f} 円が戻り、LSPがタダで手に入る神ラインです。")
col3, col4 = st.columns(2)
with col3:
    st.success(f"メルカリ: **{mercari_target_zero:,.0f} 円**")
with col4:
    st.success(f"eBay: **$ {ebay_target_usd_zero:,.2f}**")

st.markdown("<br>", unsafe_allow_html=True)

# 表示ブロック3：目標LSPライン
st.subheader(f"🎯 目標LSP単価ライン（単価 {target_lsp}円）")
st.caption(f"最大 {max_loss:,.0f} 円の赤字まで許容し、手元に {target_return_loss:,.0f} 円戻す現実的ラインです。")
col5, col6 = st.columns(2)
with col5:
    st.warning(f"メルカリ: **{mercari_target_loss:,.0f} 円**")
with col6:
    st.warning(f"eBay: **$ {ebay_target_usd_loss:,.2f}**")

st.caption(f"※eBayは実質レート {effective_rate:,.2f} 円（手数料引後）で換算しています。")
