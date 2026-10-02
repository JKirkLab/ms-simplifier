import pandas as pd

def find_abun_ratio(df: pd.DataFrame):
    """function to find abundance ratio and p-value columns"""

    abundance_cols = [
        col for col in df.columns
        if "Abundance Ratio" in col
    ]

    return abundance_cols


def filter_sig(df: pd.DataFrame, abundance_cols:list[str]):
    """filters significant proteins based on adjusted p-value"""

    pvalue_cols = [
        col for col in abundance_cols
        if "Abundance Ratio Adj. P-Value:" in col
    ]

    if len(pvalue_cols) != 1:
        raise ValueError(f"Expected 1 p-value column, found {len(pvalue_cols)}")

    pvalue_col = pvalue_cols[0]
    
    return df[df[pvalue_col] < 0.05]


def compose_columns(df: pd.DataFrame):
    """Restructures current columns for simplification."""

    df["Gene"] = df["Description"].str.extract(r"GN=(\S+)")
    df["Description"] = df["Description"].str.split(" OS=").str[0]


FIXED_KEEP_COLS = ["Accession", "Description", "Gene", "Modifications"]

def simplify_columns(df: pd.DataFrame, abundance_cols: list[str]) -> pd.DataFrame:
    """Return a trimmed DataFrame with only key identifier + abundance ratio columns."""
    present_fixed = [c for c in FIXED_KEEP_COLS if c in df.columns]
    keep = present_fixed + abundance_cols
    return df[keep]


def split_de(df: pd.DataFrame, abundance_cols: list[str]) -> dict[str, pd.DataFrame]:
    """Split DataFrame into all-DE, upregulated, and downregulated sheets.

    Upregulated:   log2(abundance ratio) > 1
    Downregulated: log2(abundance ratio) < -1
    """
    import numpy as np

    pvalue_col = next(c for c in abundance_cols if "Abundance Ratio Adj. P-Value:" in c)

    log2_col = next((c for c in abundance_cols if "Abundance Ratio (log2):" in c), None)
    if log2_col is None:
        raw_col  = next(c for c in abundance_cols if "Abundance Ratio:" in c and "P-Value" not in c and "P-value" not in c)
        log2_col = raw_col.replace("Abundance Ratio:", "Abundance Ratio (log2):")
        df[log2_col] = np.log2(df[raw_col])
        abundance_cols.append(log2_col)

    all_de = df[df[pvalue_col] < 0.05].copy()
    log2   = all_de[log2_col]

    unchanged     = all_de[(log2 >= -1) & (log2 <= 1)].copy()
    upregulated   = all_de[log2 > 1].copy()
    downregulated = all_de[log2 < -1].copy()

    unchanged["Direction"]     = "Unchanged"
    upregulated["Direction"]   = "Upregulated"
    downregulated["Direction"] = "Downregulated"

    return {
        "All DE":        all_de,
        "Unchanged":     unchanged,
        "Upregulated":   upregulated,
        "Downregulated": downregulated,
    }


def write_excel(sheets: dict[str, pd.DataFrame], path) -> None:
    """Write multiple DataFrames to separate sheets in one Excel file.

    Args:
        sheets: mapping of sheet name -> DataFrame
        path:   file path string or BytesIO buffer
    """
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    






