import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Thiết lập trang Streamlit
st.set_page_config(
    page_title="Tính Lãi Suất Thực - Hoàng Minh Nhật",
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
st.sidebar.info("**Sinh viên:** HOÀNG MINH NHẬT\n\nDữ liệu lạm phát được lấy trực tiếp từ **World Bank API** (Indicator: `FP.CPI.TOTL.ZG`).")
st.sidebar.markdown("---")

st.sidebar.header("⚙️ Cấu Hình Đầu Tư & Lãi Suất")

# Chọn quốc gia để lấy dữ liệu World Bank
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

# Hàm fetch dữ liệu lạm phát từ World Bank API
@st.cache_data(ttl=86400) # Cache dữ liệu 24h
def get_worldbank_inflation(country):
    url = f"http://api.worldbank.org/v2/country/{country}/indicator/FP.CPI.TOTL.ZG?format=json&per_page=30"
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
                df = pd.DataFrame(records).sort_values("Năm", ascending=False)
                return df
    except Exception as e:
        st.error(f"Lỗi kết nối World Bank API: {e}")
    return pd.DataFrame()

df_inflation = get_worldbank_inflation(country_code)

# Lấy tỷ lệ lạm phát gần nhất từ World Bank làm mặc định
latest_inflation = 3.5
if not df_inflation.empty:
    latest_inflation = float(df_inflation.iloc[0]["Lạm phát (%)"])
    latest_year = df_inflation.iloc[0]["Năm"]
else:
    latest_year = 2024

# Cho phép người dùng tùy chỉnh hoặc dùng dữ liệu World Bank
custom_inflation = st.sidebar.number_input(
    f"Tỷ lệ lạm phát hàng năm (%) [World Bank {latest_year}: {latest_inflation}%]:",
    min_value=-10.0,
    max_value=100.0,
    value=latest_inflation,
    step=0.1
)

nominal_rate = st.sidebar.number_input(
    "Lãi suất danh nghĩa / Lãi gửi tiết kiệm (%/năm):",
    min_value=0.0,
    max_value=50.0,
    value=6.5,
    step=0.1
)

principal = st.sidebar.number_input(
    "Số tiền đầu tư/gửi ban đầu (VNĐ):",
    min_value=1000000,
    value=100000000,
    step=5000000,
    format="%d"
)

years = st.sidebar.slider("Thời gian gửi/đầu tư (Năm):", min_value=1, max_value=30, value=5)

# Tính toán theo hiệu ứng Fisher
# Công thức chuẩn Fisher: (1 + r_real) = (1 + r_nom) / (1 + i) => r_real = (r_nom - i) / (1 + i)
i = custom_inflation / 100
n = nominal_rate / 100
real_rate = ((1 + n) / (1 + i) - 1) * 100

# Tính tăng trưởng tài sản danh nghĩa vs giá trị thực tế sau lạm phát
future_nominal = principal * ((1 + n) ** years)
future_real = principal * ((1 + real_rate / 100) ** years)
loss_due_to_inflation = future_nominal - future_real

# Hiển thị kết quả Metric
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Lãi Suất Danh Nghĩa", f"{nominal_rate:.2f}%")

with col2:
    st.metric("💸 Lạm Phát Sử Dụng", f"{custom_inflation:.2f}%")

with col3:
    st.metric(
        "🎯 Lãi Suất Thực (Real Rate)", 
        f"{real_rate:.2f}%", 
        delta=f"{real_rate - nominal_rate:.2f}% so với danh nghĩa",
        delta_color="normal" if real_rate >= 0 else "inverse"
    )

with col4:
    st.metric("🛡️ Giá Trị Thực Nhận (Sau {0} năm)".format(years), f"{future_real:,.0f} đ")

st.markdown("---")

# Tabs thông tin chi tiết
tab1, tab2, tab3 = st.tabs(["📉 Dự Phóng Tài Sản Theo Thời Gian", "🌐 Dữ Liệu Lạm Phát World Bank", "📐 Công Thức Tính Toán"])

with tab1:
    # Bảng và đồ thị dự phóng từng năm
    chart_data = []
    for yr in range(years + 1):
        val_nom = principal * ((1 + n) ** yr)
        val_real = principal * ((1 + real_rate / 100) ** yr)
        chart_data.append({
            "Năm": yr,
            "Giá trị Danh nghĩa": round(val_nom),
            "Giá trị Thực (Sức mua)": round(val_real)
        })
    
    df_chart = pd.DataFrame(chart_data)
    
    fig = px.line(
        df_chart, 
        x="Năm", 
        y=["Giá trị Danh nghĩa", "Giá trị Thực (Sức mua)"],
        title="So Sánh Giá Trị Sức Mua Theo Thời Gian",
        markers=True,
        color_discrete_sequence=["#2563EB", "#DC2626"]
    )
    fig.update_layout(yaxis_title="Số tiền (VNĐ)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"Lịch Sử Lạm Phát {country_code} (Nguồn: World Bank API)")
    if not df_inflation.empty:
        col_tb, col_gr = st.columns([1, 2])
        with col_tb:
            st.dataframe(df_inflation, height=350, use_container_width=True)
        with col_gr:
            fig_hist = px.bar(
                df_inflation, 
                x="Năm", 
                y="Lạm phát (%)", 
                title=f"Biến Động Lạm Phát {country_code} Qua Các Năm",
                color="Lạm phát (%)",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning("Không thể lấy dữ liệu từ World Bank API vào lúc này. Vui lòng kiểm tra lại kết nối mạng.")

with tab3:
    st.markdown("""
    ### Phương Pháp Tính Toán
    
    Ứng dụng áp dụng **Phương trình Fisher (Fisher Equation)** chính xác trong kinh tế học tài chính:
    
    $$1 + r_{\\text{danh nghĩa}} = (1 + r_{\\text{thực}}) \\times (1 + \\text{lạm phát})$$
    
    Suy ra **Lãi suất thực**:
    
    $$r_{\\text{thực}} = \\frac{1 + r_{\\text{danh nghĩa}}}{1 + \\text{lạm phát}} - 1 = \\frac{r_{\\text{danh nghĩa}} - \\text{lạm phát}}{1 + \\text{lạm phát}}$$
    
    *Lưu ý: Công thức đơn giản $r_{\\text{thực}} \\approx r_{\\text{danh nghĩa}} - \\text{lạm phát}$ chỉ mang tính ước lượng xấp xỉ khi tỷ lệ lạm phát nhỏ.*
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748B; padding: 10px;'>"
    "© Dự án Công cụ Lãi suất & Lạm phát World Bank - Xây dựng bởi <b>Sinh viên HOÀNG MINH NHẬT</b>"
    "</div>", 
    unsafe_allow_html=True
)
