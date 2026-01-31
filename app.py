import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. 界面与颜色配置 ---
st.set_page_config(page_title="妈妈的茶叶店", layout="wide")

# 使用自定义 CSS 注入茶绿色调
st.markdown("""
    <style>
    .stApp { background-color: #F5F5F5; }
    .main { color: #2E7D32; }
    div[data-testid="stMetricValue"] { color: #2E7D32; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍵 妈妈的茶叶店 - 智能管理专业版")

# --- 2. 数据初始化 ---
INV_FILE = "inventory_v3.csv"
LOG_FILE = "sales_log.csv"

def init_data():
    if not os.path.exists(INV_FILE):
        pd.DataFrame(columns=["大类", "品种", "库存", "单位", "进货单价"]).to_csv(INV_FILE, index=False)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=["日期", "名称", "数量", "单位", "销售额", "成本", "利润"]).to_csv(LOG_FILE, index=False)

init_data()

def get_inv(): return pd.read_csv(INV_FILE)
def save_inv(df): df.to_csv(INV_FILE, index=False)
def get_log(): return pd.read_csv(LOG_FILE)
def save_log(df): df.to_csv(LOG_FILE, index=False)

# --- 3. 侧边栏菜单 ---
with st.sidebar:
    st.image("https://www.gstatic.com/images/icons/material/system/2x/local_library_green_24dp.png")
    menu = st.radio("功能导航", ["📋 实时库存", "📥 进货入库", "💰 售出算账", "📈 利润报表"])
    st.write("---")
    st.info("💡 提示：输入数字时会自动弹出数字键盘。")

# --- 4. 功能实现 ---
inventory = get_inv()

if menu == "📋 实时库存":
    st.subheader("📦 当前库存清单")
    if inventory.empty:
        st.info("目前库房空空的，快去进货吧！")
    else:
        # 低库存高亮：少于10个单位即变红
        def highlight_low_stock(s):
            return ['background-color: #ffcccc' if s.库存 < 10 else '' for _ in s]
        
        st.dataframe(inventory.style.apply(highlight_low_stock, axis=1), use_container_width=True)
        st.write("⚠️ *注：粉色背景表示库存少于 10，请注意补货。*")

elif menu == "📥 进货入库":
    st.subheader("📥 填写入库信息")
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            cat = st.text_input("茶叶分类", placeholder="如：红茶")
            name = st.text_input("茶叶名称", placeholder="如：金骏眉")
        with c2:
            amount = st.number_input("进货数量", min_value=0.0, step=1.0, format="%.1f")
            unit = st.selectbox("单位", ["斤", "克", "泡", "盒", "袋", "个"])
        cost = st.number_input("进货成本单价 (元)", min_value=0.0, step=0.1, format="%.2f")
        
        if st.form_submit_button("确认入库"):
            if cat and name:
                mask = (inventory["大类"] == cat) & (inventory["品种"] == name)
                if mask.any():
                    inventory.loc[mask, "库存"] += amount
                    inventory.loc[mask, "进货单价"] = cost
                else:
                    new_item = {"大类": cat, "品种": name, "库存": amount, "单位": unit, "进货单价": cost}
                    inventory = pd.concat([inventory, pd.DataFrame([new_item])], ignore_index=True)
                save_inv(inventory)
                st.success(f"✅ {name} 成功入库！")
            else:
                st.error("请把名字填完整哦。")

elif menu == "💰 售出算账":
    st.subheader("💰 扫货算账")
    if inventory.empty:
        st.warning("仓库没货，卖不了哦。")
    else:
        options = inventory.apply(lambda x: f"{x['大类']}-{x['品种']}", axis=1).tolist()
        choice = st.selectbox("卖出了哪种茶？", options)
        idx = options.index(choice)
        row = inventory.iloc[idx]
        
        with st.form("sale_form"):
            st.info(f"💡 当前【{row['品种']}】库存：{row['库存']} {row['单位']}")
            c1, c2 = st.columns(2)
            with c1:
                s_amount = st.number_input("销售数量", min_value=0.0, step=1.0, format="%.1f")
            with c2:
                s_price = st.number_input("销售成交单价 (元)", min_value=0.0, step=1.0, format="%.2f")
            
            total_price = s_amount * s_price
            st.markdown(f"### 💵 应收金额：<span style='color:red'>{total_price:.2f}</span> 元", unsafe_allow_html=True)
            
            if st.form_submit_button("确认卖出"):
                if row['库存'] >= s_amount:
                    inventory.loc[idx, "库存"] -= s_amount
                    save_inv(inventory)
                    
                    # 计算利润
                    t_cost = s_amount * row['进货单价']
                    t_profit = total_price - t_cost
                    
                    # 记账
                    log = get_log()
                    new_log = {"日期": datetime.now().strftime("%Y-%m-%d %H:%M"), "名称": choice, 
                               "数量": s_amount, "单位": row['单位'], "销售额": total_price, 
                               "成本": t_cost, "利润": t_profit}
                    save_log(pd.concat([log, pd.DataFrame([new_log])], ignore_index=True))
                    st.balloons()
                    st.success("记账成功！")
                else:
                    st.error("库存不够卖了！")

elif menu == "📈 利润报表":
    st.subheader("📈 经营状况统计")
    log = get_log()
    if log.empty:
        st.info("今天还没开张呢。")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("总营业额", f"¥{log['销售额'].sum():.2f}")
        col2.metric("总成本", f"¥{log['成本'].sum():.2f}")
        col3.metric("总净利润", f"¥{log['利润'].sum():.2f}")
        
        st.write("---")
        st.write("#### 历史成交记录")
        st.dataframe(log.sort_index(ascending=False), use_container_width=True)
        
        # 导出 Excel 按钮
        csv = log.to_csv(index=False).encode('utf-8-sig') # utf-8-sig 保证 Excel 打开不乱码
        st.download_button(label="📥 下载所有账目到手机/电脑", data=csv, file_name=f"茶叶店账单_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')
