import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. 登录验证逻辑 ---
def check_password():
    """只有输入正确密码才返回 True"""
    def password_entered():
        # 这里会比对我们在 Streamlit 后台 Secrets 设置的 db_password
        if st.session_state["password"] == st.secrets["db_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🍵 欢迎来到妈妈的茶叶店")
        st.text_input("请输入管理密码以开启系统", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("密码错误，请重新输入", type="password", on_change=password_entered, key="password")
        st.error("😕 密码不对哦，请核实后再输入。")
        return False
    else:
        return True

# --- 只有登录成功才运行以下代码 ---
if check_password():
    # 页面基础配置
    st.set_page_config(page_title="妈妈的茶叶店库存管理", layout="wide")

    # 注入茶绿色调 CSS
    st.markdown("""
        <style>
        .stApp { background-color: #F5F5F5; }
        .main { color: #1B5E20; }
        div[data-testid="stMetricValue"] { color: #2E7D32; }
        .stButton>button { background-color: #2E7D32; color: white; border-radius: 8px; }
        </style>
        """, unsafe_allow_html=True)

    # 数据文件初始化
    INV_FILE = "inventory_v3.csv"
    LOG_FILE = "sales_log.csv"

    def init_data():
        if not os.path.exists(INV_FILE):
            pd.DataFrame(columns=["大类", "品种", "库存", "单位", "进货单价"]).to_csv(INV_FILE, index=False)
        if not os.path.exists(LOG_FILE):
            pd.DataFrame(columns=["日期", "名称", "数量", "单位", "销售额", "成本", "利润"]).to_csv(LOG_FILE, index=False)

    init_data()

    # 读取数据
    def get_inv(): return pd.read_csv(INV_FILE)
    def save_inv(df): df.to_csv(INV_FILE, index=False)
    def get_log(): return pd.read_csv(LOG_FILE)
    def save_log(df): df.to_csv(LOG_FILE, index=False)

    st.title("🍵 妈妈的茶叶店 - 智能管理系统")

    # --- 侧边栏菜单 ---
    with st.sidebar:
        st.header("功能导航")
        menu = st.radio("请选择操作", ["📋 实时库存", "📥 进货入库", "💰 售出算账", "📈 利润报表"])
        st.write("---")
        if st.button("退出登录"):
            st.session_state["password_correct"] = False
            st.rerun()

    inventory = get_inv()

    # --- 逻辑 1: 查看库存 ---
    if menu == "📋 实时库存":
        st.subheader("📦 当前库存清单")
        if inventory.empty:
            st.info("目前库房空空的，快去进货吧！")
        else:
            # 库存少于10单位高亮显示
            def highlight_low_stock(s):
                return ['background-color: #ffcccc' if s.库存 < 10 else '' for _ in s]
            
            st.dataframe(inventory.style.apply(highlight_low_stock, axis=1), use_container_width=True)
            st.caption("提示：粉色行代表库存少于 10，提醒补货。")

    # --- 逻辑 2: 进货入库 ---
    elif menu == "📥 进货入库":
        st.subheader("📥 填写入库信息")
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                cat = st.text_input("茶叶分类", placeholder="如：红茶、绿茶")
                name = st.text_input("茶叶品种", placeholder="如：金骏眉、西湖龙井")
            with c2:
                amount = st.number_input("进货数量", min_value=0.0, step=1.0, format="%.1f")
                unit = st.selectbox("单位", ["斤", "克", "泡", "盒", "袋", "个"])
            
            cost = st.number_input("进货成本单价 (元)", min_value=0.0, step=0.1, format="%.2f")
            
            if st.form_submit_button("确认入库"):
                if cat and name:
                    mask = (inventory["大类"] == cat) & (inventory["品种"] == name)
                    if mask.any():
                        # 已有品种则累加库存并更新最近成本
                        inventory.loc[mask, "库存"] += amount
                        inventory.loc[mask, "进货单价"] = cost
                    else:
                        # 新增品种
                        new_item = {"大类": cat, "品种": name, "库存": amount, "单位": unit, "进货单价": cost}
                        inventory = pd.concat([inventory, pd.DataFrame([new_item])], ignore_index=True)
                    save_inv(inventory)
                    st.success(f"✅ {name} 入库成功！")
                else:
                    st.error("请完整填写大类和品种名称。")

    # --- 逻辑 3: 售出算账 ---
    elif menu == "💰 售出算账":
        st.subheader("💰 销售算账与出库")
        if inventory.empty:
            st.warning("暂无库存，请先进货。")
        else:
            options = inventory.apply(lambda x: f"{x['大类']}-{x['品种']}", axis=1).tolist()
            choice = st.selectbox("卖出了哪种茶？", options)
            idx = options.index(choice)
            row = inventory.iloc[idx]
            
            with st.form("sale_form"):
                st.info(f"💡 当前库存：{row['库存']} {row['单位']} | 成本单价：{row['进货单价']} 元")
                c1, c2 = st.columns(2)
                with c1:
                    s_amount = st.number_input("卖出数量", min_value=0.0, step=1.0, format="%.1f")
                with c2:
                    s_price = st.number_input("销售单价 (元)", min_value=0.0, step=1.0, format="%.2f")
                
                total_price = s_amount * s_price
                st.markdown(f"### 💵 应收金额：:red[{total_price:.2f}] 元")
                
                if st.form_submit_button("确认成交"):
                    if row['库存'] >= s_amount:
                        # 更新库存
                        inventory.loc[idx, "库存"] -= s_amount
                        save_inv(inventory)
                        
                        # 记录流水算利润
                        t_cost = s_amount * row['进货单价']
                        t_profit = total_price - t_cost
                        
                        log = get_log()
                        new_log = {
                            "日期": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "名称": choice,
                            "数量": s_amount,
                            "单位": row['单位'],
                            "销售额": total_price,
                            "成本": t_cost,
                            "利润": t_profit
                        }
                        save_log(pd.concat([log, pd.DataFrame([new_log])], ignore_index=True))
                        st.balloons()
                        st.success(f"✅ 记账成功！本次利润：{t_profit:.2f} 元")
                    else:
                        st.error("库存不足，无法售出！")

    # --- 逻辑 4: 利润报表 ---
    elif menu == "📈 利润报表":
        st.subheader("📊 经营状况统计")
        log = get_log()
        if log.empty:
            st.info("尚无成交记录。")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("总营业额", f"¥{log['销售额'].sum():.2f}")
            col2.metric("总成本", f"¥{log['成本'].sum():.2f}")
            col3.metric("总净利润", f"¥{log['利润'].sum():.2f}")
            
            st.write("---")
            st.write("#### 历史成交明细")
            st.dataframe(log.sort_index(ascending=False), use_container_width=True)
            
            # 下载 Excel/CSV 报表
            csv_data = log.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下载所有数据备份",
                data=csv_data,
                file_name=f"茶叶店账单_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
