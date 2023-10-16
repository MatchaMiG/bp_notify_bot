"""!@package BPレイド通知モジュール
Blue Protocol通知Bot向け_レイド通知モジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.14
"""
from .my_lib.ctrl_pickle import *
from .my_lib.day_of_week import DayOfWeek as DoW

from discord import Client as d_Client
from discord.ext import tasks

from asyncio import sleep as sleep_async
from datetime import datetime as dt
from datetime import timedelta, time
from enum import Enum
from os import getenv
from zoneinfo import ZoneInfo

jst = ZoneInfo('Asia/Tokyo')

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

class RaidNotifyMsg (Enum):
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

class RaidSchedule(dict):
    """! レイドスケジュールクラス
    """
    def __init__(self):
        super().__init__(self)
        # 平日(WeekDay)の14/18/22時からのレイド設定
        self['wd14'] = [DoW.get_weekday(), time(hour=14, tzinfo=jst)]
        self['wd18'] = [DoW.get_weekday(), time(hour=18, tzinfo=jst)]
        self['wd22'] = [DoW.get_weekday(), time(hour=22, tzinfo=jst)]
        # 週末(WeekEnd)の08/12/16/20/25時からのレイド設定
        # ※25時のみ特殊な設定
        self['we08'] = [DoW.get_weekend(), time(hour=8, tzinfo=jst)]
        self['we12'] = [DoW.get_weekend(), time(hour=12, tzinfo=jst)]
        self['we16'] = [DoW.get_weekend(), time(hour=16, tzinfo=jst)]
        self['we20'] = [DoW.get_weekend(), time(hour=20, tzinfo=jst)]
        self['we25'] = [[DoW.Sun.val, DoW.Mon.val], time(hour=1, tzinfo=jst)]

class BPRaidNotify:
    """! レイド通知クラス
    """
    def __init__(self, client: d_Client):
        """! コンストラクタ
        """
        self.client = client
        self.pickle_path = getenv('RaidNotifyCh')
        self.notify_ch_dict = load_pickle(self.pickle_path, dict())
        self.last_dict_updated = dt.now(jst)
        self.notify_dt_dict = dict()
        self.update_time_dict(self.last_dict_updated, self.notify_ch_dict)

    def update_time_dict(self, dt_: dt, cond_dict: dict) -> None:
        """! 時報辞書更新関数
        @param datetime: 日時
        @param cond_dict: 通知条件辞書
        @return None
        @note dt_.time以前のレイドは除外して辞書を生成
        """
        dow = dt_.weekday() # 曜日取得
        ts_list = [dt.combine(dt_.date(), v[1], tzinfo=jst) for v in RaidSchedule().values() if dow in v[0]]    # 時報日時リスト作成
        
        tommorow_1st_time = min([v[1] for v in RaidSchedule().values() if ((dow + 1) % 7) in v[0]])       # 翌日最初の時報時刻を取得
        tommorow_1st_ts = dt.combine(dt_.date(), tommorow_1st_time, tzinfo=jst) + timedelta(days=1)     # 翌日最初の時報日時を取得
        ts_list.append(tommorow_1st_ts)     # 時報日時リストに翌日最初の時報日時を追加

        return_dict = dict()
        for d_k, d_v in cond_dict.items(): # レイド通知対象の情報を1つずつ読み出し
            # 以下の辞書を作成
            # キー: 'サーバID'と'チャンネルID'
            # 値: 'オフセットを考慮した通知日時リスト', 'here通知設定', 'メンション先ロールID', 'メッセージタイプ'
            new_ts_list = return_dict[d_k]['ts_list'].extend([ts for o in d_v['offset'] for ts in map(lambda x: x - timedelta(minutes=int(o)), ts_list) if ts > dt_])
            return_dict[d_k] = {'ts_list': new_ts_list, 'role': d_v['role'], 'type': d_v['type']}

        self.notify_dt_dict.update(return_dict)

    async def send_notification(self, dt_: dt, ts_dict: dict) -> None:
        """! 時報送信関数
        
        @param datetime: 日時
        @param ts_dict: 時報辞書
        @return None
        """
        tmp_raid_list = getenv('NowRaid').replace(' ', '').replace('　', '').split(',')
        raid_info_list = [ri for ri in RaidInfo if ri.mission_name in tmp_raid_list]

        for d_k, d_v in ts_dict.items():
            if any(d < dt_ for d in d_v['ts_list']):
                ch = self.client.get_channel(int(d_k[1]))
                msg_type = int(d_v['type'])
                #if d_v['role'] is not None: # メンション指定がある場合
                msg = d_v['role']      # メッセージにメンションを追加
                msg += '\n【時報】' + RaidNotifyMsg.get_from_val(msg_type).msg + '\n'    # 時報メッセージ追加

                # レイド情報追加
                for ri in raid_info_list:
                    msg += f'\n【{ri.mission_name}】\n{ri.portal}'
                # 時報送信
                await ch.send(msg)

                ts_dict[d_k]['ts_list'] = [d for d in d_v['ts_list'] if dt_ < d]    # 日時リストを更新(通知済みの要素を除外)

    @tasks.loop(seconds=30)
    async def measure_time(self) -> None:
        """! 時刻計測関数
        30秒ごとに時刻を計測し、各時報処理関数を呼び出す.
        @param None
        @return None
        """
        now_ = dt.now(jst)
        if self.last_dict_updated.date() < now_.date():
            self.update_time_dict(now_, self.notify_ch_dict)    # レイド時報リスト更新
            self.last_dict_updated = now_                       # 時報リスト更新日時の更新
        
        await self.send_notification(now_, self.notify_dt_dict)
        
    @measure_time.before_loop
    async def time_set(self) -> None:
        """! 時刻計測の時刻合わせ関数
        時刻計測関数をmm:00に開始するための時刻合わせをする.
        @param None
        @return None
        """
        # mm:00に開始するための時刻合わせ
        wait_time = 60.0 - dt.now(jst).second   # 時刻合わせ計算
        await sleep_async(wait_time)            # 時刻合わせ待機