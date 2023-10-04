"""! 時報通知メッセージモジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.05
"""

from enum import Enum

class NotifyMsg (Enum):
    """! 時報通知メッセージ列挙型クラス
    """
    Simple = (0, ["Simple", "シンプル"], "レイド開催")
    GuildMarm = (1, ["GuildMarm", "受付嬢"], "虚空の浮島にてデミドラゴンの出現が確認されました。\n星脈孔に向かい討伐任務に参加してください。")
    #Noble = (2, ["Noble", "ご令嬢"])