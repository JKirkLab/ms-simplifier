import io
import streamlit as st
import pandas as pd
import src.utils as util

st.title("Mass Spec Simplifier")

st.info(
    "**Note:** This app assumes a single group comparison with one set of adjusted p-values. "
    "If your file contains multiple group comparisons with multiple adjusted p-value columns, "
    "it will not work correctly."
)

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    abundance_cols = util.find_abun_ratio(df)
    util.compose_columns(df)
    sheets = util.split_de(df, abundance_cols)
    simplified_sheets = {
        name: util.simplify_columns(sheet_df, abundance_cols)
        for name, sheet_df in sheets.items()
    }

    for sheet_name, sheet_df in simplified_sheets.items():
        st.subheader(f"{sheet_name} ({len(sheet_df)} proteins)")
        st.dataframe(sheet_df)

    col1, col2 = st.columns(2)

    with col1:
        full_buf = io.BytesIO()
        util.write_excel(sheets, full_buf)
        st.download_button(
            label="Download full results",
            data=full_buf.getvalue(),
            file_name="results_full.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col2:
        simplified_buf = io.BytesIO()
        util.write_excel(simplified_sheets, simplified_buf)
        st.download_button(
            label="Download simplified results",
            data=simplified_buf.getvalue(),
            file_name="results_simplified.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )