import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 设置页面
st.set_page_config(page_title="妈妈的茶叶店库存管理", layout="wide")
st.title("🍵 妈妈的茶叶店 - 智能管理系统")

DB_FILE = "inventory_v2.csv"

# 初始化数据，增加了分类、单位和价格相关字段
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["大类", "具体茶名", "剩余库存", "单位", "最近单价", "最后更新时间"])
    df.to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

inventory = load_data()

# --- 侧边栏 ---
action = st.sidebar.selectbox("选择操作", ["📦 查看库存", "📥 进货入库", "💰 售出算账"])

if action == "📦 查看库存":
    st.subheader("📋 当前库存一览")
    if inventory.empty:
        st.info("目前还没有库存，请先去【进货入库】吧！")
    else:
        # 按大类排序显示
        st.dataframe(inventory.sort_values("大类"), use_container_width=True)

elif action == "📥 进货入库":
    st.subheader("📥 进货入库")
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            cat = st.text_input("茶叶大类", placeholder="如：红茶、岩茶")
            name = st.text_input("具体品种", placeholder="如：正山小种、肉桂")
        with col2:
            amount = st.number_input("进货数量", min_value=0.0, step=0.1)
            unit = st.selectbox("计量单位", ["斤", "克", "盒", "袋", "个"])
        
        price = st.number_input("进货单价 (元)", min_value=0.0, step=1.0)
        submit = st.form_submit_button("确认入库")
        
        if submit and cat and name:
            # 判断是否已存在（大类和品种都一样）
            mask = (inventory["大类"] == cat) & (inventory["具体茶名"] == name)
            if mask.any():
                inventory.loc[mask, "剩余库存"] += amount
                inventory.loc[mask, "最近单价"] = price
                inventory.loc[mask, "最后更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            else:
                new_row = {
                    "大类": cat, "具体茶名": name, "剩余库存": amount, 
                    "单位": unit, "最近单价": price, 
                    "最后更新时间": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                inventory = pd.concat([inventory, pd.DataFrame([new_row])], ignore_index=True)
            save_data(inventory)
            st.success(f"✅ {cat}-{name} 已入库！")

elif action == "💰 售出算账":
    st.subheader("💰 售出算账")
    if inventory.empty:
        st.warning("库里没茶，没法卖哦~")
    else:
        # 让妈妈选茶叶，显示格式：大类-品种
        options = inventory.apply(lambda x: f"{x['大类']}-{x['具体茶名']}", axis=1).tolist()
        choice = st.selectbox("卖出了哪种茶？", options)
        
        # 获取选中行的信息
        selected_cat = choice.split("-")[0]
        selected_name = choice.split("-")[1]
        row = inventory[(inventory["大类"] == selected_cat) & (inventory["具体茶名"] == selected_name)].iloc[0]
        
        with st.form("sell_form"):
            st.info(f"当前库存：{row['剩余库存']} {row['单位']}")
            col1, col2 = st.columns(2)
            with col1:
                sell_amount = st.number_input(f"卖出数量 ({row['单位']})", min_value=0.0, step=0.1)
            with col2:
                sell_price = st.number_input("成交单价 (元)", min_value=0.0, value=float(row['最近单价']))
            
            total_money = sell_amount * sell_price
            st.write(f"### 💵 应收金额：{total_money:.2f} 元")
            
            submit = st.form_submit_button("确认成交并减库存")
            
            if submit:
                if row['剩余库存'] >= sell_amount:
                    inventory.loc[(inventory["大类"] == selected_cat) & (inventory["具体茶名"] == selected_name), "剩余库存"] -= sell_amount
                    save_data(inventory)
                    st.balloons() # 庆祝成交的小动画
                    st.success(f"✅ 成交！已自动扣除库存。")
                else:
                    st.error("❌ 库存不够卖啦！")
