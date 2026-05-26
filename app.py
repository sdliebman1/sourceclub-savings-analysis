import streamlit as st
import pandas as pd
from difflib import get_close_matches
from datetime import datetime
import io

st.set_page_config(page_title="SourceClub Savings Analysis", page_icon="💰", layout="wide")

# Branding
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    h1 {color: #1e3a8a;}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://www.sourceclub.io/logo.png", width=140)   # ← Change this to real logo URL later if you want
with col2:
    st.title("SourceClub Savings Analysis Tool")
    st.subheader("AI-Powered • Automated • Real-Time Savings Reports")

st.markdown("---")

st.header("1. Upload Files")

colA, colB = st.columns(2)
with colA:
    catalog_file = st.file_uploader("SourceClub Catalog (CSV)", type="csv")
    if catalog_file is None:
        st.info("✅ Using sample catalog")
        catalog = pd.DataFrame({
            "SourceClub_Item_Name": ["Nitrile Gloves - Medium", "Face Masks - Level 3", "Surgical Gowns", "Dental Impression Material"],
            "Manufacturer": ["Medline", "Medline", "Cardinal", "3M"],
            "Pack_Size": ["100", "50", "10", "1"],
            "Unit": ["Box", "Box", "Each", "Cartridge"],
            "SourceClub_Price": [8.50, 12.99, 45.00, 28.75]
        })

with colB:
    prospect_file = st.file_uploader("Prospect Purchase History (CSV)", type="csv")

if prospect_file is None:
    st.stop()

prospect = pd.read_csv(prospect_file)

# Matching Engine
st.header("2. Matching & Savings Calculation")

def find_best_match(desc, catalog_df):
    matches = get_close_matches(str(desc), catalog_df['SourceClub_Item_Name'].astype(str).tolist(), n=1, cutoff=0.6)
    if matches:
        best = matches[0]
        match_row = catalog_df[catalog_df['SourceClub_Item_Name'] == best].iloc[0]
        confidence = "High" if get_close_matches(str(desc), [best], cutoff=0.75) else "Medium"
        return best, match_row['SourceClub_Price'], confidence
    return None, None, "Low"

prospect = prospect.copy()
prospect['Matched_Item'] = None
prospect['SourceClub_Price'] = None
prospect['Confidence'] = None

for idx, row in prospect.iterrows():
    desc = row.get('Description') or row.get('Item') or row.get('Product', '')
    matched, price, conf = find_best_match(desc, catalog)
    prospect.at[idx, 'Matched_Item'] = matched
    prospect.at[idx, 'SourceClub_Price'] = price
    prospect.at[idx, 'Confidence'] = conf

prospect['Current_Price'] = pd.to_numeric(prospect.get('Price', prospect.get('Unit_Price', 0)), errors='coerce')
prospect['Savings_Per_Unit'] = prospect['Current_Price'] - prospect['SourceClub_Price'].fillna(0)
prospect['Total_Savings'] = prospect['Savings_Per_Unit'] * prospect.get('Quantity', 1).fillna(1)

st.dataframe(prospect.style.format({
    'Current_Price': '${:.2f}', 'SourceClub_Price': '${:.2f}',
    'Savings_Per_Unit': '${:.2f}', 'Total_Savings': '${:.2f}'
}), use_container_width=True)

total = prospect['Total_Savings'].sum()
st.metric("**Total Potential Savings**", f"${total:,.2f}")

# Downloads
st.header("3. Export Reports")
colX, colY = st.columns(2)
with colX:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        prospect.to_excel(writer, index=False, sheet_name='Savings Analysis')
    st.download_button("📊 Download Excel Report", excel_buffer.getvalue(), 
                       f"SourceClub_Savings_{datetime.now().strftime('%Y%m%d')}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with colY:
    st.download_button("📄 Download PDF Report (HTML → Print to PDF)", 
                       prospect.to_html(index=False).encode(), 
                       f"SourceClub_Savings_Report_{datetime.now().strftime('%Y%m%d')}.html", "text/html")

st.success("✅ Live Savings Analysis Tool Ready!")
