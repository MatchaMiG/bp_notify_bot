"""! 曜日モジュール
曜日列挙型クラスを設定する
@note created by https://twitter.com/MatchaMiG
@date 2023.10.03
"""
from enum import Enum

class DayOfWeek(Enum):
    """! 曜日列挙型クラス
    @note datetimeモジュールの曜日と同値になるように設定
    """
    Mon = (0, '月')
    Tue = (1, '火')
    Wed = (2, '水')
    Thu = (3, '木')
    Fri = (4, '金')
    Sat = (5, '土')
    Sun = (6, '日')

    def __init__(self, val: int = None, jp_name: str = None) -> None:
        """! 曜日列挙型クラスのコンストラクタ
        @param val: int値
        @param jp_name: 日本語名
        @return None
        """
        super().__init__()
        self.val = val
        self.jp_name = jp_name

    @classmethod
    def get_weekday(cls) -> list[int]:
        """! 平日取得メソッド
        月曜日～金曜日の値をリストとして取得する
        @param None
        @return list[int]: 月曜日～金曜日の値リスト
        """
        return list(range(cls.Mon.val, cls.Fri.val + 1))

    @classmethod
    def get_weekend(cls) -> list[int]:
        """! 週末取得メソッド
        土曜日～日曜日の値をリストとして取得する
        @param None
        @return list[int]: 土曜日～日曜日の値リスト
        """
        return list(range(cls.Sat.val, cls.Sun.val + 1))