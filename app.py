import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Thiết lập trang Streamlit
st.set_page_config(
    page_title="Tính Lãi Suất Thực Sau Lạm Phát - Hoàng Minh Nhật",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .author-badge {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        text-align: center;
        width: fit-content;
        margin: 0 auto 1.5rem auto;
        border: 1px solid #FDE68A;
    }
</style>
""", unsafe_allow_html=True)

# Header & Author
st.markdown('<div class="main-header">📈 Công Cụ Tính Lãi Suất Thực Sau Lạm Phát</div>', unsafe_allow_html=True)
st.markdown('<div class="author-badge">👨‍🎓 Phát triển bởi Sinh viên: HOÀNG MINH NHẬT</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 👤 Thông Tin Tác Giả")
st.sidebar.info("**Sinh viên:** HOÀNG MINH NHẬT\n\nDữ liệu lạm phát lịch sử được truy xuất trực tiếp từ **World Bank API** (Indicator: `FP.CPI.TOTL.ZG`).")
st.sidebar.markdown("---")

st.sidebar.header("⚙️ Cấu Hình Đầu Tư & Lạm Phát")

# Chọn quốc gia
country_code = st.sidebar.selectbox(
    "Chọn quốc gia lấy dữ liệu Lạm phát:",
    options=["VNM", "USA", "JPN", "SGP", "THA"],
    format_func=lambda x: {
        "VNM": "🇻🇳 Việt Nam (VNM)",
        "USA": "🇺🇸 Mỹ (USA)",
        "JPN": "🇯🇵 Nhật Bản (JPN)",
        "SGP": "🇸🇬 Singapore (SGP)",
        "THA": "🇹🇭 Thái Lan (THA)"
    }[x],
    index=0
)

# Fetch dữ liệu World Bank
@st.cache_data(ttl=86400)
def get_worldbank_inflation(country):
    url = f"http://api.worldbank.org/v2/country/{country}/indicator/FP.CPI.TOTL.ZG?format=json&per_page=60"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                records = []
                for item in data[1]:
                    if item['value'] is not None:
                        records.append({
                            "Năm": int(item['date']),
                            "Lạm phát (%)": round(item['value'], 2)
                        })
                df = pd.DataFrame(records).sort_values("Năm", ascending=True)
                return df
    except Exception as e:
        st.error(f"Lỗi kết nối World Bank API: {e}")
    return pd.DataFrame()

df_all_inflation = get_worldbank_inflation(country_code)

if not df_all_inflation.empty:
    min_year = int(df_all_inflation["Năm"].min())
    max_year = int(df_all_inflation["Năm"].max())
    
    # Cho phép người dùng chọn khoảng năm (Ví dụ: 2018 - 2022)
    selected_years = st.sidebar.slider(
        "Chọn khoảng năm quan sát lạm phát:",
        min_value=min_year,
        max_value=max_year,
        value=(2018, min(2023, max_year)),
        step=1
    )
    start_yr, end_yr = selected_years

    # Lọc dữ liệu theo khoảng năm
    df_filtered = df_all_inflation[
        (df_all_inflation["Năm"] >= start_yr) & (df_all_inflation["Năm"] <= end_yr)
    ]
    
    # Tính lạm phát trung bình hàng năm trong giai đoạn được chọn
    avg_inflation = float(df_filtered["Lạm phát (%)"].mean())
else:
    start_yr, end_yr = 2018, 2022
    avg_inflation = 3.5
    df_filtered = pd.DataFrame()

# Ô nhập tùy chỉnh lạm phát (Mặc định lấy lạm phát trung bình giai đoạn đã chọn)
custom_inflation = st.sidebar.number_input(
    f"Tỷ lệ lạm phát bình quân (%/năm) [{start_yr} - {end_yr}]:",
    min_value=-10.0,
    max_value=100.0,
    value=round(avg_inflation, 2),
    step=0.1,
    help="Đã tự động tính trung bình lạm phát World Bank trong khoảng năm bạn chọn. Bạn có thể tự chỉnh lại nếu muốn."
)

nominal_rate = st.sidebar.number_input(
    "Lãi suất danh nghĩa / Lãi gửi tiết kiệm (%/năm):",
    min_value=0.0,
    max_value=50.0,
    value=6.5,
    step=0.1
)

principal = st.sidebar.number_input(
    "Số tiền đầu tư / gửi ban đầu (VNĐ):",
    min_value=1000000,
    value=100000000,
    step=5000000,
    format="%d"
)

# Số năm đầu tư có thể đặt mặc định bằng số năm trong giai đoạn hoặc chỉnh tùy ý
investment_years = end_yr - start_yr + 1 if (end_yr >= start_yr) else 5

# Tính toán theo Phương trình Fisher
i = custom_inflation / 100
n = nominal_rate / 100
real_rate = ((1 + n) / (1 + i) - 1) * 100

future_nominal = principal * ((1 + n) ** investment_years)
future_real = principal * ((1 + real_rate / 100) ** investment_years)

# Hiển thị Kết Quả Overview
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Lãi Suất Danh Nghĩa", f"{nominal_rate:.2f}%")

with col2:
    st.metric(f"💸 Lạm Phát TB ({start_yr}-{end_yr})", f"{custom_inflation:.2f}%")

with col3:
    st.metric(
        "🎯 Lãi Suất Thực (Real Rate)", 
        f"{real_rate:.2f}%", 
        delta=f"{real_rate - nominal_rate:.2f}% vs Danh Nghĩa",
        delta_color="normal" if real_rate >= 0 else "inverse"
    )

with col4:
    st.metric(f"🛡️ Giá Trị Thực ({investment_years} năm)", f"{future_real:,.0f} đ")

st.markdown("---")

# Tabs hiển thị
tab1, tab2, tab3 = st.tabs(["🌐 Biến Động Lạm Phát Theo Giai Đoạn", "📈 Dự Phóng Sức Mua Lãi Suất Thực", "📐 Công Thức Tính Toán"])

with tab1:
    st.subheader(f"Dữ Liệu Lạm Phát {country_code} Giai Đoạn {start_yr} - {end_yr}")
    if not df_filtered.empty:
        col_tb, col_gr = st.columns([1, 2])
        
        with col_tb:
            st.write(f"**Trung bình cộng:** `{avg_inflation:.2f}% / năm`")
            st.dataframe(df_filtered.sort_values("Năm", ascending=False), height=300, use_container_width=True)
            
        with col_gr:
            fig_hist = px.bar(
                df_filtered, 
                x="Năm", 
                y="Lạm phát (%)", 
                title=f"Lạm Phát Hàng Năm Từ {start_yr} Đến {end_yr}",
                color="Lạm phát (%)",
                color_continuous_scale="Reds",
                text="Lạm phát (%)"
            )
            fig_hist.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning("Không có dữ liệu cho giai đoạn đã chọn.")

with tab2:
    # Bảng và đồ thị dự phóng từng năm dựa theo số năm đầu tư
    chart_data = []
    for yr in range(investment_years + 1):
        val_nom = principal * ((1 + n) ** yr)
        val_real = principal * ((1 + real_rate / 100) ** yr)
        chart_data.append({
            "Năm": yr,
            "Giá trị Danh nghĩa (Chưa trừ lạm phát)": round(val_nom),
            "Giá trị Thực (Sức mua thực tế)": round(val_real)
        })
    
    df_chart = pd.DataFrame(chart_data)
    
    fig = px.line(
        df_chart, 
        x="Năm", 
        y=["Giá trị Danh nghĩa (Chưa trừ lạm phát)", "Giá trị Thực (Sức mua thực tế)"],
        title=f"Mô Phỏng Tăng Trưởng Tài Sản Qua {investment_years} Năm",
        markers=True,
        color_discrete_sequence=["#2563EB", "#DC2626"]
    )
    fig.update_layout(yaxis_title="Số tiền (VNĐ)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown(r"""
    ### Phương Pháp Tính Lãi Suất Thực
    
    1. **Tính lạm phát trung bình:**
       Tỷ lệ lạm phát bình quân được lấy từ dữ liệu chính thức của World Bank API.
       
    2. **Phương trình Fisher (Fisher Equation):**
    
    $$r_r = \frac{1 + r_n}{1 + i} - 1$$
    
    * **Trong đó:**
      * $r_r$: Lãi suất thực (Real Interest Rate)
      * $r_n$: Lãi suất danh nghĩa (Nominal Interest Rate)
      * $i$: Tỷ lệ lạm phát (Inflation Rate)
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748B; padding: 10px;'>"
    "© Dự án Công cụ Lãi suất & Lạm phát World Bank - Xây dựng bởi <b>Sinh viên HOÀNG MINH NHẬT</b>"
    "</div>", 
    unsafe_allow_html=True
)
