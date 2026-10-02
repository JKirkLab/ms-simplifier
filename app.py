import io
import streamlit as st
import pandas as pd
import src.utils as util

st.title("Mass Spec Simplifier")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    groups = util.group_abundance_cols(df)
    

    all_sheets: dict[str, dict[str, pd.DataFrame]] = {
        label: util.split_de(df, group)
        for label, group in groups.items()
    }

    all_simplified: dict[str, dict[str, pd.DataFrame]] = {
        label: {
            name: util.simplify_columns(util.compose_columns(sheet_df.copy()), groups[label])
            for name, sheet_df in sheets.items()
        }
        for label, sheets in all_sheets.items()
    }

    group_labels = list(groups.keys())
    if len(group_labels) > 1:
        tabs = st.tabs(group_labels)
        for tab, label in zip(tabs, group_labels):
            with tab:
                for sheet_name, sheet_df in all_simplified[label].items():
                    st.subheader(f"{sheet_name} ({len(sheet_df)} proteins)")
                    st.dataframe(sheet_df)
    else:
        for sheet_name, sheet_df in all_simplified[group_labels[0]].items():
            st.subheader(f"{sheet_name} ({len(sheet_df)} proteins)")
            st.dataframe(sheet_df)

    def flat_sheets(nested: dict[str, dict[str, pd.DataFrame]]) -> dict[str, pd.DataFrame]:
        if len(nested) == 1:
            return list(nested.values())[0]
        flat = {}
        for i, (label, sheets) in enumerate(nested.items(), 1):
            for sheet_name, sheet_df in sheets.items():
                flat[f"G{i} {sheet_name}"[:31]] = sheet_df
        return flat

    col1, col2 = st.columns(2)

    with col1:
        full_buf = io.BytesIO()
        util.write_excel(flat_sheets(all_sheets), full_buf)
        st.download_button(
            label="Download full results",
            data=full_buf.getvalue(),
            file_name="results_full.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col2:
        simplified_buf = io.BytesIO()
        util.write_excel(flat_sheets(all_simplified), simplified_buf)
        st.download_button(
            label="Download simplified results",
            data=simplified_buf.getvalue(),
            file_name="results_simplified.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
