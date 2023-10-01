"""! 設定モジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.01
"""

from datetime import datetime as dt
from zoneinfo import ZoneInfo   # 'Asia/Tokyo'が見つからないとエラーが出るときは、「pip install tzdata」すること

from day_of_week import DayOfWeek as DoW

class RaidSchedule(dict):
    def __init__(self):
        tz = ZoneInfo('Asia/Tokyo')
        # 平日(WeekDay)の14/18/22時からのレイド設定
        self['wd14'] = [DoW.get_weekday, dt.time(hour=14, tzinfo=tz)]
        self['wd18'] = [DoW.get_weekday, dt.time(hour=18, tzinfo=tz)]
        self['wd22'] = [DoW.get_weekday, dt.time(hour=22, tzinfo=tz)]
        # 週末(WeekEnd)の08/12/16/20/25時からのレイド設定
        # ※25時のみ特殊な設定
        self['we8'] = [DoW.get_weekday, dt.time(hour=8, tzinfo=tz)]
        self['we12'] = [DoW.get_weekday, dt.time(hour=12, tzinfo=tz)]
        self['we16'] = [DoW.get_weekday, dt.time(hour=16, tzinfo=tz)]
        self['we20'] = [DoW.get_weekday, dt.time(hour=20, tzinfo=tz)]
        self['we25'] = [[DoW.Sun.val, DoW.Mon.val], dt.time(hour=1, tzinfo=tz)]