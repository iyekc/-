import streamlit as st
import pandas as pd
import os

# 设置页面标题
st.set_page_config(page_title="妈妈的茶叶店库存管理", layout="wide")
st.title("🍵 妈妈的茶叶店 - 库存助手")

# 数据文件路径
DB_FILE = "inventory.csv"

# 初始化数据
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["茶叶名称", "剩余库存(斤)", "备注"])
    df.to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# 加载数据
inventory = load_data()

# --- 侧边栏：操作面板 ---
st.sidebar.header("操作菜单")
action = st.sidebar.selectbox("选择操作", ["查看库存", "进货入库", "售出登记"])

if action == "查看库存":
    st.subheader("📋 当前库存一览")
    # 高亮显示库存不足（少于5斤）
    st.dataframe(inventory.style.highlight_between(left=0, right=5, subset=["剩余库存(斤)"], color="#ffcccc"))
    
elif action == "进货入库":
    st.subheader("📥 增加库存")
    with st.form("add_form"):
        name = st.selectbox("选择或输入茶叶名", ["龙井", "大红袍", "普洱", "铁观音", "其他"])
        if name == "其他":
            name = st.text_input("请输入新茶叶名称")
        amount = st.number_input("进货数量", min_value=0.1, step=0.1)
        note = st.text_input("备注 (如：某某茶场进货)")
        submit = st.form_submit_button("确认入库")
        
        if submit:
            if name in inventory["茶叶名称"].values:
                inventory.loc[inventory["茶叶名称"] == name, "剩余库存(斤)"] += amount
            else:
                new_row = {"茶叶名称": name, "剩余库存(斤)": amount, "备注": note}
                inventory = pd.concat([inventory, pd.DataFrame([new_row])], ignore_index=True)
            save_data(inventory)
            st.success(f"✅ {name} 已更新，当前库存：{inventory.loc[inventory['茶叶名称'] == name, '剩余库存(斤)'].values[0]}")

elif action == "售出登记":
    st.subheader("💰 销售出库")
    with st.form("sell_form"):
        name = st.selectbox("卖出了哪种茶？", inventory["茶叶名称"].unique())
        amount = st.number_input("卖出数量", min_value=0.1, step=0.1)
        submit = st.form_submit_button("确认售出")
        
        if submit:
            current_stock = inventory.loc[inventory["茶叶名称"] == name, "剩余库存(斤)"].values[0]
            if current_stock >= amount:
                inventory.loc[inventory["茶叶名称"] == name, "剩余库存(斤)"] -= amount
                save_data(inventory)
                st.success(f"💰 {name} 卖出 {amount} 斤，剩余 {current_stock - amount} 斤")
            else:
                st.error(f"❌ 库存不足！当前仅剩 {current_stock} 斤")
