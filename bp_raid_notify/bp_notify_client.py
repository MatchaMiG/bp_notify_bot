"""! BP通知Botクライアント
Blue Protocol通知Botクライアント及びスラッシュコマンド
@note created by https://twitter.com/MatchaMiG
@date 2023.10.14
"""

from .my_lib.ctrl_pickle import *
from .bp_raid_notify import *

from discord import Client as d_Client
from discord import Role as d_Role
from discord import Intents, Interaction, Message, Game
from discord.app_commands import CommandTree
from discord.app_commands import Range as d_Range
from discord.ext.commands import Greedy

from os import getenv
from typing import Coroutine

from re import findall
from zoneinfo import ZoneInfo

jst = ZoneInfo('Asia/Tokyo')

class BPNotifyClient(d_Client):
    """! Blue Protocol通知Discord Botクライアントクラス
    """
    def __init__(self, intents: Intents) -> None:
        """! BPRaidNotifyクラスのコンストラクタ
        @param intents: 受け取るイベントの設定
        @return None
        """
        # 環境変数読込
        self.raid_notification_ch_save_path = getenv('RaidNotifyCh')      # レイド通知対象チャンネル保存ファイルパス
        # self.cycle_notification_ch_save_path = getenv('CycleNotifyCh')    # 昼夜サイクル通知対象チャンネル保存ファイルパス(未使用)

        # 通知対象辞書取得
        self.raid_notification_ch_dict = load_pickle(self.raid_notification_ch_save_path, dict())    # レイド通知対象チャンネル辞書取得
        # self.cycle_notification_ch_dict = load_pickle(self.cycle_notification_ch_save_path, dict())  # 昼夜サイクル通知対象チャンネル辞書取得(未使用)

        # 通知クラスインスタンス生成
        self.raid = BPRaidNotify(self)

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
        #await self.change_presence(activity=Game(name='\N{rooster} 準備中 \N{rooster}'))
        self.raid.measure_time.start()    # 時刻計測開始

# グローバル変数宣言
g_client = BPNotifyClient(intents=Intents.default())    # Discord botクライアント

@g_client.tree.command()
async def set_raid_notification(
    ctx: Interaction,
    #offset: d_Range[int, -60, 60],
    offset: str,
    #here: bool = False,
    mention: str = None,
    type: d_Range[int, 0] = 0,
    ) -> None:
    """! レイド通知追加関数
    本コマンドを実行したチャンネルをレイド通知対象として追加. メンション先ロール指定があった場合は、通知時に指定ロールにメンションする
    @param offset: 通知時刻オフセット(分)
    @param role: 通知時のメンション先(optional)
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
    set_role = ' '.join(role_list)
    msg += '\nメンション:'
    if not role_list:
        msg += ' なし'
    else:
        msg += f' {set_role}'

    # メッセージタイプ
    msg += '\nメッセージタイプ: '

    if not any(type == nm.val for nm in NotifyMsg):  # 選択したメッセージタイプがない場合
        type = 0    # メッセージタイプを0に設定
        msg += '不正な値 - タイプ0に設定 > '
    
    tgt_nm = NotifyMsg.get_from_val(type)
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
        g_client.raid.notify_ch_dict.pop((ctx.guild_id, ctx.channel_id), None)    # レイド時報辞書から該当データを削除
    dump_pickle(g_client.raid.pickle_path, g_client.raid_notification_ch_dict)    # 辞書を.pickleに保存

g_client.run(token=getenv('Token'))