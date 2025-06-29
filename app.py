import pandas as pd
import streamlit as st 
import os



file_path = "est_7.xlsx"

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


st.subheader("🧹 Select Damaged Parts")

# Get valid parts
all_parts = df_paint.columns.str.strip().str.upper().tolist()
valid_parts = [part for part in all_parts if part not in ["MAKER", "MODEL", "YEAR", "CITY", "W_METALLIC/SOLID"]]

# Autocomplete part selector
selected_parts_list = st.multiselect(
    "🔧 Choose parts from database",
    options=sorted(valid_parts),
    help="Start typing to search from known parts in Excel"
)

if selected_parts_list:
    # Create editable part table
    manual_parts_df = pd.DataFrame({
        "Part": selected_parts_list,
        "Disc %": [0.0] * len(selected_parts_list),
        "R&R?": ["No"] * len(selected_parts_list),
        "R&R Cost": ["" for _ in selected_parts_list],
        "Tinkering?": ["No"] * len(selected_parts_list),
        "Tinkering Cost": ["" for _ in selected_parts_list]
    })

    # Show editable table
    user_parts_df = st.data_editor(
        manual_parts_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Part": st.column_config.TextColumn("Part", disabled=True),
            "Disc %": st.column_config.NumberColumn("Disc(%)", min_value=0.0, max_value=100.0, step=0.1),
            "R&R?": st.column_config.SelectboxColumn("R&R?", options=["Yes", "No"]),
            "R&R Cost": st.column_config.TextColumn("Cost(optional)"),
            "Tinkering?": st.column_config.SelectboxColumn("Tinkering?", options=["Yes", "No"]),
            "Tinkering Cost": st.column_config.TextColumn("Cost(optional)")
        },
        key="manual_parts_editor"
    )

    # Normalize and filter parts
    user_parts_df["Part"] = user_parts_df["Part"].astype(str).str.strip().str.upper()
    selected_parts = user_parts_df[user_parts_df["Part"] != ""]

    # ✅ Continue with your logic from here (paint/labour lookup, calculation, etc.)

else:
    st.info("ℹ️ Please select at least one part to proceed.")


if not selected_parts.empty:
    st.markdown("### ✅ Selected Parts")
    st.table(selected_parts[["Part", "Disc %", "R&R?", "Tinkering?"]])

    # Fetch paint and labour data rows from Excel
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
        # Extract the single matching row
        paint_row = paint_row.iloc[0].copy()
        labour_row = labour_row.iloc[0].copy()

        # Normalize part names (column headers)
        paint_row.index = paint_row.index.str.strip().str.upper()
        labour_row.index = labour_row.index.str.strip().str.upper()

        # Cost totals
        results = []
        total_painting = 0.0
        total_tinkering = 0.0
        total_rnr = 0.0

        for _, row in selected_parts.iterrows():
            part = row["Part"].strip().upper()
            try:
                custom_discount = float(row.get("Disc %", 0)) / 100
            except:
                custom_discount = 0

            # --- Painting Cost ---
            if part in paint_row:
                try:
                    paint_schedule = float(paint_row[part])
                except:
                    paint_schedule = 0
            else:
                st.warning(f"⚠️ No paint schedule found for part: {part}")
                paint_schedule = 0

            paint_cost = paint_schedule * custom_discount

            # --- Labour Cost ---
            if part in labour_row:
                try:
                    base_cost = float(labour_row[part])
                except:
                    base_cost = 0
            else:
                st.warning(f"⚠️ No labour cost found for part: {part}")
                base_cost = 0

            # --- Tinkering ---
            tinkering_cost = 0
            if row.get("Tinkering?") == "Yes":
                try:
                    tinkering_cost = float(row.get("Tinkering Cost", ""))
                except:
                    tinkering_cost = base_cost * 3300 if part in tinkering_parts else 0

            # --- R&R ---
            rnr_cost = 0
            if row.get("R&R?") == "Yes":
                try:
                    rnr_cost = float(row.get("R&R Cost", ""))
                except:
                    rnr_cost = base_cost * 3300 if part in rnr_parts else 0

            # --- Totals and Result Table ---
            total_tinkering += tinkering_cost
            total_rnr += rnr_cost
            total_painting += paint_cost

            results.append({
                "Description": part,

                "R&R": round(rnr_cost, 2),
                "Tinkering": round(tinkering_cost, 2),
                "Painting": round(paint_cost, 2),
                "Disc %": round(custom_discount * 100, 2),
                "Schedule": round(paint_schedule, 2)
            })

        # Convert results to DataFrame
        final_df = pd.DataFrame(results)
        final_df.index = range(1, len(final_df) + 1)
        final_df.index.name = "S.No"

        # Display final table
        st.markdown("### 💰 Final Estimate")
        st.dataframe(final_df, use_container_width=True)

        # Show summary totals
        st.subheader("🧾 Summary")
        summary_df = pd.DataFrame([
            {
                "Description": "Sub Total",
                "R&R": round(total_rnr, 2),
                "Tinkering": round(total_tinkering, 2),
                "Painting": round(total_painting, 2)
            },
            {
                "Description": "Grand Total",
                "R&R": "",
                "Tinkering": "",
                "Painting": round(total_rnr + total_tinkering + total_painting, 2)
            }
        ])
        st.table(summary_df)
else:
    st.info("ℹ️ Please enter damaged parts above to generate the cost estimate.")
