"""! BP通知Botクライアント
Blue Protocol通知Botクライアント及びスラッシュコマンド
@note created by https://twitter.com/MatchaMiG
@date 2023.10.16
"""
# 自作モジュール
from .my_lib.ctrl_pickle import *
from .bp_raid_notify import *
from .bp_Regnas_clock import *
# Discord Bot API
from discord import Client as d_Client
from discord import Intents, Interaction
from discord.app_commands import CommandTree
from discord.app_commands import Range as d_Range
# その他
from os import getenv           # 環境変数取得
from typing import Coroutine    # 型アノテーション
from re import findall          # 文字列抽出
from zoneinfo import ZoneInfo   # タイムゾーンデータ

jst = ZoneInfo('Asia/Tokyo')

class BPNotifyClient(d_Client):
    """! Blue Protocol通知Discord Botクライアントクラス
    """
    def __init__(self, intents: Intents) -> None:
        """! BPRaidNotifyクラスのコンストラクタ
        @param intents: 受け取るイベントの設定
        @return None
        """
        # 通知クラスインスタンス生成
        self.raid = BPRaidNotify(self)
        self.clock = RegnasClock(self)

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
        # 時刻計測開始
        self.raid.measure_time.start()
        self.clock.measure_time.start()

# グローバル変数宣言
g_client = BPNotifyClient(intents=Intents.default())    # Discord botクライアント

@g_client.tree.command()
async def set_raid_notification(
    ctx: Interaction,
    offset: str,
    mention: str = '',
    type: d_Range[int, 0] = 0,
    ) -> None:
    """! レイド通知追加関数
    本コマンドを実行したチャンネルをレイド通知対象として追加. メンション先ロール指定があった場合は、通知時に指定ロールにメンションする
    @param offset: 通知時刻オフセット(分)
    @param role: 通知時のメンション先(optional)
    @param type: 通知時のメッセージタイプ(optional)
    @return None
    """
    # 通知メッセージ作成
    msg = '【通知】このチャンネルをレイド通知対象に設定しました'
    # オフセット
    offset_list = sorted(set([i for i in map(int, findall(r'-?\d+', offset)) if -120 <= i <= 120]), reverse=True)
    msg += '\nオフセット:' 
    if not offset_list:
        offset_list = [0]
    for o in offset_list:
        if o < 0:  # オフセットの値が負
            msg += f' {-1*o}分後'
        else:      # オフセットの値が非負
            msg += f' {o}分前'

    # 通知ロール
    role_list = list(set(findall(r'<@.*?>|@here|@everyone', mention)))
    msg += '\nメンション:'
    if not role_list:
        set_role = ''
        msg += ' なし'
    else:
        set_role = ' '.join(role_list)
        msg += f' {set_role}'

    # メッセージタイプ
    msg += '\nメッセージタイプ: '

    if not any(type == nm.val for nm in RaidNotifyMsg):  # 選択したメッセージタイプがない場合
        type = 0    # メッセージタイプを0に設定
        msg += '不正な値 - タイプ0に設定 > '
    
    tgt_nm = RaidNotifyMsg.get_from_val(type)
    msg += f'{tgt_nm.jp_name}\n例: {tgt_nm.msg}'

    # 新規辞書を作成 offset: int, here: bool, role: str, type: int
    new_dict = {(ctx.guild_id, ctx.channel_id): {'offset': offset_list, 'role': set_role, 'type': type}}
    g_client.raid.notify_ch_dict.update(new_dict)

    dump_pickle(g_client.raid.pickle_path, g_client.raid.notify_ch_dict)    # 辞書を.pickleに保存
    g_client.raid.update_time_dict(dt.now(jst), new_dict)

    await ctx.response.send_message(msg, silent=True)

@g_client.tree.command()
async def unset_raid_notification(ctx: Interaction) -> None:
    """! レイド通知解除関数
    本コマンドを実行したチャンネルをレイド通知対象から削除
    @param None
    @return None
    """
    if g_client.raid.notify_ch_dict.pop((ctx.guild_id, ctx.channel_id), None) is None:  # 辞書に入っていない場合
        await ctx.response.send_message('【通知】このチャンネルはレイド通知対象に入っていません', silent=True)
    else:   # 辞書に入っている場合
        await ctx.response.send_message('【通知】このチャンネルをレイド通知対象から解除しました', silent=True) 
        g_client.raid.notify_dt_dict.pop((ctx.guild_id, ctx.channel_id), None)      # レイド時報辞書から該当データを削除
    dump_pickle(g_client.raid.pickle_path, g_client.raid.notify_ch_dict)            # 辞書を.pickleに保存

@g_client.tree.command()
async def set_clock_notification(
    ctx: Interaction,
    offset: str,
    mention: str = '',
    type: d_Range[int, 0] = 0,
    ) -> None:
    """! レグナス時計通知追加関数
    本コマンドを実行したチャンネルをレグナス時計通知対象として追加. メンション先ロール指定があった場合は、通知時に指定ロールにメンションする
    @param offset: 通知時刻オフセット(分)
    @param role: 通知時のメンション先(optional)
    @param type: 通知時のメッセージタイプ(optional)
    @return None
    """
    # 通知メッセージ作成
    msg = '【通知】このチャンネルをレグナス時計通知対象に設定しました'
    # オフセット
    offset_list = sorted(set([i for i in map(int, findall(r'-?\d+', offset)) if 0 <= i < 25]), reverse=True)
    msg += '\nオフセット:' 
    if not offset_list:
        offset_list = [0]
    for o in offset_list:
        if o < 0:  # オフセットの値が負
            msg += f' {-1*o}分後'
        else:      # オフセットの値が非負
            msg += f' {o}分前'

    # 通知ロール
    role_list = list(set(findall(r'<@.*?>|@here|@everyone', mention)))
    set_role = ' '.join(role_list)
    msg += '\nメンション:'
    if not role_list:
        msg += ' なし'
    else:
        msg += f' {set_role}'

    # メッセージタイプ
    msg += '\nメッセージタイプ: '

    if not any(type == nm.val for nm in ClockNotifyMsg):  # 選択したメッセージタイプがない場合
        type = 0    # メッセージタイプを0に設定
        msg += '不正な値 - タイプ0に設定 > '
    
    tgt_nm = ClockNotifyMsg.get_from_val(type)
    msg += f'{tgt_nm.jp_name}\n例: {tgt_nm.day_msg}'

    # 新規辞書を作成 offset: int, here: bool, role: str, type: int
    new_dict = {(ctx.guild_id, ctx.channel_id): {'offset': offset_list, 'role': set_role, 'type': type}}
    g_client.clock.notify_ch_dict.update(new_dict)

    dump_pickle(g_client.clock.pickle_path, g_client.clock.notify_ch_dict)    # 通知チャンネル辞書を.pickleに保存
    if g_client.clock.last_period != RegnasTimePeriod.Unset:    # 時間帯が未設定でない場合
        g_client.clock.update_dt_dict(dt.now(jst), replace=True)  # 通知日時辞書を更新

    await ctx.response.send_message(msg, silent=True)

@g_client.tree.command()
async def unset_clock_notification(ctx: Interaction) -> None:
    """! レグナス時計通知解除関数
    本コマンドを実行したチャンネルをレグナス時計通知対象から削除
    @param None
    @return None
    """
    if g_client.clock.notify_ch_dict.pop((ctx.guild_id, ctx.channel_id), None) is None:  # 辞書に入っていない場合
        await ctx.response.send_message('【通知】このチャンネルはレグナス時刻通知対象に入っていません', silent=True)
    else:   # 辞書に入っている場合
        await ctx.response.send_message('【通知】このチャンネルをレグナス時計通知対象から解除しました', silent=True) 
        g_client.clock.notify_dt_dict.pop((ctx.guild_id, ctx.channel_id), None)    # レイド時報辞書から該当データを削除
    dump_pickle(g_client.clock.pickle_path, g_client.clock.notify_ch_dict)    # 辞書を.pickleに保存

g_client.run(token=getenv('Token'))