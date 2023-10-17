"""! レグナス時計モジュール
Blue Protocol通知Bot向け_レグナス時計モジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.17
"""
from .my_lib.ctrl_pickle import *

from discord import Client as d_Client
from discord import Game
from discord.ext import tasks

from datetime import datetime as dt
from datetime import timedelta, time
from enum import Enum
from os import getenv
from asyncio import sleep as sleep_async
from zoneinfo import ZoneInfo

jst = ZoneInfo('Asia/Tokyo')

class ClockNotifyMsg (Enum):
    """! レグナス時計通知メッセージ列挙型クラス
    """
    Simple = (0, "シンプル", "時間帯移行 夜 > 昼", "時間帯移行 昼 > 夜")
    GuildMarm = (1, "受付嬢", "まもなく時間帯が昼になります。", "まもなく時間帯が夜になります。")
    Noble = (2, "御令嬢", "昼になりますわ～～～！！", "夜になりますわ～～～！！")
    Chicken = (2816, "ニワトリ", "ｹｹｺｺｹｯｹｺｹｹｺｯｹｺｯｺｺｯｹｹｯ", "ｹｹｯｹｺｹｹｺｯｹｺｯｺｺｯｹｹｯ")

    def __init__(self, val: int, jp_name: str, day_msg: str, night_msg: str) -> None:
        """! レグナス時計通知メッセージ列挙型クラスのコンストラクタ
        @param val: int値
        @param jp_name: 日本語名
        @param day_msg: 昼に切り替わる際の通知メッセージ
        @param night_msg: 夜に切り替わる際の通知メッセージ
        @return None
        """
        super().__init__()
        self.val = val
        self.jp_name = jp_name
        self.day_msg = day_msg
        self.night_msg = night_msg

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
    
class RegnasTimePeriod(Enum):
    """! レグナス時間帯_列挙型クラス
    """
    Unset = -1  # 未設定
    Day = 0     # 昼
    Night = 1   # 夜

class RegnasClock:
    """! レグナス時計クラス
    """
    def __init__(self, client: d_Client):
        """! コンストラクタ
        """
        self.client = client                        # Discord botクライアント(呼出元のインスタンス)
        self.last_period = RegnasTimePeriod.Unset   # 最新の時間帯(初期値は未設定)
        self.next_switch_dt = None                  # 次の時間帯切替日時
        self.pickle_path = getenv('RegnasClockNotifyCh')            # pickle保存パス
        self.notify_ch_dict = load_pickle(self.pickle_path, dict()) # 通知チャンネル辞書
        self.notify_dt_dict = dict()                                # 通知日時辞書

    @property
    def Regnas_basetime_list(self) -> list():
        """! レグナス基準時刻のリスト
        レグナス時刻の基準時刻のリストを格納するプロパティ変数(Readonly)
        """
        return [2530, 1930, 1330, 730, 130] # 毎日600秒ずつズレるのをリスト化

    @property
    def Regnas_service_start_dt(self) -> dt:
        """! ブルプロのサービス開始日
        Blue Protocolのサービス開始日を格納するプロパティ変数(Readonly)
        @note 2023/06/14 09:00:00として設定(基準時刻計算に利用)
        """
        return dt(2023, 6, 14, 9, 0, 0, tzinfo=jst)

    def update_dt_dict(self, upd_dt: dt, overwrite: bool = False) -> None:
        """! 通知日時辞書の更新
        通知日時辞書を更新する
        @param upd_dt: 更新日時
        @param overwrite: 入れ替えフラグ
        @return None
        @note upd_dt以前の通知は除外して辞書を生成
        @note overwriteフラグがTrueの場合既存の通知日時リストは削除
        """
        # 通知日時辞書の更新
        upd_dict = dict()   # 更新辞書
        for d_k, d_v in self.notify_ch_dict.items(): # レグナス時計通知対象の情報を1つずつ読み出し
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
            ts_list.extend([ts for ts in map(lambda o: self.next_switch_dt.replace(second=0, microsecond=0) - timedelta(minutes=int(o)), d_v['offset']) if upd_dt < ts])
            # 更新辞書に各値を設定
            upd_dict[d_k] = {'ts_list': ts_list, 'role': d_v['role'], 'type': d_v['type']}

        # 通知日時辞書を更新辞書で更新
        self.notify_dt_dict.update(upd_dict)

    async def send_notification(self, snd_dt: dt) -> None:
        """! 通知送信関数
        @param datetime: 送信日時
        @return None
        """
        for d_k, d_v in self.notify_dt_dict.items():        # 通知日時辞書を順番に処理
            if any(d < snd_dt for d in d_v['ts_list']):     # 送信日時以前の通知日時がある場合
                ch = self.client.get_channel(int(d_k[1]))   # 通知先チャンネルを取得

                # メッセージにメンションを追加
                if msg := d_v['role']:          # メンションがある場合
                    msg += '\n'                 # メッセージに改行を追加

                msg_type = int(d_v['type'])     # メッセージタイプを取得

                if self.last_period == RegnasTimePeriod.Night:  # 現在夜 → 次は昼
                    msg += '【通知】' + ClockNotifyMsg.get_from_val(msg_type).day_msg     # 昼切替の通知メッセージ追加
                elif self.last_period == RegnasTimePeriod.Day:  # 現在昼 → 次は夜
                    msg += '【通知】' + ClockNotifyMsg.get_from_val(msg_type).night_msg   # 夜切替の通知メッセージ追加

                # 通知送信
                await ch.send(msg)

                self.notify_dt_dict[d_k]['ts_list'] = [d for d in d_v['ts_list'] if snd_dt < d]    # 通知日時リストを更新(通知済みの要素を除外)

    def get_Regnas_basetime(self, calc_dt: dt) -> int:
        """! レグナス基準時刻取得メソッド
        レグナス時刻の基準時刻を取得する
        @param calc_dt: 基準時刻を算出する対象の日時
        @return int: レグナス基準時刻(秒)
        """
        idx = (calc_dt - self.Regnas_service_start_dt).days % 5
        return self.Regnas_basetime_list[idx]

    def calc_Regnas_time(self, calc_dt:dt) -> [RegnasTimePeriod, dt, dt]:
        """! レグナス時間計算関数
        現在の昼/夜を判定し、その時間帯の開始時刻と終了時刻を算出する.これらの結果をbotのステータスに表示する.
        @param calc_dt: 算出する日時(JST)
        @return 現在の時間帯, 開始日時, 終了日時
        @note 基準時刻は環境変数から取得
        """
        Regnas_basetime = self.get_Regnas_basetime(calc_dt)                     # 算出日時の基準時刻を取得
        Regnas_totalsec = int(calc_dt.timestamp() - Regnas_basetime) % 3000     # 算出日時のレグナス時刻(累計秒)を算出

        # 現在の昼夜を判定
        if Regnas_totalsec < 1500:
            now_period = RegnasTimePeriod.Day
        else:
            now_period = RegnasTimePeriod.Night

        elapsed_secs = Regnas_totalsec % 1500                       # 現在の時間帯の経過秒数
        start_dt = calc_dt - timedelta(seconds=elapsed_secs)        # 現在の時間帯の開始日時
        end_dt = calc_dt + timedelta(seconds=1500 - elapsed_secs)   # 現在の時間帯の終了日時

        if start_dt.time() < time(hour=9, tzinfo=jst) < end_dt.time():  # 現在の時間帯が 午前9時(JST) を跨ぐ場合
            if time(hour=9, tzinfo=jst) < calc_dt.time():   # 算出時刻が 午前9時(JST) を過ぎた場合
                start_dt += timedelta(seconds=600)           # 開始日時を 600秒 = 10分 遅らせる
            else:                                           # 算出時刻が 午前9時(JST) 以降の場合
                end_dt -= timedelta(seconds=600)             # 終了日時を 600秒 = 10分 短縮

        return now_period, start_dt, end_dt     # 時間帯/開始日時/終了日時 を返戻

    async def apply_Regnas_clock(self, period: RegnasTimePeriod, start_dt: dt, end_dt: dt) -> None:
        """! レグナス時計反映メソッド
        レグナス時計をBotのステータス欄に反映する
        @param period: 昼夜
        @param start_dt: 開始日時
        @param end_dt: 終了日時
        @return None
        """
        # アクティビティ設定
        if period == RegnasTimePeriod.Day:      # 時間帯が昼の場合
            act = Game(name=f'\N{High Brightness Symbol}昼\N{High Brightness Symbol} {start_dt.strftime("%H:%M")}-{end_dt.strftime("%H:%M")}')
        elif period == RegnasTimePeriod.Night:  # 時間帯が夜の場合
            act = Game(name=f'\N{White Medium Star}夜\N{White Medium Star} {start_dt.strftime("%H:%M")}-{end_dt.strftime("%H:%M")}')
        else:                                   # 時間帯が昼でも夜でもない場合(不定値)
            act = Game(name='\N{rooster} 準備中 \N{rooster}')

        await self.client.change_presence(activity=act) # Botのアクティビティを変更

    @tasks.loop(seconds=15)
    async def measure_time(self) -> None:
        """! 時刻計測関数
        30秒ごとに時刻を計測し、各レグナス時計処理関数を呼び出す.
        @param None
        @return None
        """
        now_dt = dt.now(jst)    # 現在日時(JST)

        # 通知送信
        # note: self.last_period変更後に送信する場合、切替日時ちょうどの通知時にメッセージが不適切になるため前に配置
        await self.send_notification(now_dt)

        now_period, start_dt, end_dt = self.calc_Regnas_time(now_dt)    # レグナス時間を計算
        if now_period != self.last_period:                              # 計算した時間帯 と 最新の時間帯が異なる場合
            self.next_switch_dt = end_dt                                # 次の切替時刻を新しく算出した終了時刻に設定
            await self.apply_Regnas_clock(now_period, start_dt, end_dt) # レグナス時計をステータスに反映
            self.update_dt_dict(now_dt)                                 # 通知日時辞書を更新
            self.last_period = now_period                               # 最新の時間帯を 新しく算出した時間帯に変更

        
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