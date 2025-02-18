import streamlit as st
import pandas as pd
import os
from io import BytesIO
import zipfile
import plotly.express as px

# Initialize session state
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = {}

st.set_page_config(page_title="Data Sweeper Pro", layout="wide")
st.title("📊 Data Sweeper Pro")
st.write("Advanced data transformation and analysis tool with enhanced cleaning, visualization, and processing capabilities")

# File upload section
upload_files = st.file_uploader("Upload your files (CSV or Excel):", 
                               type=["csv", "xlsx"], 
                               accept_multiple_files=True,
                               help="You can upload multiple files at once")

def process_file(file):
    """Process uploaded file and store in session state"""
    try:
        file_ext = os.path.splitext(file.name)[-1].lower()
        if file_ext == ".csv":
            df = pd.read_csv(file)
        elif file_ext == ".xlsx":
            df = pd.read_excel(file)
        else:
            st.error(f"Unsupported file format: {file_ext}")
            return None
        
        # Store original and processed data with file size
        if file.name not in st.session_state.processed_files:
            st.session_state.processed_files[file.name] = {
                'original': df.copy(),
                'processed': df.copy(),
                'cleaning_steps': [],
                'file_size': file.size  # Store file size here
            }
        return file.name
    except Exception as e:
        st.error(f"Error processing {file.name}: {str(e)}")
        return None

# Process uploaded files
if upload_files:
    for file in upload_files:
        if file.name not in st.session_state.processed_files:
            process_file(file)

# Main processing loop for each file
for file_name in list(st.session_state.processed_files.keys()):
    file_data = st.session_state.processed_files[file_name]
    df = file_data['processed']
    original_df = file_data['original']
    
    st.divider()
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.subheader(f"File: {file_name}")
        st.metric("Original Size", f"{original_df.shape[0]:,} rows, {original_df.shape[1]:,} cols")
        st.metric("Current Size", f"{df.shape[0]:,} rows, {df.shape[1]:,} cols")
        
        # Get file size from session state
        file_size = file_data['file_size']
        st.caption(f"File size: {file_size/1024:.2f} KB")  # Corrected line
    
    with col2:
        # Data summary expander
        with st.expander("🔍 Data Summary", expanded=True):
            st.write("Preview:")
            st.dataframe(df.head(10)) 

            st.write("Statistics:")
            st.dataframe(df.describe(include='all'))

            st.write("Missing Values:")
            missing = df.isna().sum().to_frame(name="Missing Values")
            missing["% Missing"] = (missing["Missing Values"] / len(df) * 100).round(2)
            st.dataframe(missing)

        # Enhanced data cleaning options
        with st.expander("🧹 Data Cleaning Tools"):
            cleaning_options = st.multiselect(
                "Select cleaning operations:",
                options=[
                    "Remove Duplicates", 
                    "Fill Missing Values",
                    "Drop Columns",
                    "Drop Rows with Missing Values",
                    "Reset Index"
                ],
                key=f"clean_{file_name}"
            )
            
            if "Fill Missing Values" in cleaning_options:
                fill_col, method_col = st.columns(2)
                with fill_col:
                    fill_columns = st.multiselect(
                        "Select columns to fill:",
                        options=df.columns,
                        key=f"fill_cols_{file_name}"
                    )
                with method_col:
                    fill_method = st.selectbox(
                        "Fill method:",
                        ["Mean", "Median", "Mode", "Specific Value"],
                        key=f"fill_method_{file_name}"
                    )
                    if fill_method == "Specific Value":
                        fill_value = st.text_input("Enter fill value:", key=f"fill_value_{file_name}")

            if "Drop Columns" in cleaning_options:
                drop_columns = st.multiselect(
                    "Select columns to drop:",
                    options=df.columns,
                    key=f"drop_cols_{file_name}"
                )

            if st.button("Apply Cleaning", key=f"apply_clean_{file_name}"):
                new_df = df.copy()
                cleaning_steps = []
                
                if "Remove Duplicates" in cleaning_options:
                    new_df = new_df.drop_duplicates()
                    cleaning_steps.append("Removed duplicates")
                
                if "Fill Missing Values" in cleaning_options and fill_columns:
                    for col in fill_columns:
                        if fill_method == "Mean":
                            new_df[col] = new_df[col].fillna(new_df[col].mean())
                        elif fill_method == "Median":
                            new_df[col] = new_df[col].fillna(new_df[col].median())
                        elif fill_method == "Mode":
                            new_df[col] = new_df[col].fillna(new_df[col].mode()[0])
                        elif fill_method == "Specific Value":
                            new_df[col] = new_df[col].fillna(fill_value)
                    cleaning_steps.append(f"Filled missing values using {fill_method}")
                
                if "Drop Columns" in cleaning_options and drop_columns:
                    new_df = new_df.drop(columns=drop_columns)
                    cleaning_steps.append(f"Dropped columns: {', '.join(drop_columns)}")
                
                if "Drop Rows with Missing Values" in cleaning_options:
                    new_df = new_df.dropna()
                    cleaning_steps.append("Dropped rows with missing values")
                
                if "Reset Index" in cleaning_options:
                    new_df = new_df.reset_index(drop=True)
                    cleaning_steps.append("Reset index")
                
                file_data['processed'] = new_df
                file_data['cleaning_steps'] += cleaning_steps
                st.success(f"Applied {len(cleaning_steps)} cleaning operations!")

        # Advanced visualization
        with st.expander("📈 Data Visualization"):
            viz_col1, viz_col2 = st.columns(2)
            with viz_col1:
                chart_type = st.selectbox(
                    "Chart Type:",
                    ["Bar", "Line", "Scatter", "Histogram", "Box"],
                    key=f"chart_type_{file_name}"
                )
            with viz_col2:
                x_axis = st.selectbox(
                    "X-axis:",
                    options=df.select_dtypes(include='number').columns,
                    key=f"x_axis_{file_name}"
                )
                y_axis = st.selectbox(
                    "Y-axis:",
                    options=df.select_dtypes(include='number').columns,
                    key=f"y_axis_{file_name}"
                )
            
            if chart_type == "Bar":
                fig = px.bar(df, x=x_axis, y=y_axis)
            elif chart_type == "Line":
                fig = px.line(df, x=x_axis, y=y_axis)
            elif chart_type == "Scatter":
                fig = px.scatter(df, x=x_axis, y=y_axis)
            elif chart_type == "Histogram":
                fig = px.histogram(df, x=x_axis)
            elif chart_type == "Box":
                fig = px.box(df, x=x_axis, y=y_axis)
            
            st.plotly_chart(fig, use_container_width=True)

        # Conversion and download
        with st.expander("💾 Conversion & Export"):
            conversion_type = st.radio(
                "Convert to:",
                ["CSV", "Excel", "JSON"],
                key=f"conversion_{file_name}"
            )
            
            if st.button(f"Prepare Download ({file_name})"):
                buffer = BytesIO()
                if conversion_type == "CSV":
                    df.to_csv(buffer, index=False)
                    mime_type = "text/csv"
                    ext = ".csv"
                elif conversion_type == "Excel":
                    df.to_excel(buffer, index=False)
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ext = ".xlsx"
                elif conversion_type == "JSON":
                    df.to_json(buffer, orient="records")
                    mime_type = "application/json"
                    ext = ".json"
                
                buffer.seek(0)
                st.download_button(
                    label=f"Download {conversion_type}",
                    data=buffer,
                    file_name=file_name.split('.')[0] + ext,
                    mime=mime_type,
                    key=f"download_{file_name}"
                )

# Batch processing section
st.sidebar.header("Batch Processing")
if st.sidebar.checkbox("Show Batch Processing Options"):
    if st.sidebar.button("Download All Processed Files"):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for file_name, data in st.session_state.processed_files.items():
                df = data['processed']
                buffer = BytesIO()
                df.to_csv(buffer, index=False)
                buffer.seek(0)
                zip_file.writestr(f"processed_{file_name}", buffer.getvalue())
        
        zip_buffer.seek(0)
        st.sidebar.download_button(
            label="Download All as ZIP",
            data=zip_buffer,
            file_name="processed_files.zip",
            mime="application/zip"
        )

    if st.sidebar.button("Reset All Processing"):
        st.session_state.processed_files = {}
        st.experimental_rerun()

st.sidebar.header("App Information")
st.sidebar.info("""
**Data Sweeper Pro** features:
- Multi-file processing
- Advanced data cleaning
- Interactive visualizations
- Batch operations
- Data conversion (CSV/Excel/JSON)
- Summary statistics
- Missing value analysis
- Session persistence
""")

st.success("✨ Processing complete! Explore your data using the tools above.")