import pandas as pd
import streamlit as st 
import os
    


file_path = "est_5.xlsx"

#app title
st.title("COST ESTIMATOR (Tinkering, R&R, Painting)")   

# File check (silent)
if not os.path.exists(file_path):
    st.error("❌ File not found!")
    st.stop()

# Load Excel file (silent)
try:
    excel = pd.ExcelFile(file_path)
except Exception as e:
    st.error(f"❌ Failed to load Excel file: {e}")
    st.stop()

#read  sheets
df_paint=pd.read_excel(excel,sheet_name="DATABASE_PAINT")
df_labour=pd.read_excel(excel,sheet_name="DATABASE_LAB")
df_tinkering=pd.read_excel(excel,sheet_name="TINKERING",header=None)
df_rnr=pd.read_excel(excel,sheet_name="R&R",header=None)



#clean the sheets 
df_paint.dropna(how='all', inplace=True)
df_labour.dropna(how='all', inplace=True)
df_tinkering.dropna(how='all', inplace=True)
df_rnr.dropna(how='all', inplace=True)

# Optional: strip whitespace in column headers
df_paint.columns = df_paint.columns.str.strip()
df_labour.columns = df_labour.columns.str.strip()


# Clean column names and values
df_paint.columns = df_paint.columns.str.strip().str.upper()
df_labour.columns = df_labour.columns.str.strip().str.upper()
df_tinkering.iloc[:, 0] = df_tinkering.iloc[:, 0].astype(str).str.strip().str.upper()
df_rnr.iloc[:, 0] = df_rnr.iloc[:, 0].astype(str).str.strip().str.upper()

# Columns required in paint sheet
required_cols_paint = ["MAKER", "MODEL", "YEAR", "CITY", "W_METALLIC/SOLID"]
# Columns required in labour sheet (without paint type)
required_cols_labour = ["MAKER", "MODEL", "YEAR", "CITY"]

# Check paint sheet
for col in required_cols_paint:
    if col not in df_paint.columns:
        st.error(f"❌ Missing column '{col}' in PAINTING sheet.")

# Check labour sheet
for col in required_cols_labour:
    if col not in df_labour.columns:
        st.error(f"❌ Missing column '{col}' in LABOUR sheet.")

# Clean and standardize sheet values
common_cols = ["MAKER", "MODEL", "CITY", "YEAR"]
for df in [df_paint, df_labour]:
    for col in common_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
    df["YEAR"] = df["YEAR"].astype(str).str.strip()

# Clean paint type only in df_paint
if "W_METALLIC/SOLID" in df_paint.columns:
    df_paint["W_METALLIC/SOLID"] = df_paint["W_METALLIC/SOLID"].astype(str).str.strip().str.upper()

#reading only the tinkering and r&r parts from the sheet
tinkering_parts=df_tinkering.iloc[:, 0].dropna().astype(str).str.strip().str.upper().tolist()
rnr_parts=df_rnr.iloc[:, 0].dropna().astype(str).str.strip().str.upper().tolist()

# Extract all unique parts from paint and labour sheets (for autocomplete)
non_part_cols = ["MAKER", "MODEL", "YEAR", "CITY", "W_METALLIC/SOLID"]
paint_parts = [col for col in df_paint.columns if col not in non_part_cols]
labour_parts = [col for col in df_labour.columns if col not in non_part_cols]
all_parts = sorted(set(paint_parts + labour_parts))

#MAKER
makers=sorted(set(df_paint["MAKER"]) | set(df_labour["MAKER"]))
selected_maker=st.selectbox("🚗 Select Car Maker", makers)

#model 
model=sorted(set(df_paint[df_paint["MAKER"]==selected_maker]["MODEL"]).union(
   df_labour[df_labour["MAKER"]==selected_maker]["MODEL"]
))
selected_model=st.selectbox("🚙 Select Car Model",model)

#year
years = sorted(set(
    df_paint[(df_paint["MODEL"] == selected_model)]["YEAR"]
).union(
    df_labour[(df_labour["MODEL"] == selected_model)]["YEAR"]
), reverse=True)
selected_year=st.selectbox("📆 Select Schedule Year",years)

#city 
cities=sorted(set(df_paint["CITY"]) | set(df_labour["CITY"]))
selected_city=st.selectbox("📍 Select City", cities)

#paint type
paint_types = sorted(df_paint["W_METALLIC/SOLID"].dropna().unique())
selected_paint_type = st.selectbox("🎨 Select Paint Type", paint_types)

#garage type
garage_type=st.radio("🏭 Select Garage Type",["A","B","C","D"])

#damaged parts input table wise?
st.subheader("🧹 Select Damaged Parts ")

def_rows = 5
manual_parts_df = pd.DataFrame({
    "Part": [""] * def_rows,
    "Paint Discount (%)": [0] * def_rows
})

# Default template for manual entry
manual_parts_df = pd.DataFrame({
    "Part": [""],
    "Paint Discount (%)": [0.0]
})


# Editable table for user input
user_parts_df = st.data_editor(
    manual_parts_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Part": st.column_config.TextColumn("Part"),
        "Paint Discount (%)": st.column_config.NumberColumn(
            "Paint Discount (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.1f"
        )
    },
    key="manual_parts"
)



# Normalize and clean user input
user_parts_df["Part"] = user_parts_df["Part"].astype(str).str.strip().str.upper()

# Ensure Paint Discount column exists
if "Paint Discount (%)" not in user_parts_df.columns:
    user_parts_df["Paint Discount (%)"] = 0.0

# Filter only filled parts
selected_parts = user_parts_df[user_parts_df["Part"] != ""]

if not selected_parts.empty:
    st.markdown("### ✅ Selected Parts")
    st.table(selected_parts[["Part", "Paint Discount (%)"]])

    st.subheader("📊 Final Estimate Table")
    garage_discounts = {"A": 0.0, "B": 0.8, "C": 0.5, "D": 1.0}
    discount_rate = garage_discounts.get(garage_type.upper(), 0)

    paint_row = df_paint[
        (df_paint["MAKER"] == selected_maker) &
        (df_paint["MODEL"] == selected_model) &
        (df_paint["YEAR"] == selected_year) &
        (df_paint["CITY"] == selected_city) &
        (df_paint["W_METALLIC/SOLID"] == selected_paint_type)
    ]

    labour_row = df_labour[
        (df_labour["MAKER"] == selected_maker) &
        (df_labour["MODEL"] == selected_model) &
        (df_labour["YEAR"] == selected_year) &
        (df_labour["CITY"] == selected_city)
    ]

    if paint_row.empty or labour_row.empty:
        st.error("❌ No matching data found for the selected inputs.")
    else:
        paint_row = paint_row.iloc[0].copy()
        labour_row = labour_row.iloc[0].copy()
        paint_row.index = pd.Index([str(i).strip().upper() for i in paint_row.index])
        labour_row.index = pd.Index([str(i).strip().upper() for i in labour_row.index])

        results = []
        total_painting = 0.0
        total_tinkering = 0.0
        total_rnr = 0.0 

        for _, row in selected_parts.iterrows():
            part = row["Part"]
            try:
                custom_discount = float(row.get("Paint Discount (%)", 0)) / 100
            except:
                custom_discount = 0

            paint_schedule = paint_row.get(part, 0)
            base_cost = labour_row.get(part, 0)

            try:
                paint_schedule = float(paint_schedule) if not pd.isna(paint_schedule) else 0
            except:
                paint_schedule = 0

            try:
                base_cost = float(base_cost) if not pd.isna(base_cost) else 0
            except:
                base_cost = 0

            tinkering_cost = base_cost * 3300 if part in tinkering_parts else 0
            rnr_cost = base_cost * 3300 if part in rnr_parts else 0
            paint_cost = paint_schedule * custom_discount  # use user-entered discount

            total_tinkering += tinkering_cost
            total_rnr += rnr_cost
            total_painting += paint_cost

            results.append({
                "Description": part,
                "Tinkering": round(tinkering_cost, 2),
                "R&R": round(rnr_cost, 2),
                "Painting": round(paint_cost, 2),
                "Paint Discount (%)": round(custom_discount * 100, 2),
                "Schedule": round(paint_schedule, 2)
            })

        final_df = pd.DataFrame(results)
        st.dataframe(final_df)

        st.subheader("🧾 Summary")
        st.table(pd.DataFrame([
            {"Description": "Sub Total", "Tinkering": round(total_tinkering, 2), "R&R": round(total_rnr, 2), "Painting": round(total_painting, 2)},
            {"Description": "Grand Total", "Tinkering": "", "R&R": "", "Painting": round(total_tinkering + total_rnr + total_painting, 2)}
        ]))

else:
    st.info("ℹ️ Please enter damaged parts above to generate the cost estimate.")
