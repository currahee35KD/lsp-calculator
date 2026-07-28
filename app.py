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

st.sidebar.header("📦 梱包サイズ・重量設定")
# FedExパックか自前ダンボールかを選択
package_type = st.sidebar.radio(
    "梱包材の種類", 
    ["FedExパック (実重量ベース)", "自前ダンボール (寸法重量ベース)"],
    help="FedExパックを選択するとサイズ(寸法)による切り上げが免除され、実重量のみで計算されます。"
)

item_weight = st.sidebar.number_input("実重量 (kg / 1個あたり)", value=0.3, step=0.1)

# FedExパック選択時は寸法入力を無効化（グレーアウト）する工夫
is_custom_box = "自前ダンボール" in package_type
item_l = st.sidebar.number_input("長さ (cm)", value=30.0, step=1.0, disabled=not is_custom_box)
item_w = st.sidebar.number_input("幅 (cm)", value=15.0, step=1.0, disabled=not is_custom_box)
item_h = st.sidebar.number_input("高さ/厚さ (cm)", value=6.0, step=1.0, disabled=not is_custom_box)

if not is_custom_box:
    st.sidebar.caption("※FedExパック適用時のため寸法入力は無視されます。")

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
def calculate_cpass_cost(qty, pkg_type):
    """個数に応じたCPaSS送料（FICP）と内訳を計算"""
    actual_weight_total = item_weight * qty
    
    # 梱包材による判定分岐
    if "FedExパック" in pkg_type:
        billed_weight = actual_weight_total
    else:
        total_h = item_h * qty
        volumetric_weight = (item_l * item_w * total_h) / 5000
        billed_weight = max(volumetric_weight, actual_weight_total)
        
    # 0.5kg単位で切り上げ（0の場合は最低0.5kg）
    rounded_weight = math.ceil(billed_weight * 2) / 2
    if rounded_weight == 0:
        rounded_weight = 0.5
        
    base_cost = ficp_base_rates.get(rounded_weight, 7000)
    
    # 内訳の計算
    shipping_with_surcharge = base_cost * surcharge_multiplier
    final_cost = shipping_with_surcharge + cpass_handling_fee
    
    return final_cost, rounded_weight, base_cost, shipping_with_surcharge, cpass_handling_fee

# --- 基本計算ロジック (1個売り) ---
card_lsp = (purchase_price * 0.01) / 400
purchase_price_exc_tax = purchase_price / 1.1
jmp_lsp = (purchase_price_exc_tax * (jmp_rate / 100)) / 100
total_lsp = card_lsp + jmp_lsp

effective_rate = usd_jpy_rate * (1 - (payoneer_fee / 100))
ebay_total_rate = (ebay_fee + ebay_ad + ebay_customs) / 100

# 1個売りの送料と内訳を取得
shipping_cost_1pc, billed_weight_1pc, base_1pc, sur_ship_1pc, ddp_fee_1pc = calculate_cpass_cost(1, package_type)

target_return_profit = purchase_price * 1.1
target_return_zero = purchase_price
max_loss = total_lsp * target_lsp
target_return_loss = purchase_price - max_loss

ebay_target_jpy_profit = (target_return_profit + shipping_cost_1pc) / (1 - ebay_total_rate)
ebay_usd_profit_1pc = ebay_target_jpy_profit / effective_rate

# 目標販売価格に対する関税額（JPY）を計算
customs_duty_jpy = (ebay_usd_profit_1pc * effective_rate) * (ebay_customs / 100)

ebay_target_jpy_zero = (target_return_zero + shipping_cost_1pc) / (1 - ebay_total_rate)
ebay_usd_zero_1pc = ebay_target_jpy_zero / effective_rate

ebay_target_jpy_loss = (target_return_loss + shipping_cost_1pc) / (1 - ebay_total_rate)
ebay_usd_loss_1pc = ebay_target_jpy_loss / effective_rate

mercari_target_profit = (target_return_profit + mercari_ship) / (1 - (mercari_fee / 100))
mercari_target_zero = (target_return_zero + mercari_ship) / (1 - (mercari_fee / 100))
mercari_target_loss = (target_return_loss + mercari_ship) / (1 - (mercari_fee / 100))

# --- メイン画面表示 ---
st.subheader("💡 獲得予定のLSP (1個あたり)")
st.info(f"合計: **{total_lsp:.2f} LSP** （カード分 {card_lsp:.2f} ＋ JMP分 {jmp_lsp:.2f}）")

st.markdown("---")
st.subheader(f"🚀 1個売りの最低出品価格")
st.markdown(f"**適用重量**: {billed_weight_1pc:.1f}kg / **送料総額 予測**: **{shipping_cost_1pc:,.0f} 円**")

# 内訳表示（見やすくボックス化）
st.caption(f"**【CPaSS送料・関税の内訳 (利益10%設定時)】**\n"
           f"① 運賃（基本料金）: {base_1pc:,.0f} 円\n"
           f"② 燃油等サーチャージ込運賃 (① × {surcharge_multiplier}): {sur_ship_1pc:,.0f} 円\n"
           f"③ CPaSS関税処理手数料 (DDP固定費): {ddp_fee_1pc:,.0f} 円\n"
           f"④ 予測される関税額 (米国 {ebay_customs}%): 約 {customs_duty_jpy:,.0f} 円\n"
           f"※②と③の合計額、および④の関税を考慮した上で下記の出品価格が算出されています。")

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

if "FedExパック" in package_type:
    st.info("💡 現在「FedExパック」が選択されているため、実重量ベースで計算されています。実際の梱包時にパックに収まる個数かどうかにご注意ください。")

cols = st.columns(5)
cols[0].markdown("**個数**")
cols[1].markdown("**適用重量**")
cols[2].markdown("**CPaSS総額 予測**")
cols[3].markdown("**目標売上(USD)**")
cols[4].markdown("**提示可能な割引率**")

for qty in [2, 3, 4]:
    multi_cost_jpy, applied_weight, _, _, _ = calculate_cpass_cost(qty, package_type)
    
    target_return_multi = target_return_profit * qty
    required_jpy_multi = (target_return_multi + multi_cost_jpy) / (1 - ebay_total_rate)
    required_usd_multi = required_jpy_multi / effective_rate
    
    no_discount_usd = ebay_usd_profit_1pc * qty
    
    if no_discount_usd > 0:
        discount_rate = (1 - (required_usd_multi / no_discount_usd)) * 100
    else:
        discount_rate = 0
        
    cols = st.columns(5)
    cols[0].markdown(f"**{qty} 個**")
    cols[1].markdown(f"{applied_weight:.1f} kg")
    cols[2].markdown(f"約 {multi_cost_jpy:,.0f} 円")
    cols[3].markdown(f"$ {required_usd_multi:,.2f}")
    
    if discount_rate > 0:
        cols[4].success(f"最大 **{discount_rate:.1f} %** オフ可能")
    else:
        cols[4].error("割引不可（寸法オーバー）")
