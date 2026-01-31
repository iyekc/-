import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 页面配置
st.set_page_config(page_title="茶叶店助手", layout="wide")
st.title("🍵 妈妈的茶叶店 - 智能管理专业版")

# 文件路径
INV_FILE = "inventory_v3.csv"  # 库存表
LOG_FILE = "sales_log.csv"     # 销售流水表（算利润用）

# 初始化数据表
def init_data():
    if not os.path.exists(INV_FILE):
        df = pd.DataFrame(columns=["大类", "品种", "库存", "单位", "进货单价"])
        df.to_csv(INV_FILE, index=False)
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=["日期", "名称", "数量", "单位", "销售额", "成本", "利润"])
        df.to_csv(LOG_FILE, index=False)

init_data()

# 加载和保存函数
def get_inv(): return pd.read_csv(INV_FILE)
def save_inv(df): df.to_csv(INV_FILE, index=False)
def get_log(): return pd.read_csv(LOG_FILE)
def save_log(df): df.to_csv(LOG_FILE, index=False)

# --- 侧边栏 ---
menu = st.sidebar.radio("功能菜单", ["📋 实时库存", "📥 进货入库", "💰 售出算账", "📈 利润报表"])

# 1. 查看库存
if menu == "📋 实时库存":
    st.subheader("库存清单")
    df = get_inv()
    if df.empty: st.info("暂无库存，请先进货。")
    else: st.dataframe(df, use_container_width=True)

# 2. 进货入库
elif menu == "📥 进货入库":
    st.subheader("新茶入库")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            cat = st.text_input("茶叶大类 (如: 岩茶)")
            name = st.text_input("具体品种 (如: 肉桂)")
        with c2:
            # 这里的 step=0.1 和 min_value 在手机端通常会触发数字键盘
            amount = st.number_input("进货数量", min_value=0.0, step=1.0, format="%.1f")
            unit = st.selectbox("单位", ["斤", "克", "泡", "盒", "袋", "个"])
        
        cost_price = st.number_input("成本单价 (元)", min_value=0.0, step=1.0, format="%.2f")
        if st.form_submit_button("确认入库"):
            inv = get_inv()
            mask = (inv["大类"] == cat) & (inv["品种"] == name)
            if mask.any():
                inv.loc[mask, "库存"] += amount
                inv.loc[mask, "进货单价"] = cost_price # 更新最新成本
            else:
                new_data = {"大类":cat, "品种":name, "库存":amount, "单位":unit, "进货单价":cost_price}
                inv = pd.concat([inv, pd.DataFrame([new_data])], ignore_index=True)
            save_inv(inv)
            st.success("入库成功！")

# 3. 售出算账
elif menu == "💰 售出算账":
    st.subheader("销售登记")
    inv = get_inv()
    if inv.empty: st.warning("没有库存可以售卖。")
    else:
        # 选择茶叶
        options = inv.apply(lambda x: f"{x['大类']}-{x['品种']}", axis=1).tolist()
        choice = st.selectbox("选择卖出的茶叶", options)
        idx = options.index(choice)
        row = inv.iloc[idx]
        
        with st.form("sale_form"):
            st.info(f"当前库存: {row['库存']} {row['单位']} | 成本价参考: {row['进货单价']}元")
            col1, col2 = st.columns(2)
            with col1:
                s_amount = st.number_input("卖出数量", min_value=0.0, step=1.0, format="%.1f")
            with col2:
                s_price = st.number_input("零售单价 (元)", min_value=0.0, step=1.0, format="%.2f")
            
            total_sell = s_amount * s_price
            st.write(f"### 💰 应收金额: {total_sell:.2f} 元")
            
            if st.form_submit_button("确认成交"):
                if row['库存'] >= s_amount:
                    # 1. 减库存
                    inv.loc[idx, "库存"] -= s_amount
                    save_inv(inv)
                    
                    # 2. 记流水 (算利润)
                    total_cost = s_amount * row['进货单价']
                    profit = total_sell - total_cost
                    log = get_log()
                    new_log = {
                        "日期": datetime.now().strftime("%Y-%m-%d"),
                        "名称": f"{row['大类']}-{row['品种']}",
                        "数量": s_amount,
                        "单位": row['单位'],
                        "销售额": total_sell,
                        "成本": total_cost,
                        "利润": profit
                    }
                    log = pd.concat([log, pd.DataFrame([new_log])], ignore_index=True)
                    save_log(log)
                    st.balloons()
                    st.success(f"成交！净赚 {profit:.2f} 元")
                else:
                    st.error("库存不足！")

# 4. 利润报表
elif menu == "📈 利润报表":
    st.subheader("简易利润表")
    log = get_log()
    if log.empty: st.info("暂无销售记录。")
    else:
        # 显示统计数据
        total_s = log["销售额"].sum()
        total_c = log["成本"].sum()
        total_p = log["利润"].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("总营业额", f"{total_s:.2f} 元")
        c2.metric("总成本", f"{total_c:.2f} 元")
        c3.metric("净利润", f"{total_p:.2f} 元", delta=f"{total_p/total_s:.1%}" if total_s !=0 else None)
        
        st.write("---")
        st.write("#### 销售明细历史")
        st.dataframe(log.sort_index(ascending=False), use_container_width=True)
        
        if st.button("清空所有历史记录"):
            if st.confirm("确定要清空吗？此操作不可撤销"):
                os.remove(LOG_FILE)
                st.rerun()
