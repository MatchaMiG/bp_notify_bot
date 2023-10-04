"""! pickle操作モジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.04
"""
import pickle
import os.path
from os import makedirs
from typing import Any

def load_pickle(path_str: str, default_val: Any) -> Any:
    """! 通知チャンネル情報を外部ファイル(.pickle)から取得する
    @param path: .pickleファイルまでのパス
    @param default_val: .pickleファイルがなかった場合の返戻値
    @return 外部ファイルがある場合: 外部ファイルから取得したデータ
    @return 外部ファイルがない場合: default_val
    """
    makedirs(os.path.dirname(path_str), exist_ok=True)  # ディレクトリ作成

    if os.path.isfile(path_str):                # ファイルがある場合
        with open(path_str, mode='rb') as f:    # ファイルオープン
            return pickle.load(f)               # ファイルを読み込んで返戻
    else:                       # ファイルがない場合
        return default_val      # 引数のデフォルト値を返戻
    
def dump_pickle(path_str: str, var: Any) -> None:
    """! 通知チャンネル情報を外部ファイル(RaidNotify)に保存する
    @param path: .pickleファイルまでのパス
    @param var: 保存する変数
    @return None
    """
    makedirs(os.path.dirname(path_str), exist_ok=True)  # ディレクトリ作成

    with open(path_str, mode='wb+') as f:   # ファイルオープン ※ファイルがない場合は作成
        pickle.dump(var, f)                 # ファイルに書き込み