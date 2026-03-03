"""
Sync the latest `visible_text` values from the raw dataset into the
`_success` dataset so downstream processes always read the newest text.

Usage:
    python update_dataset.py

The script does **not** execute automatically when imported.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

SOURCE_PATH = Path(
    r"C:\畢業專題\資料集\搞AI欄位的\phishing_dataset_expansion_forEmbeddingModule_Gemini_text.csv"
)
TARGET_PATH = Path(
    r"C:\畢業專題\資料集\搞AI欄位的\phishing_dataset_expansion_forEmbeddingModule_Gemini_text_success.csv"
)
KEY_COLUMN = "url"
TEXT_COLUMN = "visible_text"
ENCODING = "utf-8-sig"


def ensure_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"找不到檔案：{path}")


def check_size(df_source: pd.DataFrame, df_target: pd.DataFrame) -> None:
    if len(df_source) != len(df_target):
        raise ValueError("來源檔案和成功檔案筆數不一致")
    print(f"來源筆數：{len(df_source):,}，成功檔案筆數：{len(df_target):,}")


def load_dataset(path: Path, label: str) -> pd.DataFrame:
    ensure_file(path)
    df = pd.read_csv(path)
    return df


def update_visible_text(df_source: pd.DataFrame, df_target: pd.DataFrame):
    for index, row in df_source.iterrows():
        if index < 33000:
            continue
        if index > 46000:
            break
        if pd.isna(row['visible_text']):
           continue
        if df_target.loc[index, 'url'] == row['url']:
            if pd.isna(df_target.loc[index, 'visible_text']):
                df_target.loc[index, 'visible_text'] = row['visible_text']
                print(f"更新第 {index+1} 筆資料")
            else:
                print(f"第 {index+1} 筆資料已經更新")
    return df_target

def save_dataset(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, encoding=ENCODING)


def main() -> None:
    print("🔄 載入資料集中...")
    df_source = load_dataset(SOURCE_PATH, "來源檔案")
    df_target = load_dataset(TARGET_PATH, "成功檔案")

    print(f"來源筆數：{len(df_source):,}，成功檔案筆數：{len(df_target):,}")

    check_size(df_source, df_target)
    df_source.info()
    df_target.info()
    print("✏️ 開始更新 visible_text...")
    df_target = update_visible_text(df_source, df_target)
    df_source.info()
    df_target.info()
    print("💾 儲存結果...")
    save_dataset(df_target, TARGET_PATH)
    print("🎉 更新完成！")


if __name__ == "__main__":
    main()

