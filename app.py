import streamlit as st
import pandas as pd
from difflib import get_close_matches
from datetime import datetime
import io

st.set_page_config(page_title="SourceClub Savings Analysis", page_icon="💰", layout="wide")

st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    h1 {color: #1e3a8a;}
    .low-confidence {background-color: #fee2e2 !important;}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://www.sourceclub.io/logo.png", width=140)
with col2:
    st.title("SourceClub Savings Analysis Tool")
    st.subheader("End-to-End Automation • Raw Benco Export → Clean Savings Report")

st.markdown("---")

# ==================== SOURCECLUB CATALOG ====================
st.header("SourceClub Pricing Catalog")
catalog = pd.DataFrame({
    "SourceClub_Item_Name": ["GRAHAM LIDOCAINE 1:100 RED 50", "GRAHAM MEPIVACAINE 3% BX50", "ORABLOC 4% W/EPI 1:100 GLD 50", "Nitrile Gloves - Medium", "Face Masks - Level 3", "Surgical Gowns"],
    "Manufacturer": ["Benco", "Benco", "Pierrel", "Medline", "Medline", "Cardinal"],
    "Pack_Size": ["50", "50", "50", "100", "50", "10"],
    "Unit": ["Box", "Box", "Box", "Box", "Box", "Each"],
    "SourceClub_Price": [28.75, 32.50, 35.00, 8.50, 12.99, 45.00]
})
st.dataframe(catalog, use_container_width=True)

# ==================== RAW INPUT & CLEANUP ====================
st.header("1. Raw Prospect Purchase History (Benco Export)")

tab1, tab2, tab3 = st.tabs(["📤 Upload Raw CSV", "✍️ Manual Entry", "🚀 Load Realistic Benco Demo"])

with tab1:
    raw_file = st.file_uploader("Upload raw messy Benco export", type=["csv"])

with tab3:
    if st.button("🚀 Load Realistic Benco Demo Data (from Loom video)", type="primary"):
        demo = pd.DataFrame({
            "Description": ["GRAHAM LIDOCAINE 1:100 RED 50", "GRAHAM LIDOCAINE 1:100 RED 50", "GRAHAM MEPIVACAINE 3% BX50", "ORABLOC 4% W/EPI 1:100 GLD 50", "Nitrile Gloves - Medium"],
            "Current_Price": [39.89, 50.15, 51.56, 47.69, 14.99],
            "Quantity": [2, 1, 1, 5, 5]
        })
        st.session_state.raw_data = demo
        st.success("✅ Realistic Benco demo loaded!")

if "raw_data" not in st.session_state:
    st.session_state.raw_data = pd.DataFrame()

# Process data
if not st.session_state.raw_data.empty:
    prospect = st.session_state.raw_data.copy()
elif raw_file is not None:
    prospect = pd.read_csv(raw_file)
else:
    st.info("👆 Use one of the options above to load data")
    st.stop()

# Matching Engine
st.header("2. AI Matching & Savings Calculation")

def find_best_match(desc, catalog_df):
    matches = get_close_matches(str(desc).strip(), catalog_df['SourceClub_Item_Name'].astype(str).tolist(), n=1, cutoff=0.5)
    if matches:
        best = matches[0]
        match_row = catalog_df[catalog_df['SourceClub_Item_Name'] == best].iloc[0]
        confidence = "High" if get_close_matches(str(desc).strip(), [best], cutoff=0.75) else "Medium"
        reason = "Description similarity match"
        return best, match_row['SourceClub_Price'], confidence, reason
    return None, None, "Low", "No strong match found"

prospect = prospect.copy()
prospect['Matched_Item'] = None
prospect['SourceClub_Price'] = None
prospect['Confidence'] = None
prospect['Match_Reason'] = None

for idx, row in prospect.iterrows():
    desc = row.get('Description', row.get('Item', ''))
    matched, price, conf, reason = find_best_match(desc, catalog)
    prospect.at[idx, 'Matched_Item'] = matched
    prospect.at[idx, 'SourceClub_Price'] = price
    prospect.at[idx, 'Confidence'] = conf
    prospect.at[idx, 'Match_Reason'] = reason

prospect['Savings_Per_Unit'] = prospect['Current_Price'] - prospect['SourceClub_Price'].fillna(0)
prospect['Total_Savings'] = prospect['Savings_Per_Unit'] * prospect.get('Quantity', 1).fillna(1)

# Display with review highlighting
def highlight_confidence(row):
    if row['Confidence'] == "Low":
        return ['background-color: #fee2e2'] * len(row)
    return [''] * len(row)

st.subheader("Matching Results + Review Queue")
styled = prospect.style.format({
    'Current_Price': '${:.2f}', 'SourceClub_Price': '${:.2f}',
    'Savings_Per_Unit': '${:.2f}', 'Total_Savings': '${:.2f}'
}).apply(highlight_confidence, axis=1)

st.dataframe(styled, use_container_width=True)

total_savings = prospect['Total_Savings'].sum()
st.metric("**Total Potential Savings (this order)**", f"${total_savings:,.2f}")

st.caption("🔴 Red rows = Low-confidence matches → Human review recommended")

# Exports
st.header("3. Export Reports")
colX, colY = st.columns(2)
with colX:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        prospect.to_excel(writer, index=False, sheet_name='Savings Analysis')
    st.download_button("📊 Download Full Excel Report", excel_buffer.getvalue(), 
                       f"SourceClub_Savings_Analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with colY:
    st.download_button("📄 Download Professional PDF Report", 
                       prospect.to_html(index=False).encode(), 
                       f"SourceClub_Savings_Report_{datetime.now().strftime('%Y%m%d')}.html", "text/html")
    st.caption("Open HTML → Print → Save as PDF for prospect")

st.success("✅ End-to-end prototype: Raw Benco export → Clean matched savings report")
