import math
import streamlit as st

# 画面のタイトル
st.title("LSPレスキュー：最低出品価格＆まとめ売りチェッカー")
st.markdown("仕入れ値・LSP目標からの最低出品価格と、同梱時の安全な「まとめ売り割引率」を自動算出します。")

# サイドバー（入力フォーム）
st.sidebar.header("📊 基本設定 (1個あたり)")
purchase_price = st.sidebar.number_input("入荷価格（税込）", value=4000, step=100)
target_lsp = st.sidebar.number_input("目標LSP単価（円）", value=1000, step=100)
jmp_rate = st.sidebar.number_input("JMPマイル還元率（100円=Xマイル）", value=4.0, step=0.5)

st.sidebar.header("📦 梱包サイズ・重量設定 (1個あたり)")
item_weight = st.sidebar.number_input("実重量 (kg)", value=0.3, step=0.1)
item_l = st.sidebar.number_input("長さ (cm)", value=30.0, step=1.0)
item_w = st.sidebar.number_input("幅 (cm)", value=15.0, step=1.0)
item_h = st.sidebar.number_input("高さ/厚さ (cm)", value=6.0, step=1.0)

st.sidebar.header("✈️ プラットフォーム & 配送設定")
st.sidebar.subheader("メルカリ")
mercari_fee = st.sidebar.slider("メルカリ 手数料(%)", 0, 20, 10)
mercari_ship = st.sidebar.number_input("メルカリ 送料(円)", value=210, step=10)

st.sidebar.subheader("eBay / Payoneer")
usd_jpy_rate = st.sidebar.number_input("基準為替レート (円/USD)", value=160.0, step=1.0)
payoneer_fee = st.sidebar.number_input("Payoneer為替手数料 (%)", value=2.5, step=0.1)
ebay_fee = st.sidebar.slider("eBay 手数料(%)", 0.0, 30.0, 15.0, step=0.5)
ebay_ad = st.sidebar.slider("eBay 広告費(%)", 0.0, 10.0, 2.0, step=0.5)

st.sidebar.subheader("CPaSS / DDP 設定")
ebay_customs = st.sidebar.number_input("米国関税率 (%)", value=12.5, step=0.5)
cpass_handling_fee = st.sidebar.number_input("CPaSS関税処理手数料 (最低固定費・円)", value=850, step=50)
surcharge_multiplier = st.sidebar.number_input("CPaSS 燃油等サーチャージ倍率", value=2.10, step=0.01)

# FICP 米国(Zone F) 基本料金テーブル (kg: 基本料金)
ficp_base_rates = {
    0.5: 2115, 1.0: 2599, 1.5: 2840, 2.0: 3108, 
    2.5: 3383, 3.0: 3540, 3.5: 3593, 4.0: 4022,
    4.5: 4451, 5.0: 4718, 5.5: 5043, 6.0: 5366,
    6.5: 5735, 7.0: 6184, 7.5: 6683, 8.0: 6871
}

# --- CPaSS 送料計算関数 ---
def calculate_cpass_cost(qty):
    """個数に応じたCPaSS送料（FICP）を計算"""
    # 商品を重ねる（厚みが増す）と仮定して寸法を計算
    total_h = item_h * qty
    
    # 寸法重量の計算 (長さ×幅×高さ / 5000)
    volumetric_weight = (item_l * item_w * total_h) / 5000
    actual_weight_total = item_weight * qty
    
    # 実重量と寸法重量の大きい方を適用
    billed_weight = max(volumetric_weight, actual_weight_total)
    
    # 0.5kg単位で切り上げ
    rounded_weight = math.ceil(billed_weight * 2) / 2
    
    # テーブルから基本料金を取得（上限オーバー時は一旦7000円でフェイルセーフ）
    base_cost = ficp_base_rates.get(rounded_weight, 7000)
    
    # サーチャージ倍率を掛け、関税処理手数料(DDPの固定費)を足す
    # ※CPaSSの送料計算機には「DDPの関税処理手数料」は含まれないため、アプリ側で確実に合算して赤字を防ぎます。
    final_cost = (base_cost * surcharge_multiplier) + cpass_handling_fee
    
    return final_cost, rounded_weight

# --- 基本計算ロジック (1個売り) ---
# 1. 獲得LSPの計算
card_lsp = (purchase_price * 0.01) / 400
purchase_price_exc_tax = purchase_price / 1.1
jmp_lsp = (purchase_price_exc_tax * (jmp_rate / 100)) / 100
total_lsp = card_lsp + jmp_lsp

# 実質の為替レート
effective_rate = usd_jpy_rate * (1 - (payoneer_fee / 100))
ebay_total_rate = (ebay_fee + ebay_ad + ebay_customs) / 100

# 1個売りの送料を取得
shipping_cost_1pc, billed_weight_1pc = calculate_cpass_cost(1)

# 目標回収額の定義
target_return_profit = purchase_price * 1.1 # 利益10%
target_return_zero = purchase_price # トントン
max_loss = total_lsp * target_lsp
target_return_loss = purchase_price - max_loss # LSP目標許容赤字

# 1個売りのeBay目標販売価格 (USD)
ebay_target_jpy_profit = (target_return_profit + shipping_cost_1pc) / (1 - ebay_total_rate)
ebay_usd_profit_1pc = ebay_target_jpy_profit / effective_rate

ebay_target_jpy_zero = (target_return_zero + shipping_cost_1pc) / (1 - ebay_total_rate)
ebay_usd_zero_1pc = ebay_target_jpy_zero / effective_rate

ebay_target_jpy_loss = (target_return_loss + shipping_cost_1pc) / (1 - ebay_total_rate)
ebay_usd_loss_1pc = ebay_target_jpy_loss / effective_rate

# 1個売りのメルカリ目標販売価格 (JPY)
mercari_target_profit = (target_return_profit + mercari_ship) / (1 - (mercari_fee / 100))
mercari_target_zero = (target_return_zero + mercari_ship) / (1 - (mercari_fee / 100))
mercari_target_loss = (target_return_loss + mercari_ship) / (1 - (mercari_fee / 100))


# --- メイン画面表示 ---
st.subheader("💡 獲得予定のLSP (1個あたり)")
st.info(f"合計: **{total_lsp:.2f} LSP** （カード分 {card_lsp:.2f} ＋ JMP分 {jmp_lsp:.2f}）")

st.markdown("---")
st.subheader(f"🚀 1個売りの最低出品価格 (適用重量: {billed_weight_1pc:.1f}kg / 送料予測: {shipping_cost_1pc:,.0f}円)")

col1, col2, col3 = st.columns(3)
with col1:
    st.error("利益10%ライン")
    st.write(f"eBay: **$ {ebay_usd_profit_1pc:,.2f}**")
    st.write(f"メルカリ: **{mercari_target_profit:,.0f} 円**")
with col2:
    st.success("トントンライン")
    st.write(f"eBay: **$ {ebay_usd_zero_1pc:,.2f}**")
    st.write(f"メルカリ: **{mercari_target_zero:,.0f} 円**")
with col3:
    st.warning(f"LSP単価{target_lsp}円ライン")
    st.write(f"eBay: **$ {ebay_usd_loss_1pc:,.2f}**")
    st.write(f"メルカリ: **{mercari_target_loss:,.0f} 円**")


st.markdown("---")
# --- まとめ売り（Volume Pricing）シミュレーション ---
st.subheader("🛒 まとめ売り（Volume Pricing）最適割引率")
st.markdown("1個売りと同じ「利益10%」を維持したまま、同梱によって浮いた送料分で提示できる**最大割引率**です。")

# テーブル用データの作成
cols = st.columns(5)
cols[0].markdown("**個数**")
cols[1].markdown("**適用重量**")
cols[2].markdown("**CPaSS送料予測**")
cols[3].markdown("**目標売上(USD)**")
cols[4].markdown("**提示可能な割引率**")

for qty in [2, 3, 4]:
    multi_cost_jpy, applied_weight = calculate_cpass_cost(qty)
    
    # 複数個口の目標利益（1個あたりの「利益10%回収額」× 個数）
    target_return_multi = target_return_profit * qty
    
    # 複数個口の場合に必要なeBay総売上(USD)を逆算
    required_jpy_multi = (target_return_multi + multi_cost_jpy) / (1 - ebay_total_rate)
    required_usd_multi = required_jpy_multi / effective_rate
    
    # 割引なしで単純に個数倍した場合の売上(USD)
    no_discount_usd = ebay_usd_profit_1pc * qty
    
    # 割引率の算出
    if no_discount_usd > 0:
        discount_rate = (1 - (required_usd_multi / no_discount_usd)) * 100
    else:
        discount_rate = 0
        
    # 行の表示
    cols = st.columns(5)
    cols[0].markdown(f"**{qty} 個**")
    cols[1].markdown(f"{applied_weight:.1f} kg")
    cols[2].markdown(f"約 {multi_cost_jpy:,.0f} 円")
    cols[3].markdown(f"$ {required_usd_multi:,.2f}")
    
    if discount_rate > 0:
        cols[4].success(f"最大 **{discount_rate:.1f} %** オフ可能")
    else:
        cols[4].error("割引不可（寸法オーバー）")

st.caption("※送料予測には、CPaSS計算機には表示されないDDP関税処理手数料（立替固定費）もあらかじめ合算しています。安全マージンを取った確実な数値です。")
