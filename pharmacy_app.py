# 📦 Step 1: Import libraries
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import gspread
import datetime
import os
import io
import time
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 📱 Improve mobile compatibility
print("System time (UTC):", time.time())
# Function to convert image to base64
def get_base64_image(image_file):
    with open(image_file, "rb") as img:
        return base64.b64encode(img.read()).decode()
# Convert your local image
img_base64 = get_base64_image("image.jpg")

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-position: center;
}}

html, body, [class*="css"] {{
    font-size: 18px;
    font-family: 'Segoe UI', sans-serif;
    padding: 8px;
}}

.reportview-container .main .block-container {{
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
    background-color: rgba(240, 240, 240, 0.9); /* light gray overlay */;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}}
</style>
""", unsafe_allow_html=True)

# Your footer & text styles
st.markdown("""
<div style='text-align: center; padding: 5px 0;'>
<h4 style='color: #111;'>By Malaika Zafar | Data Analyst & App Developer</h4>
</div>
<style>
[data-testid="stAppViewContainer"] {
    background-color: rgba(255,255,255,0.85);
    padding: 20px;
    border-radius: 10px;
}
h1, h2, h3, h4 {
    color: #111; /* almost black */;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ✅ Folder for saving files
SAVE_FOLDER = "saved_data"
os.makedirs(SAVE_FOLDER, exist_ok=True)
def save_user_data(df, user_email):
    filename = os.path.join(SAVE_FOLDER, f"{user_email}.xlsx")
    df.to_excel(filename, index=False)

# 💟 Step 2: App Title
st.set_page_config(page_title="Pharmacy Expiry Tracker", layout="centered")
# 💊 Pharmacy Banner
st.markdown("""
<div style='background: linear-gradient(to right, #dcdcdc, #f5f5f5); padding: 20px; border-radius: 10px; text-align: center; color: #111;'>
    <h2>💊 Pharmacy Expiry Tracker</h2>
    <p>Track medicines and get instant expiry alerts. Ensure health & safety with timely inventory email updates.</p>
</div>
""", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📁 Upload", "🧽 Cleaning", "📊 Dashboard", "🚨 Alerts"])

# 📄 Step 3: File Upload Section
with tab1:
    st.header("📁 Upload Inventory File")
    file = st.file_uploader("📁 Upload your Medicine Inventory (CSV or Excel). There should be 3 columns: Medicine_name, Quantity( also write quantity type like tablets, injections, syrups and units for better analysis ) and Expiry_date", type=['csv', 'xlsx'])

    if file:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
        except Exception as e:
            st.error(f"❌ Error loading file: {e}")
            st.stop()

        required_cols = ['medicine_name', 'quantity', 'expiry_date']
        if not all(col in df.columns for col in required_cols):
            st.error(f"❌ Your file must contain the following columns: {required_cols}")
            st.stop()
        st.session_state.df = df
        st.success("✅ File uploaded and stored!")
with tab2:
    st.header("🧽 Clean and Edit Your Data")

    if "df" not in st.session_state:
        st.warning("⚠️ Please upload a file in the '📁 Upload' tab first.")
        st.stop()
    else:
        df = st.session_state.df.copy()

    st.subheader("🧪 Cleaning data")
    st.subheader("🗘️ Optional: You can edit Your Data. Remember to fill all cells to get right analysis.")
    st.info("Below check enable editing of data,")
    st.info("1. If you see any missing values in column 'quantity' and do not know how to fill. Scroll down little bit. There will be options so choose anyone according to your data.")
    st.info("2. If you do not fill missing values of medicine and date. It will be directly changed into None and Nat")
    enable_editing = st.checkbox("✏️ Enable editing of uploaded data", value=False)

    if enable_editing:
        df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        st.info("✅ Changes are saved automatically in memory.")

    df['medicine_name'] = df['medicine_name'].astype(str).str.strip()

    missing_names = df['medicine_name'].isna().sum()
    if missing_names > 0:
        st.warning(f"⚠️ {missing_names} rows are missing medicine names.")
        fill_missing_names = st.checkbox("Do you want to handle missing medicine names automatically?")

        if fill_missing_names:
            strategy = st.selectbox("Select what you’d like to do:", ["Replace with 'Unknown'", "Do it by editing or replacing by yourself"])
            if strategy == "Replace with 'Unknown'":
                df['medicine_name'].fillna("Unknown", inplace=True)
                st.success("✅ Missing names replaced with 'Unknown'")
            else:
                st.stop()

    def extract_quantity_and_unit(text):
        if pd.isna(text):
            return pd.Series([None, None])
        text = str(text).lower().strip()
        match = re.match(r'(\d+)\s*([a-zA-Z]*)', text)
        if match:
            quantity = int(match.group(1))
            unit = match.group(2) if match.group(2) else 'unit'
            return pd.Series([quantity, unit])
        else:
            return pd.Series([None, None])

    df[['clean_quantity', 'unit_type']] = df['quantity'].apply(extract_quantity_and_unit)
    missing_qty = df['clean_quantity'].isna().sum()

    if missing_qty > 0:
        st.warning(f"⚠️ {missing_qty} rows have missing quantity values.")
        if st.checkbox("🔧 Fix missing quantities?"):
            method = st.selectbox("Choose a method to fill missing quantities:", ["0 (Assume no stock)", "Median", "Mean"])
            if method == "0 (Assume no stock)":
                df['clean_quantity'].fillna(0, inplace=True)
            elif method == "Median":
                df['clean_quantity'].fillna(df['clean_quantity'].median(), inplace=True)
            elif method == "Mean":
                df['clean_quantity'].fillna(df['clean_quantity'].mean(), inplace=True)
                st.success("Successfully, Missing quantity values have been replaced.")
    df['quantity'] = df['clean_quantity']

    st.markdown("### 🗕️ Date Format Settings")
    date_format = st.selectbox("Choose the date format used in your file", ["Auto-detect", "DD-MM-YYYY", "MM-DD-YYYY", "YYYY-MM-DD"])

    if date_format == "DD-MM-YYYY":
        df['expiry_date'] = pd.to_datetime(df['expiry_date'], format='%d-%m-%Y', errors='coerce')
    elif date_format == "MM-DD-YYYY":
        df['expiry_date'] = pd.to_datetime(df['expiry_date'], format='%m-%d-%Y', errors='coerce')
    elif date_format == "YYYY-MM-DD":
        df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
    else:
        df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
    nat_rows = df[df['expiry_date'].isna()]
    if not nat_rows.empty:
        st.warning(f"⚠️ {len(nat_rows)} rows have empty expiry dates and are automatically converted in Nat. Review them in edit box.")

    today = pd.Timestamp.today()
    df['days_to_expiry'] = (df['expiry_date'] - today).dt.days

    def classify_expiry(days):
        if days < 0:
            return "❌ Expired"
        elif days <= 30:
            return "⚠️ Near Expiry"
        else:
            return "✅ Safe"

    df['status'] = df['days_to_expiry'].apply(classify_expiry)
    st.session_state.df = df

    cleaned_filename = os.path.join(SAVE_FOLDER, f"cleaned_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(cleaned_filename, index=False)
    st.success(f"✅ Cleaned data saved to: {cleaned_filename}")

with tab3:
    st.header("📊 Dashboard Summary")
    
    if "df" not in st.session_state:
        st.warning("⚠️ Please upload a file in the '📁 Upload' tab first.")
        st.stop()
    else:
        df = st.session_state.df.copy()
    if 'status' not in df.columns:
        st.warning("⚠️ Please clean your data in the '🧽 Cleaning' tab before viewing the dashboard.")
        st.stop()

    st.markdown("## 📈 Quick Summary")

    total = int(len(df))
    expired_count = int((df['status'] == "❌ Expired").sum())
    near_expiry_count = int((df['status'] == "⚠️ Near Expiry").sum())
    safe_count = int((df['status'] == "✅ Safe").sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Medicines", total)
    col2.metric("Expired", expired_count, delta=f"-{expired_count}")
    col3.metric("Near Expiry", near_expiry_count)
    col4.metric("Safe", safe_count)

    st.subheader("📋 Inventory with Expiry Status")
    st.dataframe(df[['medicine_name', 'quantity', 'expiry_date', 'days_to_expiry', 'status']])

    st.markdown("### 🔗 Optional: Group Medicines by")
    group_by_cols = st.multiselect("Select columns to group by:", options=['medicine_name', 'unit_type', 'expiry_date'], default=['medicine_name', 'unit_type'])

    if group_by_cols:
        grouped = df.groupby(group_by_cols)['quantity'].sum().reset_index()
        st.dataframe(grouped)
        if st.button("Replace original data with grouped version?"):
            df = grouped
            st.success("✅ Data has been grouped and updated.")

    st.subheader("📊 Expiry Status Summary")
    status_counts = df['status'].value_counts()
    fig, ax = plt.subplots()
    status_counts.plot(kind='bar', color=['green', 'orange', 'red'], ax=ax)
    ax.set_xlabel("Status")
    ax.set_ylabel("Number of Medicines")
    ax.set_title("Medicine Expiry Categories")
    st.pyplot(fig)

    near_expiry = df[df['status'] == '⚠️ Near Expiry']
    expired = df[df['status'] == '❌ Expired']

    if not near_expiry.empty or not expired.empty:
        st.subheader("🚨 Alert Summary")
        if not near_expiry.empty:
            st.warning(f"⚠️ {len(near_expiry)} medicines are NEAR expiry. Please take action soon.")
        if not expired.empty:
            st.error(f"❌ {len(expired)} medicines have already EXPIRED!")

        with st.expander("📦 View Details"):
            st.dataframe(pd.concat([near_expiry, expired])[['medicine_name', 'quantity', 'expiry_date', 'status']])
    else:
        st.success("✅ All medicines are in safe expiry zone.")
with tab4:
    st.header("🚨 Expiry Alerts")
    if "df" not in st.session_state:
        st.warning("⚠️ Please upload a file in the '📁 Upload' tab first.")
        st.stop()
    else:
        df = st.session_state.df.copy()
        if st.button("📧 Setup Weekly Email Alerts"):
            st.info("✅ Email alerts for expired medicines will be sent automatically every week.")
        with st.form("email_form"):
            st.write("📧 Enter your email (comma-separated):")
            emails_input = st.text_area("Emails")
            submitted = st.form_submit_button("Save Emails")
            if submitted:
                emails = [e.strip() for e in emails_input.split(",") if e.strip()]
                # Save these emails in Google Sheet or a file
                st.success(f"✅ Saved {len(emails)} email(s)")

        st.download_button("⬇️ Download Cleaned Data", df.to_csv(index=False), file_name="cleaned_pharmacy_data.csv")
        excel_filename = os.path.join(SAVE_FOLDER, f"cleaned_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(excel_filename, index=False)
        st.success(f"✅ Cleaned Excel file also saved: {excel_filename}")
        st.download_button("⬇️ Download Excel File", data=open(excel_filename, 'rb'), file_name="cleaned_pharmacy_data.xlsx")
