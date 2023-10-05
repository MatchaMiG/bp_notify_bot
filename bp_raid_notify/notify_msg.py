"""! 時報通知メッセージモジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.05
"""

from enum import Enum

class NotifyMsg (Enum):
    """! 時報通知メッセージ列挙型クラス
    """
    Simple = (0, "シンプル", "レイド開催")
    GuildMarm = (1, "受付嬢", "虚空の浮島にてデミドラゴンの出現が確認されました。\n星脈孔に向かい討伐任務に参加してください。")
    #Noble = (2, ["Noble", "ご令嬢"])
    def __init__(self, val: int, jp_name: str, msg: str) -> None:
        """! 時報通知メッセージ列挙型クラスのコンストラクタ
        @param val: int値
        @param jp_name: 日本語名
        @param msg: 通知メッセージ
        @return None
        """
        super().__init__()
        self.val = val
        self.jp_name = jp_name
        self.msg = msg

    @classmethod
    def get_from_val(cls, tgt_val: int) -> Enum:
        """! 整数値から該当情報を取得するメソッド
        @param tgt_val: 対象値
        @return 該当する情報の辞書
        """
        for c in cls:
            if c.val == tgt_val:
                return c
        return c

class RaidInfo (Enum):
    """! レイド情報列挙型クラス
    """
    # 常設
    NormalDemiDragon =  ('虚空の浮島', 'アステリア平原・アンドラ盆地')
    
    # 期間限定
    FlareDemiDragon = ('虚空の浮島・炎竜襲来', 'モンテノール渓谷・リッツェ交易街道')
    FrostDemiDragon = ('虚空の浮島・氷竜襲来', 'バハマール高原・神の見守る丘')
    EarthDemiDragon = ('虚空の浮島・土竜襲来', 'バハマール高原・神の見守る丘')
    ThunderDemiDragon = ('虚空の浮島・雷竜襲来', 'モンテノール渓谷・リッツェ交易街道')
    
    #SnadWarm = ('騒嵐の大地・砂蟲侵出', '未確認')
    #OriginDemiDragon = ('虚空の浮島・原竜襲来', '未確認')
    def __init__(self, mission_name: str, portal: str) -> None:
        """! レイド情報列挙型クラスのコンストラクタ
        @param mission_name: ミッション名
        @param portal: 星脈孔情報
        @return None
        """
        super().__init__()
        self.mission_name = mission_name
        self.portal = portal
        