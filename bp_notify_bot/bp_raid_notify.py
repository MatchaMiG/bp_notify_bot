"""!@package BPレイド通知モジュール
Blue Protocol通知Bot向け_レイド通知モジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.17
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
    ## 〇竜
    FlareDemiDragon = ('虚空の浮島・炎竜襲来', 'モンテノール渓谷・リッツェ交易街道')
    FrostDemiDragon = ('虚空の浮島・氷竜襲来', 'バハマール高原・神の見守る丘')
    EarthDemiDragon = ('虚空の浮島・土竜襲来', 'バハマール高原・神の見守る丘')
    ThunderDemiDragon = ('虚空の浮島・雷竜襲来', 'モンテノール渓谷・リッツェ交易街道')
    OriginDemiDragon = ('虚空の浮島・原竜襲来', 'バハマール高原・神の見守る丘')
    
    ## 〇蟲
    SandWarm = ('騒嵐の大地・砂蟲侵出', 'エバーグリーン砂漠・帰らずの砂塵')
    
    ## 防衛戦
    AsterleedsDefenceBattle = ('アステルリーズ防衛戦', '海鳴りの草原')

    def __init__(self, mission_name: str, portal: str) -> None:
        """! レイド情報列挙型クラスのコンストラクタ
        @param mission_name: ミッション名
        @param portal: 参加地点情報
        @return None
        """
        super().__init__()
        self.mission_name = mission_name
        self.portal = portal

class RaidNotifyMsg (Enum):
    """! 時報通知メッセージ列挙型クラス
    """
    Simple = (0, "シンプル", "レイド開催")
    GuildMarm = (1, "受付嬢", "大型エネミーの出現が確認されました。\n星脈孔に向かい討伐任務に参加してください。")
    Noble = (2, "御令嬢", "大型エネミーが出現しましてよ～～！\n冒険者の皆様はご討伐くださいませ～～！！")
    Chicken = (2816, "ニワトリ", "ｺｹｺｺｺｯｺｹｺｺｺｯｺｹｺｺｯｺｺｯｹｺｯｹｺｹｹｹｯｹｹｺｹｯｺｺｹｺｹｯｺｹｹｺｹｯｺｹｺｺｯｺｺｯｹｹｺｹｺｯｺｹｹｺｯｹｺｹｹｯｺｺｯｺｹｺｹｺｯ")

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
        self.client = client                        # Discord botクライアント(呼出元のインスタンス)
        self.last_dict_updated = dt.now(jst)        # 通知日時辞書の最新更新日時
        self.pickle_path = getenv('RaidNotifyCh')   # pickle保存パス
        self.notify_ch_dict = load_pickle(self.pickle_path, dict()) # 通知チャンネル辞書
        self.notify_dt_dict = dict()                                # 通知日時辞書

        self.update_dt_dict(self.last_dict_updated)

    def update_dt_dict(self, upd_dt: dt, overwrite: bool = False) -> None:
        """! 通知日時辞書の更新
        通知日時辞書を更新する
        @param upd_dt: 更新日時
        @param overwrite: リスト上書きフラグ
        @return None
        @note upd_dt以前の通知は除外して辞書を生成
        @note overwriteフラグがTrueの場合既存の通知日時リストは削除
        """
        # 通知日時リスト作成
        dow = upd_dt.weekday() # 曜日取得
        scd_list = [dt.combine(upd_dt.date(), v[1], tzinfo=jst) for v in RaidSchedule().values() if dow in v[0]]    # レイドスケジュールリスト作成
        
        tommorow_1st_time = min([v[1] for v in RaidSchedule().values() if ((dow + 1) % 7) in v[0]])                 # 翌日最初の時報時刻を取得
        tommorow_1st_ts = dt.combine(upd_dt.date(), tommorow_1st_time, tzinfo=jst) + timedelta(days=1)              # 翌日最初の時報日時を取得
        scd_list.append(tommorow_1st_ts)                                                                            # 通知日時リストに翌日最初の通知日時を追加

        # 通知日時辞書の更新
        upd_dict = dict()   # 更新辞書
        for d_k, d_v in self.notify_ch_dict.items(): # レイド通知対象の情報を1つずつ読み出し
            # 以下の辞書を作成
            # キー: 'サーバID'と'チャンネルID'
            # 値: 'オフセットを考慮した通知日時リスト', 'メンション', 'メッセージタイプ'

            if overwrite:   # リスト上書きフラグがTrueの場合
                ts_list = list()
            else:           # リスト上書きフラグがFalseの場合
                # 該当チャンネルの既存通知日時リストを取得
                # チャンネル辞書または通知日時リストが未生成の場合は空リストを取得
                ts_list = self.notify_dt_dict.get(d_k, dict()).get('ts_list', list())
            # 既存通知日時リスト(または空リスト)に新規通知日時リストを連結
            ts_list.extend([ts for o in d_v['offset'] for ts in map(lambda x: x - timedelta(minutes=int(o)), scd_list) if upd_dt < ts])
            # 更新辞書に各値を設定
            upd_dict[d_k] = {'ts_list': ts_list, 'role': d_v['role'], 'type': d_v['type']}

        # 通知日時辞書を更新辞書で更新
        self.notify_dt_dict.update(upd_dict)

    async def send_notification(self, snd_dt: dt) -> None:
        """! 通知送信関数
        @param snd_dt: 送信日時
        @return None
        """
        # 開催中のレイドを環境変数より取得
        tmp_raid_list = getenv('NowRaid').replace(' ', '').replace('　', '').split(',') # 区切り文字で分割しリスト化(スペースは削除)
        raid_info_list = [ri for ri in RaidInfo if ri.mission_name in tmp_raid_list]    # 該当するレイド情報があるもののみ抽出しリスト化

        for d_k, d_v in self.notify_dt_dict.items():        # 通知日時辞書を順番に処理
            if any(d < snd_dt for d in d_v['ts_list']):     # 送信日時以前の通知日時がある場合
                ch = self.client.get_channel(int(d_k[1]))   # 通知先チャンネルを取得

                # メッセージにメンションを追加
                if msg := d_v['role']:          # メンションがある場合
                    msg += '\n'                 # メッセージに改行を追加

                msg_type = int(d_v['type'])     # メッセージタイプを取得
                
                msg += '【通知】' + RaidNotifyMsg.get_from_val(msg_type).msg + '\n'    # 通知メッセージ追加

                # レイド情報追加
                for ri in raid_info_list:   # 開催中のレイドリストを順番に処理
                    msg += f'\n【{ri.mission_name}】\n{ri.portal}'  # 開催中のレイド情報をメッセージに追加

                # 通知送信
                try:
                    await ch.send(msg)
                except:
                    pass
                self.notify_dt_dict[d_k]['ts_list'] = [d for d in d_v['ts_list'] if snd_dt < d]    # 通知日時リストを更新(通知済みの要素を除外)

    @tasks.loop(seconds=15)
    async def measure_time(self) -> None:
        """! 時刻計測関数
        一定時間ごとに時刻を計測し、各時報処理関数を呼び出す.
        @param None
        @return None
        """
        now_dt = dt.now(jst)                    # 現在日時(JST)
        await self.send_notification(now_dt)    # 通知送信

        if self.last_dict_updated.date() < now_dt.date():   # 通知日時辞書の最新更新日時が、現在日時の日付以前の場合
            self.update_dt_dict(now_dt)         # 通知日時辞書を更新
            self.last_dict_updated = now_dt     # 通知日時辞書の最新更新日時を現在日時に設定
        
        
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