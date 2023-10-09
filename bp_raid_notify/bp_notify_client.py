"""! BP通知Botクライアントモジュール
@note created by https://twitter.com/MatchaMiG
@date 2023.10.10
"""
from .my_lib.ctrl_pickle import *

from discord import Client as d_Client
from discord import Intents
from discord.app_commands import CommandTree

from os import getenv
from typing import Coroutine

class BPNotifyClient(d_Client):
    """! Blue Protocol通知Discord Botクライアントクラス
    """
    def __init__(self, intents: Intents) -> None:
        """! BPRaidNotifyクラスのコンストラクタ
        @param intents: 受け取るイベントの設定
        @return None
        """
        # インスタンス変数宣言・初期化
        # 環境変数読込
        self.raid_notification_ch_save_path = getenv('RaidNotifyCh')      # レイド通知対象チャンネル保存ファイルパス
        # self.cycle_notification_ch_save_path = getenv('CycleNotifyCh')    # 昼夜サイクル通知対象チャンネル保存ファイルパス(未使用)

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
        #await self.change_presence(activity=Game(name='\N{rooster} 準備中 \N{rooster}'))
        #measure_time.start()    # 時刻計測開始