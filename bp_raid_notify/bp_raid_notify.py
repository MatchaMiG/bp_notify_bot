"""!@package BPレイド通知モジュール
Blue Protocol用レイド通知Botのメインモジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.05
"""
from .raid_schedule import *   # レイド時刻の設定
from .notify_msg import *   

from os import getenv
from .my_lib.ctrl_pickle import *

from discord import Client as d_Client
from discord import Role as d_Role
from discord import Intents, Interaction, Game, ActivityType
from discord.app_commands import CommandTree
from discord.app_commands import Range as d_Range
from discord.ext import tasks

from asyncio import sleep as sleep_async
from datetime import datetime as dt
from datetime import timedelta
from typing import Coroutine, Any
from zoneinfo import ZoneInfo

jst = ZoneInfo('Asia/Tokyo')

class BPRaidNotifyClient(d_Client):
    """! Blue Protocolレイド通知クラス
    """
    def __init__(self, intents: Intents) -> None:
        """! BPRaidNotifyクラスのコンストラクタ
        @param intents: 受け取るイベントの設定
        @return None
        """
        # インスタンス変数宣言・初期化
        # 環境変数読込
        self.raid_notification_ch_save_path = getenv('RaidNotify')      # レイド通知対象チャンネル保存ファイルパス
        # self.cycle_notification_ch_save_path = getenv('CycleNotify')    # 昼夜サイクル通知対象チャンネル保存ファイルパス(未使用)

        # 通知対象辞書取得
        self.raid_notification_ch_dict = load_pickle(self.raid_notification_ch_save_path, dict())    # レイド通知対象チャンネル辞書取得
        # self.cycle_notification_ch_dict = load_pickle(self.cycle_notification_ch_save_path, dict())  # 昼夜サイクル通知対象チャンネル辞書取得(未使用)

        super().__init__(intents=intents)    # Discord botオブジェクト生成
        self.tree = CommandTree(self)   # コマンドツリーオブジェクト生成

    def __del__(self) -> None:
        """! DiscordBotBaseクラスのデストラクタ
        @param None
        @return None
        """
        pass

    async def setup_hook(self) -> Coroutine[Any, Any, None]:
        """! botセットアップコルーチン
        @param None
        @return None
        """
        await self.tree.sync()              # コマンドツリー同期
        return await super().setup_hook()   # セットアップコルーチン
    
    async def on_ready(self) -> None:
        """! 準備完了メソッド
        botの準備完了時に呼び出される.通知を出し、時刻計測を開始する
        @param None
        @return None
        """
        await self.change_presence(activity=Game(name='\N{rooster} 準備中 \N{rooster}'))
        measure_time.start()    # 時刻計測開始

# グローバル変数宣言
g_client = BPRaidNotifyClient(intents=Intents.default())    # Discord botクライアント
g_last_updated_date = dt.now(jst).date()                    # レイド通知辞書の最終更新日付
g_raid_ts_dict = dict()                                     # レイド通知辞書

@g_client.tree.command()
async def set_raid_notification(
    ctx: Interaction,
    offset: d_Range[int, -60, 60],
    role: d_Role = None,
    ) -> None:
    """! レイド通知追加関数
    本コマンドを実行したチャンネルをレイド通知対象として追加. メンション先ロール指定があった場合は、通知時に指定ロールにメンションする
    @param offset: 通知時刻オフセット(分)
    @param role: 通知時のメンション先(optional)
    @return None
    """
    msg = '【通知】このチャンネルをレイド通知対象に追加しました'
    if offset < 0:  # オフセットの値が負
        msg += f'\nオフセット: {-1*offset}分後'
    else:           # オフセットの値が非負
        msg += f'\nオフセット: {offset}分前'

    if role is None:
        new_list = [offset, None]    # 追加するキーと値をまとめたリストを作成
        msg += '\nメンション: なし'
    else:
        new_list = [offset, role.id] # 追加するキーと値をまとめたリストを作成
        msg += f'\nメンション: {role.mention}'
    new_dict = {(ctx.guild_id, ctx.channel_id): new_list}
    g_client.raid_notification_ch_dict.update(new_dict)

    dump_pickle(g_client.raid_notification_ch_save_path, g_client.raid_notification_ch_dict)    # 辞書を.pickleに保存
    update_raid_ts_dict(dt.now(jst), new_dict)

    await ctx.response.send_message(msg)

@g_client.tree.command()
async def unset_raid_notification(ctx: Interaction) -> None:
    """! レイド通知解除関数
    本コマンドを実行したチャンネルをレイド通知対象から削除
    @param None
    @return None
    """
    if g_client.raid_notification_ch_dict.pop((ctx.guild_id, ctx.channel_id), None) is None:  # 辞書に入っていない場合
        await ctx.response.send_message('【通知】このチャンネルはレイド通知対象に入っていません')
    else:   # 辞書に入っている場合
        global g_raid_ts_dict
        await ctx.response.send_message('【通知】このチャンネルをレイド通知対象から解除しました') 
        g_raid_ts_dict.pop((ctx.guild_id, ctx.channel_id), None)    # レイド時報辞書から該当データを削除
    dump_pickle(g_client.raid_notification_ch_save_path, g_client.raid_notification_ch_dict)    # 辞書を.pickleに保存

def update_raid_ts_dict(dt_: dt, cond_dict:dict) -> dict:
    """! レイド時報辞書更新関数
    @param datetime: 日時
    @return None
    @note dt_.time以前のレイドは除外して辞書を生成
    """
    global g_raid_ts_dict
    dow = dt_.weekday() # 曜日取得
    today_ts_list = [dt.combine(dt_.date(), v[1], tzinfo=jst) for v in RaidSchedule().values() if dow in v[0]]        # その日の時報日時リスト作成

    return_dict = dict()
    for d_k, d_v in cond_dict.items(): # レイド通知対象の情報を1つずつ読み出し
        # 以下の辞書を作成
        # キー: 'サーバID'と'チャンネルID'
        # 値: 'オフセットを考慮した通知日時リスト'と'メンション先ロールID'
        return_dict[d_k] = [[ts for ts in map(lambda x: x - timedelta(minutes=int(d_v[0])), today_ts_list) if ts > dt_], d_v[1]]

    g_raid_ts_dict.update(return_dict)

async def send_notification(dt_: dt, ts_dict: dict) -> None:
    """! 時報送信関数
    
    @param datetime: 日時
    @param ts_dict: 時報辞書
    @return None
    """
    global g_client

    for d_k, d_v in ts_dict.items():
        if any(d < dt_ for d in d_v[0]):
            ch = g_client.get_channel(int(d_k[1]))
            if d_v[1] is None:  # メンション指定がない場合
                await ch.send(f'【時報】レイド')
            else:               # メンション指定がある場合
                try:
                    role = g_client.get_guild(int(d_k[0])).get_role(int(d_v[1]))    # メンション取得
                    await ch.send(f'{role.mention}\n【時報】レイド')
                except:
                    await ch.send(f'※メンション取得に失敗しました\n【時報】レイド')

            ts_dict[d_k][0] = [d for d in d_v[0] if dt_ < d]    # 日時リストを更新(通知済みの要素を除外)

async def calc_Regnas_time(dt_:dt) -> None:
    """! レグナス時間計算関数
    現在の昼/夜を判定し、その時間帯の残り時間を算出する.これらの結果をbotのステータスに表示する.
    @param dt_: 判定する時刻
    @return None
    @note 基準時刻は環境変数から取得
    """
    Regnas_basetime = int(getenv('RegnasBaseTime', 1340))
    Regnas_totalsec = int(dt_.replace(tzinfo=jst).timestamp() - Regnas_basetime) % 3000  # 現在の日の時刻(累計秒)を取得
    m, s = divmod(int(1500-Regnas_totalsec % 1500), 60) # 残り時間(分, 秒)を算出
    if Regnas_totalsec < 1500:  # 昼
        act = Game(name=f'\N{High Brightness Symbol}昼\N{High Brightness Symbol} 残{m:02}:{s:02}')
    else:                       # 夜
        act = Game(name=f'\N{White Medium Star}夜\N{White Medium Star} 残{m:02}:{s:02}')
    global g_client
    await g_client.change_presence(activity=act)

@tasks.loop(seconds=10)
async def measure_time() -> None:
    """! 時刻計測関数
    30秒ごとに時刻を計測し、各時報処理関数を呼び出す.
    @param None
    @return None
    """
    global g_last_updated_date
    global g_raid_ts_dict
    now = dt.now(jst)
    await calc_Regnas_time(now)
    if (measure_time.current_loop == 0) or (g_last_updated_date < now.date()):
        update_raid_ts_dict(now, g_client.raid_notification_ch_dict)    # レイド時報リスト更新
        g_last_updated_date = now.date()    # 時報リスト更新日時の更新
    
    await send_notification(now, g_raid_ts_dict)
    
@measure_time.before_loop
async def time_set() -> None:
    """! 時刻計測の時刻合わせ関数
    時刻計測関数をmm:00に開始するための時刻合わせをする.
    @param None
    @return None
    """
    # mm:00に開始するための時刻合わせ
    now = dt.now(jst)
    wait_time = 60.0 - now.second   # 時刻合わせ計算
    await sleep_async(wait_time)    # 時刻合わせ待機

g_client.run(token=getenv('Token'))