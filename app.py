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
    st.image("https://www.sourceclub.io/logo.png", width=140)
with col2:
    st.title("SourceClub Savings Analysis Tool")
    st.subheader("AI-Powered • Automated • Real-Time Savings Reports")

st.markdown("---")

# ==================== SOURCECLUB CATALOG (Pre-loaded) ====================
st.header("SourceClub Catalog (Pre-loaded)")

catalog = pd.DataFrame({
    "SourceClub_Item_Name": [
        "Nitrile Gloves - Medium", "Face Masks - Level 3", "Surgical Gowns", 
        "Dental Impression Material", "Composite Resin A2", "Dental Burs FG", 
        "Cavity Liner", "X-Ray Sensor Covers", "Prophy Paste", "Anesthetic Cartridges"
    ],
    "Manufacturer": ["Medline", "Medline", "Cardinal", "3M", "Kerr", "SS White", "Kerr", "Henry Schein", "3M", "Septodont"],
    "Pack_Size": ["100", "50", "10", "1", "1", "100", "1", "500", "200", "50"],
    "Unit": ["Box", "Box", "Each", "Cartridge", "Syringe", "Pack", "Tube", "Box", "Jar", "Box"],
    "SourceClub_Price": [8.50, 12.99, 45.00, 28.75, 65.00, 19.99, 12.50, 24.99, 15.75, 32.50]
})

st.dataframe(catalog, use_container_width=True)

# ==================== PROSPECT INPUT ====================
st.header("Prospect Purchase History")

tab1, tab2, tab3 = st.tabs(["📤 Upload CSV", "✍️ Manual Entry", "🚀 Load Demo Data"])

with tab1:
    prospect_file = st.file_uploader("Upload Prospect CSV", type="csv")

with tab2:
    st.write("Add items one by one:")
    if "manual_data" not in st.session_state:
        st.session_state.manual_data = pd.DataFrame(columns=["Description", "Current_Price", "Quantity"])
    
    new_item = st.data_editor(st.session_state.manual_data, num_rows="dynamic", use_container_width=True)
    st.session_state.manual_data = new_item

with tab3:
    if st.button("🚀 Load Realistic Demo Prospect Data", type="primary"):
        demo_data = pd.DataFrame({
            "Description": ["Nitrile exam gloves medium", "Level 3 surgical masks", "Disposable surgical gowns", 
                           "Impression material light body", "Composite resin A2", "FG dental burs", 
                           "X-ray sensor protectors", "Prophy paste mint"],
            "Current_Price": [14.99, 22.50, 68.00, 42.00, 89.00, 28.00, 38.00, 24.99],
            "Quantity": [5, 8, 3, 12, 4, 10, 6, 15]
        })
        st.session_state.manual_data = demo_data
        st.success("✅ Demo data loaded! Switch to Manual Entry tab to see it.")

# Use manual data if available, otherwise uploaded file
if not st.session_state.manual_data.empty:
    prospect = st.session_state.manual_data.copy()
    prospect = prospect.rename(columns={"Description": "Prospect_Item_Description", "Current_Price": "Current_Price"})
elif prospect_file is not None:
    prospect = pd.read_csv(prospect_file)
else:
    st.info("👆 Use one of the options above to get started")
    st.stop()

# Matching Engine
st.header("2. Matching & Savings Calculation")

def find_best_match(desc, catalog_df):
    matches = get_close_matches(str(desc), catalog_df['SourceClub_Item_Name'].astype(str).tolist(), n=1, cutoff=0.5)
    if matches:
        best = matches[0]
        match_row = catalog_df[catalog_df['SourceClub_Item_Name'] == best].iloc[0]
        confidence = "High" if get_close_matches(str(desc), [best], cutoff=0.7) else "Medium"
        return best, match_row['SourceClub_Price'], confidence
    return None, None, "Low"

prospect = prospect.copy()
prospect['Matched_Item'] = None
prospect['SourceClub_Price'] = None
prospect['Confidence'] = None

for idx, row in prospect.iterrows():
    desc = row.get('Prospect_Item_Description') or row.get('Description') or row.get('Item', '')
    matched, price, conf = find_best_match(desc, catalog)
    prospect.at[idx, 'Matched_Item'] = matched
    prospect.at[idx, 'SourceClub_Price'] = price
    prospect.at[idx, 'Confidence'] = conf

prospect['Savings_Per_Unit'] = prospect['Current_Price'] - prospect['SourceClub_Price'].fillna(0)
prospect['Total_Savings'] = prospect['Savings_Per_Unit'] * prospect.get('Quantity', 1).fillna(1)

st.dataframe(prospect.style.format({
    'Current_Price': '${:.2f}', 'SourceClub_Price': '${:.2f}',
    'Savings_Per_Unit': '${:.2f}', 'Total_Savings': '${:.2f}'
}), use_container_width=True)

total_savings = prospect['Total_Savings'].sum()
st.metric("**Total Potential Savings for this Order**", f"${total_savings:,.2f}")

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
    st.download_button("📄 Download PDF Report", 
                       prospect.to_html(index=False).encode(), 
                       f"SourceClub_Savings_Report_{datetime.now().strftime('%Y%m%d')}.html", "text/html")
    st.caption("Open HTML file → Print → Save as PDF")

st.success("✅ Live working prototype ready for the case study!")
