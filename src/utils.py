import pandas as pd

FIXED_KEEP_COLS = ["Accession", "Description", "Gene", "Modifications"]


def group_abundance_cols(df: pd.DataFrame) -> dict[str, dict[str, str]]:
    """Find all comparison groups and pair their ratio, p-value, and adj. p-value columns.

    Returns a dict mapping comparison label -> {adj_pvalue, pvalue, ratio} column names.
    Raises ValueError if expected paired columns are missing for any group.
    """
    adj_pvalue_cols = [c for c in df.columns if "Abundance Ratio Adj. P-Value:" in c]

    if not adj_pvalue_cols:
        raise ValueError("No 'Abundance Ratio Adj. P-Value:' columns found")

    groups = {}
    for adj_col in adj_pvalue_cols:
        suffix     = adj_col.split("Abundance Ratio Adj. P-Value:")[1]
        pvalue_col = f"Abundance Ratio P-Value:{suffix}"
        ratio_col  = f"Abundance Ratio:{suffix}"
        log2_col   = f"Abundance Ratio (log2):{suffix}"

        missing = [c for c in [pvalue_col, ratio_col] if c not in df.columns]
        if missing:
            raise ValueError(f"Missing paired columns for '{suffix.strip()}': {missing}")

        group = {"adj_pvalue": adj_col, "pvalue": pvalue_col, "ratio": ratio_col}
        if log2_col in df.columns:
            group["log2"] = log2_col

        groups[suffix.strip()] = group

    return groups


def compose_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Extract Gene symbol and trim Description in place. Returns df for chaining."""
    df["Gene"] = df["Description"].str.extract(r"GN=(\S+)")
    df["Description"] = df["Description"].str.split(" OS=").str[0]
    return df


def simplify_columns(df: pd.DataFrame, group: dict[str, str]) -> pd.DataFrame:
    """Return a trimmed DataFrame with fixed identifier columns + group-specific columns."""
    present_fixed = [c for c in FIXED_KEEP_COLS if c in df.columns]
    group_cols    = [c for c in group.values() if c in df.columns]
    direction     = ["Direction"] if "Direction" in df.columns else []
    keep = present_fixed + group_cols + direction
    return df[keep]


def split_de(df: pd.DataFrame, group: dict[str, str]) -> dict[str, pd.DataFrame]:
    """Split DataFrame into All DE, Unchanged, Upregulated, Downregulated for one group.

    Generates a log2 column from the raw ratio if one is not already present.
    Upregulated:   log2(ratio) > 1
    Downregulated: log2(ratio) < -1
    """
    import numpy as np

    pvalue_col = group["adj_pvalue"]

    if "log2" not in group:
        raw_col  = group["ratio"]
        log2_col = raw_col.replace("Abundance Ratio:", "Abundance Ratio (log2):")
        df[log2_col] = np.log2(df[raw_col])
        group["log2"] = log2_col

    all_de = df[df[pvalue_col] < 0.05].copy()
    log2   = all_de[group["log2"]]

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