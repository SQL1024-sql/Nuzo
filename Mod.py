import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import os
import requests
import json
import yt_dlp
from datetime import datetime, timedelta
import threading
import edge_tts
from nuro_tts import NeuroSmartGenerator
import pygame
import pygame._sdl2.audio as sdl2_audio
import pyaudio
import wave
import time
import numpy as np

NEURO_MODEL_PATH = r"C:\Peter\TR and M\Dc_Bot\mod\Neuro.pth"
NEURO_INDEX_PATH = r"C:\Peter\TR and M\Dc_Bot\mod\Neuro.index"
INFER_CLI_PATH = r"C:\Peter\TR and M\Dc_Bot\mod\infer_cli.py"
THRESHOLD = 700       # 音量門檻
SILENCE_LIMIT = 1.5   # 自動收工時間
VB_CABLE_IN = "CABLE Input"
RECORD_OUT = "HitPaw"

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch'}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# 搶銀行劇情
ROB_PLOTS = {
    "prep": [
      "🚗 {user} 負責接應，將改裝過的黑色麵包車停在巷口...",
      "🚁 {user} 將直升機飛到銀行上方，將窗戶切割進入...",
      "🔧 {user} 換上電力公司制服，藉由維修名義剪斷了銀行的備用供電線。",
      "💻 {user} 窩在公寓裡，透過暴力破解程序癱瘓了警局的調度系統 5 分鐘。",
      "🎭 {user} 提前在銀行門口布置了『修路中』看板，引導巡邏警車繞道。"
    ],
    "entry": [
      "💥 {user} 扔出一枚閃光彈，趁著混亂帶頭衝進大廳！",
      "📢 {user} 對著天花板開了一槍，大喊：『通通趴下！』",
      "🔕 {user} 使用吸盤與雷射刀，悄無聲息地在二樓落地窗切出一個圓洞。",
      "🆔 {user} 刷開了偽造的高階主管門禁卡，冷靜地走進 VIP 走廊。",
      "🧱 {user} 猛踩油門，開著重型卡車直接撞穿了銀行的側邊外牆！"
    ],
    "vault_drill": [
      "⚙️ {user} 架設起工業級電鑽，鑽頭與保險庫門磨出激烈火花...",
      "📟 {user} 接上破解黑盒，手指在螢幕上飛速敲擊指令...",
      "❄️ {user} 將液態氮灌入鎖芯，隨後用重錘猛力一擊，金屬瞬間粉碎。",
      "🔥 {user} 啟動了鋁熱劑切斷器，高溫融毀了厚達 30 公分的鋼板。",
      "👂 {user} 屏息凝神，用聽診器捕捉轉盤內部彈簧落下的極細微聲響。"
    ],
    "vault_open": [
      "🔓 隨著一聲清脆的響聲，{user} 成功推開了厚重的保險庫門！",
      "🌟 沉重的齒輪緩緩轉動，{user} 被門後堆積如山的金磚晃得睜不開眼。",
      "💨 氣壓平衡發出噴氣聲，{user} 拉開了這扇價值連城的最後防線。",
      "🚨 門開了，但內部的紅外線感應器開始閃爍，{user} 知道時間不多了！",
      "🛠️ 經過最後一次敲擊，保險庫手把終於鬆動，{user} 露出了一抹壞笑。"
    ],
    "loot": [
      "💰 {user} 瘋狂地將一疊疊美鈔塞進運動提袋中...",
      "💎 {user} 撬開了私人保險箱，發現了幾顆碩大的鑽石！",
      "👑 {user} 發現了收藏架上的純金古董皇冠，毫不猶豫地將它收入袋中。",
      "🧧 {user} 打開保險箱，發現裡面裝滿了不記名債券與秘密合約。",
      "🧱 {user} 快速搬運著沉重的金磚，每一塊都象徵著後半輩子的自由。"
    ],
    "police": [
      "🚨 警笛聲響徹街道，{user} 透過無線電大喊：『警察來了，準備撤離！』",
      "🚓 第一輛巡邏車甩尾停在門口，{user} 看見警員已經拔槍尋求掩護。",
      "🚁 遙遠的天空傳來直升機螺旋槳聲，{user} 知道特種部隊即將封鎖現場。",
      "👮 擴音器傳來最後通牒：『裡面的武裝分子聽著，你們已經被包圍了！』",
      "⚡ 銀行的靜默報警器被觸發，{user} 發現外面早已佈滿了藍紅閃爍的燈光。"
    ],
    "skirmish": [
      "🔫 {user} 拿起步槍對著防暴盾牌猛烈開火，壓制住了警方的包圍...",
      "🔥 {user} 扔出一枚煙霧彈，掩護隊友衝向出口！",
      "💥 {user} 啟動了預埋在街口汽車下的炸彈，巨大的爆炸聲讓警方陣腳大亂。",
      "🏹 {user} 爬上屋頂天台，用狙擊步槍點射那些試圖包抄的特警。",
      "🛡️ {user} 躲在圓柱後與警方展開激烈對射，子彈擊碎了銀行華麗的大理石柱。"
    ],
    "escape": [
      "🏎️ 最終猛踩油門，設法甩開了後方的巡邏車...",
      "🏁 最終穿過狹窄的後巷，前進至預定的安全屋...",
      "🌊 最終帶領隊友跳上運河旁的快艇，在海警的追逐中瘋狂加速...",
      "🚇 最終丟下受損的車輛，帶著大袋現金試圖混入了混亂的地鐵人群中...",
      "✈️ 最終抵達了私人機場，在警方趕到前設法飛往了沒有引渡條約的島嶼..."
    ]
}

# 讀取授權名單的工具函式
def load_allowed_users():
    config_path = "C:\\Peter\\TR and M\\Dc_Bot\\config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f).get("allowed_users", [])
    return []
def save_allowed_users(user_list):
    with open("C:\\Peter\\TR and M\\Dc_Bot\\config.json", "w", encoding="utf-8") as f:
        json.dump({"allowed_users": user_list}, f, indent=4)

# 釣魚
class FishingView(discord.ui.View):
    def __init__(self, interaction, cog_instance):
        super().__init__(timeout=None)
        self.cog = cog_instance
        self.uid = str(interaction.user.id)

# 釣魚確認 View（確認後才執行出海）
class FishConfirmView(discord.ui.View):
    def __init__(self, interaction, cog_instance, times, cost, boat_lv, rod_lv, per_fish_time, duration, finish_time):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.cog = cog_instance
        self.uid = interaction.user.id
        self.times = times
        self.cost = cost
        self.boat_lv = boat_lv
        self.rod_lv = rod_lv
        self.per_fish_time = per_fish_time
        self.duration = duration
        self.finish_time = finish_time
        self.pa = pyaudio.PyAudio()
        self.loop = asyncio.get_event_loop()

    @discord.ui.button(label="確認出海", style=discord.ButtonStyle.green)
    async def confirm_fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            return await interaction.response.send_message("❌ 這不是你的釣魚任務！", ephemeral=True)

        await self.cog.execute_fish_start(interaction, self)

# blackjack 介面設定
BLACKJACK_AVATAR_URL = None  # 可設為角色頭像圖網址，例如 "https://i.imgur.com/xxx.png"

# blackjack 按鈕邏輯 View
class BlackjackView(discord.ui.View):
    def _rank_to_key(self, rank):
        # 將 J/Q/K/A 轉為小寫字母，其餘維持原數字
        face_map = {"J": "j", "Q": "q", "K": "k", "A": "a"}
        return face_map.get(rank, rank)

    def __init__(self, interaction, p_hand, d_hand, deck, calc_func, bank, bet, cog_instance):
        super().__init__(timeout=60)
        self.main_interaction = interaction
        self.p_hand = p_hand
        self.d_hand = d_hand
        self.deck = deck
        self.calc = calc_func
        self.bank = bank
        self.bet = bet
        self.uid = str(interaction.user.id)
        self.gid = str(interaction.guild.id)
        self.cog = cog_instance
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.DATA_PATH = os.path.join(self.root_dir, "C:/Peter/TR and M/Dc_Bot/mod/active_fishers.json")
        # 初始化花色與 emoji 對照表
        self.suits_map = {"♠️": "s", "♥️": "h", "♦️": "d", "♣️": "c"}
        self.card_emoji_ids = {
            "sq": 1472706402933018726, "sk": 1472706401557020763, "sj": 1472706399996743731, "sa": 1472706398029746329,
            "s10": 1472706396343505030, "s9": 1472706394628165642, "s8": 1472706393004965888, "s7": 1472706391629107321,
            "s6": 1472706389938933834, "s5": 1472706388374589560, "s4": 1472706386889670821, "s3": 1472706385266475113,
            "s2": 1472706384217768150,
            "hq": 1472706380468191446, "hk": 1472706378538680432, "hj": 1472706376986791996, "ha": 1472706375183368267,
            "h10": 1472706373749047464, "h9": 1472706372608069906, "h8": 1472706370875691210, "h7": 1472706369327988927,
            "h6": 1472706367931420722, "h5": 1472706365977002186, "h4": 1472706364039102556, "h3": 1472706362214584340,
            "h2": 1472706360700567552,
            "dq": 1472706358850752532, "dk": 1472706357139341444, "dj": 1472706355117953114, "da": 1472706353599615157,
            "d10": 1472706351971958939, "d9": 1472706349652508722, "d8": 1472706348109271060, "d7": 1472706346397995028,
            "d6": 1472706344233599242, "d5": 1472706342606082161, "d4": 1472706341230608414, "d3": 1472706339842031824,
            "d2": 1472706338160377926,
            "cq": 1472706336142790770, "ck": 1472706334481973419, "cj": 1472706332749598770, "ca": 1472706330988122245,
            "c10": 1472706329499013212, "c9": 1472706327401726165, "c8": 1472706325761888336, "c7": 1472706324340015225,
            "c6": 1472706322926669844, "c5": 1472706321383162012, "c4": 1472706319793393860, "c3": 1472706318304284833,
            "c2": 1472706316375031879,
            "card_back": 1472706314969944247,
        }
    # 其餘方法同樣左對齊 class
    def _get_bj_control(self):
        # 每次都重新讀取 C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json
        try:
            bj_path = os.path.join(self.root_dir, "C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json")
            if os.path.exists(bj_path):
                with open(bj_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get(str(self.uid))
        except Exception as e:
            print(f"[BJ控制] 讀取失敗: {e}")
        return None

    def get_controlled_card(self, who, for_dealer=False):
        """
        who: 'player' or 'dealer'
        for_dealer: True if dealer抽牌
        """
        control = self._get_bj_control()
        mode = (control or {}).get("mode", "").lower()
        # --- 必贏模式 ---
        if mode == 'w':
            if who == 'player':
                cur = self.calc(self.p_hand)
                # 若點數已高(18-20)，只給A/2/3等小牌
                if cur >= 18:
                    safe_cards = []
                    for i, card in enumerate(self.deck):
                        val = self.calc(self.p_hand + [card])
                        # 僅允許21以下，且優先A/2/3
                        if val <= 21:
                            rank = str(card[:-2]).upper()
                            if rank in ('A', '2', '3'):
                                safe_cards.append((i, card))
                    if safe_cards:
                        idx, card = safe_cards[0]
                        return self.deck.pop(idx)
                # 其他情況，給任何不爆的牌
                for i, card in enumerate(self.deck):
                    val = self.calc(self.p_hand + [card])
                    if val <= 21:
                        return self.deck.pop(i)
                # 沒有安全牌就pop
                return self.deck.pop()
            elif who == 'dealer' and for_dealer:
                p_val = self.calc(self.p_hand)
                d_val = self.calc(self.d_hand)
                # 玩家點數高(>=19)，莊家只能停在小於玩家
                if p_val >= 19:
                    for i, card in enumerate(self.deck):
                        val = self.calc(self.d_hand + [card])
                        if val < p_val and val >= 17:
                            return self.deck.pop(i)
                    # 若無法精準控制，給最小不爆牌
                    min_card = None
                    min_val = 99
                    for i, card in enumerate(self.deck):
                        val = self.calc(self.d_hand + [card])
                        if val <= 21 and val < min_val:
                            min_card = (i, card)
                            min_val = val
                    if min_card:
                        idx, card = min_card
                        return self.deck.pop(idx)
                # 玩家點數較低(<=16)，莊家爆牌
                elif p_val <= 16:
                    for i, card in enumerate(self.deck):
                        val = self.calc(self.d_hand + [card])
                        if val > 21:
                            return self.deck.pop(i)
                # 其他情況正常pop
                return self.deck.pop()
        # --- 必輸模式 ---
        if mode == 'l':
            if who == 'player':
                cur = self.calc(self.p_hand)
                # 16以下隨機給牌
                if cur <= 16:
                    idx = random.randrange(len(self.deck))
                    return self.deck.pop(idx)
                # 17以上，強制爆牌
                else:
                    for i, card in enumerate(self.deck):
                        val = self.calc(self.p_hand + [card])
                        if val > 21:
                            return self.deck.pop(i)
                    # 若找不到爆牌，給最大牌
                    max_card = max(enumerate(self.deck), key=lambda x: self._card_value(x[1]))
                    return self.deck.pop(max_card[0])
            elif who == 'dealer' and for_dealer:
                p_val = self.calc(self.p_hand)
                d_val = self.calc(self.d_hand)
                # 讓莊家大於玩家且<=21，優先21或大1點
                best = None
                for i, card in enumerate(self.deck):
                    val = self.calc(self.d_hand + [card])
                    if d_val < 17 and val > p_val and val <= 21:
                        # 優先21或大1點
                        if val == 21:
                            return self.deck.pop(i)
                        if not best or val < best[1]:
                            best = (i, val)
                if best:
                    return self.deck.pop(best[0])
        # 無控制時正常發牌
        return self.deck.pop()

    def get_card_emoji(self, card_str, use_card_back=False):
        """將 'J♥️' 轉為 Discord 自訂 emoji 字串 <:名稱:id>（你機器人伺服器上的 emoji 會直接顯示）"""
        if use_card_back:
            eid = self.card_emoji_ids.get("card_back")
            if eid:
                return f"<:card_back:{eid}>"
            return "🂠"
        rank = card_str[:-2]
        suit_icon = card_str[-2:]
        suit = self.suits_map.get(suit_icon, "s")
        key = f"{suit}{self._rank_to_key(rank)}"
        eid = self.card_emoji_ids.get(key)
        if eid:
            return f"<:{key}:{eid}>"
        return "🃏"

    @discord.ui.button(label="要牌", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid:
            return await interaction.response.send_message("這不是你的牌局！", ephemeral=True)

        # 每次都重新讀取控制
        card = self.get_controlled_card('player')
        self.p_hand.append(card)
        if self.calc(self.p_hand) > 21:
            await self.finish_game(interaction, "💥 你爆牌了！莊家獲勝。", discord.Color.red(), 'loss')
        else:
            await self.update_display(interaction)

    @discord.ui.button(label="結束", style=discord.ButtonStyle.danger)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid:
            return await interaction.response.send_message("這不是你的牌局！", ephemeral=True)

        d_val = self.calc(self.d_hand)
        while d_val < 17:
            card = self.get_controlled_card('dealer', for_dealer=True)
            self.d_hand.append(card)
            d_val = self.calc(self.d_hand)

        p_val = self.calc(self.p_hand)
        if d_val > 21:
            msg, res_type, color = "🎊 莊家爆牌！你贏了！", 'win', discord.Color.green()
        elif p_val > d_val:
            msg, res_type, color = f"🎉 你以 {p_val} 點擊敗莊家 {d_val} 點！", 'win', discord.Color.green()
        elif p_val < d_val:
            msg, res_type, color = f"👻 莊家 {d_val} 點勝出，你輸了。", 'loss', discord.Color.red()
        else:
            msg, res_type, color = "🤝 雙方平手，退回賭注。", 'draw', discord.Color.light_grey()

        await self.finish_game(interaction, msg, color, res_type)

    def _build_hand_display(self, value, cards, hide_second=True):
        """組合手牌顯示：一級標題 # 讓點數與 emoji 變大"""
        if hide_second and len(cards) >= 2:
            emojis = self.get_card_emoji(cards[0]) + " " + self.get_card_emoji(None, use_card_back=True)
        else:
            emojis = " ".join([self.get_card_emoji(c) for c in cards])
        return f"# {value} {emojis}"

    async def update_display(self, interaction):
        """更新遊戲畫面（米米警察風格），手牌放 description 讓 # 標題能正確放大"""
        embed = discord.Embed(title="🕐 21點遊戲進行中", color=0x3498db)

        # 莊家 (只顯示第一張，第二張用卡背) + 玩家，全部放 description 讓 # 一級標題能放大
        d_val = self.calc([self.d_hand[0]])
        d_display = self._build_hand_display(d_val, self.d_hand, hide_second=True)
        p_val = self.calc(self.p_hand)
        p_display = self._build_hand_display(p_val, self.p_hand, hide_second=False)
        embed.description = f"**莊家手牌：**\n{d_display}\n\n**你的手牌：**\n{p_display}"

        # 底部財務資訊（含總盈虧）
        self.bank.users = self.bank.load_data()
        user_data = self.bank.add_stats(int(self.gid), int(self.uid), coin=0)
        bj_pnl = user_data.get("blackjack_pnl", 0)
        pnl_str = f"{bj_pnl:+,}" if bj_pnl != 0 else "0"
        embed.set_footer(text=f"下注: {self.bet} | 餘額: {user_data.get('coin', 0):,} | 總盈虧: {pnl_str}")
        if BLACKJACK_AVATAR_URL:
            embed.set_thumbnail(url=BLACKJACK_AVATAR_URL)

        await interaction.response.edit_message(embed=embed, view=self)

    async def finish_game(self, interaction, result_text, color, result_type):
        """結算畫面，顯示雙方所有手牌，並更新總盈虧"""
        self.clear_items()

        self.bank.users = self.bank.load_data()

        payout = 0
        res = str(result_type).strip().lower()
        if res == 'win': payout = int(self.bet) * 2
        elif res == 'draw': payout = int(self.bet)

        user_data = self.bank.add_stats(self.gid, self.uid, coin=payout)

        # 追蹤 21 點總盈虧、勝場、總場次
        pnl_delta = 0
        if res == 'win':
            pnl_delta = int(self.bet)
            user_data["blackjack_wins"] = user_data.get("blackjack_wins", 0) + 1
        elif res == 'loss':
            pnl_delta = -int(self.bet)
        user_data["blackjack_pnl"] = user_data.get("blackjack_pnl", 0) + pnl_delta
        user_data["blackjack_games"] = user_data.get("blackjack_games", 0) + 1
        self.bank.save_data()

        d_val = self.calc(self.d_hand)
        d_emojis = " ".join([self.get_card_emoji(c) for c in self.d_hand])
        p_val = self.calc(self.p_hand)
        p_emojis = " ".join([self.get_card_emoji(c) for c in self.p_hand])

        # 贏得/損失 醒目顯示（最重要）
        win_loss_line = ""
        if res == 'win':
            win_loss_line = f"✅ 贏得 {int(self.bet)} 💰"
        elif res == 'loss':
            win_loss_line = f"❌ 損失 {int(self.bet)} 💰"
        else:
            win_loss_line = "🤝 平手 退回賭注"

        # 勝率與總場次
        total_games = user_data.get("blackjack_games", 1)
        wins = user_data.get("blackjack_wins", 0)
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        stats_line = f"➡️ 勝率 {win_rate:.1f}% 總場次 {total_games}"

        bj_pnl = user_data.get("blackjack_pnl", 0)
        pnl_str = f"{bj_pnl:+,}" if bj_pnl != 0 else "0"

        # 結算介面：結果標題 → 贏得/損失 → 勝率 → 手牌 → 底部財務
        embed = discord.Embed(
            title="🎰 21點 遊戲結算",
            description=(
                f"### {result_text}\n\n"
                f"### {win_loss_line}\n\n"
                f"{stats_line}\n\n"
                f"**🎰 莊家手牌：**\n# {d_val} {d_emojis}\n\n"
                f"**你的手牌：**\n# {p_val} {p_emojis}"
            ),
            color=color
        )
        embed.set_footer(text=f"下注: {self.bet} | 餘額: {user_data['coin']:,} | 總盈虧: {pnl_str}")
        if BLACKJACK_AVATAR_URL:
            embed.set_thumbnail(url=BLACKJACK_AVATAR_URL)

        # 再玩一局按鈕
        retry_btn = discord.ui.Button(label=f"再玩一局 (${self.bet})", style=discord.ButtonStyle.blurple, emoji="🔄")
        async def retry_callback(ri: discord.Interaction):
            if str(ri.user.id) != self.uid: return
            await self.cog.start_blackjack(ri, self.bet)
        retry_btn.callback = retry_callback
        self.add_item(retry_btn)

        double_bet = int(self.bet) * 2
        double_retry_btn = discord.ui.Button(label=f"雙倍下注 (${double_bet})", style=discord.ButtonStyle.danger, emoji="🔥")

        async def double_retry_callback(ri: discord.Interaction):
            if str(ri.user.id) != self.uid: return
            # 這裡直接呼叫 start_blackjack 並傳入兩倍的賭金
            await self.cog.start_blackjack(ri, double_bet)

        double_retry_btn.callback = double_retry_callback
        self.add_item(double_retry_btn)

        await interaction.response.edit_message(embed=embed, view=self)

class DragonGateView(discord.ui.View):
    def __init__(self, interaction, user_data, bet, deck, cog, bank):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.user_data = user_data
        self.bet = bet
        self.deck = deck
        self.cog = cog
        self.bank = bank
        self.gate = sorted([self.deck.pop(), self.deck.pop()], key=lambda x: x[1])
        self.is_pair = self.gate[0][1] == self.gate[1][1]

    def card_to_str(self, card):
            suit, val = card
            names = {1: "A", 11: "J", 12: "Q", 13: "K"}
            return f"{suit}{names.get(val, val)}"

    @discord.ui.button(label="射門！ (Shoot)", style=discord.ButtonStyle.green)
    async def shoot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.interaction.user.id):
            return await interaction.response.send_message("這不是你的賭局！", ephemeral=True)

        shoot_card = self.deck.pop()
        p1, p2 = self.gate[0][1], self.gate[1][1]
        val = shoot_card[1]

        # 邏輯判斷
        result = ""
        win = 0
        if val == p1 or val == p2:
            result = f"😱 **撞柱了！！** 賠兩倍！"
            win = -self.bet * 2
        elif p1 < val < p2:
            result = f"🎊 **射中了！** 恭喜贏得獎金！"
            win = self.bet
        else:
            result = f"💨 **射偏了...** 賭金沒收。"
            win = -self.bet

        await self.finish_game(interaction, shoot_card, result, win)

    @discord.ui.button(label="不射 (Fold)", style=discord.ButtonStyle.gray)
    async def fold(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 折損一半賭金
        loss = self.bet // 2
        self.user_data["coin"] -= loss
        self.bank.save_data()

        # 再來一局按鈕
        retry_btn = discord.ui.Button(label=f"再來一局 (${self.bet})", style=discord.ButtonStyle.blurple, emoji="🔄")
        async def retry_callback(ri: discord.Interaction):
            if str(ri.user.id) != str(self.interaction.user.id): return
            user_data = self.bank.add_stats(ri.guild.id, ri.user.id, coin=0)
            suits = ["♠️", "♥️", "♦️", "♣️"]
            deck = [(s, v) for s in suits for v in range(1, 14)]
            random.shuffle(deck)
            view = DragonGateView(ri, user_data, self.bet, deck, self.cog, self.bank)
            embed = discord.Embed(title="🐉 射龍門 (Shoot the Dragon Gate)", color=0xf1c40f)
            embed.add_field(name="⚖️ 目前門柱", value=f"{view.card_to_str(view.gate[0])}  ↔️  {view.card_to_str(view.gate[1])}", inline=False)
            embed.add_field(name="💰 下注金額", value=f"`${self.bet:,}` (已扣除)", inline=True)
            embed.set_footer(text="提示：撞柱賠兩倍！")
            await ri.response.edit_message(content=None, embed=embed, view=view)
        retry_btn.callback = retry_callback

        # 雙倍下注按鈕
        double_bet = int(self.bet) * 2
        double_retry_btn = discord.ui.Button(label=f"雙倍下注 (${double_bet})", style=discord.ButtonStyle.danger, emoji="🔥")
        async def double_retry_callback(ri: discord.Interaction):
            if str(ri.user.id) != str(self.interaction.user.id): return
            user_data = self.bank.add_stats(ri.guild.id, ri.user.id, coin=0)
            suits = ["♠️", "♥️", "♦️", "♣️"]
            deck = [(s, v) for s in suits for v in range(1, 14)]
            random.shuffle(deck)
            view = DragonGateView(ri, user_data, double_bet, deck, self.cog, self.bank)
            embed = discord.Embed(title="🐉 射龍門 (Shoot the Dragon Gate)", color=0xf1c40f)
            embed.add_field(name="⚖️ 目前門柱", value=f"{view.card_to_str(view.gate[0])}  ↔️  {view.card_to_str(view.gate[1])}", inline=False)
            embed.add_field(name="💰 下注金額", value=f"`${double_bet:,}` (已扣除)", inline=True)
            embed.set_footer(text="提示：撞柱賠兩倍！")
            await ri.response.edit_message(content=None, embed=embed, view=view)
        double_retry_btn.callback = double_retry_callback

        retry_view = discord.ui.View()
        retry_view.add_item(retry_btn)
        retry_view.add_item(double_retry_btn)

        await interaction.response.edit_message(content=f"🏳️ 你退縮了，損失一半賭金 (${loss})。", embed=None, view=retry_view)

    async def finish_game(self, interaction, shoot_card, result, win):
        self.user_data["coin"] += win
        self.bank.save_data()

        embed = discord.Embed(title="🐉 射龍門結果", color=0x00ff00 if win > 0 else 0xff0000)
        embed.add_field(name="門柱", value=f"{self.card_to_str(self.gate[0])}  ↔️  {self.card_to_str(self.gate[1])}", inline=False)
        embed.add_field(name="你的牌", value=f"🎯 **{self.card_to_str(shoot_card)}**", inline=False)
        embed.description = f"### {result}\n你的損益: `{win:+,}`\n目前餘額: `${self.user_data['coin']:,}`"

        # 再來一局按鈕
        retry_btn = discord.ui.Button(label=f"再來一局 (${self.bet})", style=discord.ButtonStyle.blurple, emoji="🔄")
        async def retry_callback(ri: discord.Interaction):
            if str(ri.user.id) != str(self.interaction.user.id): return
            # 重新開一局 dragongate
            # 重新洗牌與資料
            user_data = self.bank.add_stats(ri.guild.id, ri.user.id, coin=0)
            suits = ["♠️", "♥️", "♦️", "♣️"]
            deck = [(s, v) for s in suits for v in range(1, 14)]
            random.shuffle(deck)
            view = DragonGateView(ri, user_data, self.bet, deck, self.cog, self.bank)
            embed = discord.Embed(title="🐉 射龍門 (Shoot the Dragon Gate)", color=0xf1c40f)
            embed.add_field(name="⚖️ 目前門柱", value=f"{view.card_to_str(view.gate[0])}  ↔️  {view.card_to_str(view.gate[1])}", inline=False)
            embed.add_field(name="💰 下注金額", value=f"`${self.bet:,}` (已扣除)", inline=True)
            embed.set_footer(text="提示：撞柱賠兩倍！")
            await ri.response.edit_message(embed=embed, view=view)
        retry_btn.callback = retry_callback

        # 雙倍下注按鈕
        double_bet = int(self.bet) * 2
        double_retry_btn = discord.ui.Button(label=f"雙倍下注 (${double_bet})", style=discord.ButtonStyle.danger, emoji="🔥")
        async def double_retry_callback(ri: discord.Interaction):
            if str(ri.user.id) != str(self.interaction.user.id): return
            user_data = self.bank.add_stats(ri.guild.id, ri.user.id, coin=0)
            suits = ["♠️", "♥️", "♦️", "♣️"]
            deck = [(s, v) for s in suits for v in range(1, 14)]
            random.shuffle(deck)
            view = DragonGateView(ri, user_data, double_bet, deck, self.cog, self.bank)
            embed = discord.Embed(title="🐉 射龍門 (Shoot the Dragon Gate)", color=0xf1c40f)
            embed.add_field(name="⚖️ 目前門柱", value=f"{view.card_to_str(view.gate[0])}  ↔️  {view.card_to_str(view.gate[1])}", inline=False)
            embed.add_field(name="💰 下注金額", value=f"`${double_bet:,}` (已扣除)", inline=True)
            embed.set_footer(text="提示：撞柱賠兩倍！")
            await ri.response.edit_message(embed=embed, view=view)
        double_retry_btn.callback = double_retry_callback

        retry_view = discord.ui.View()
        retry_view.add_item(retry_btn)
        retry_view.add_item(double_retry_btn)

        await interaction.response.edit_message(embed=embed, view=retry_view)

# 隱藏訊息
class SecretModal(discord.ui.Modal, title='發布訊息'):
    # 設定輸入框
    secret_text = discord.ui.TextInput(
        label='內容',
        style=discord.TextStyle.paragraph,
        placeholder='在此輸入內容...',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # 引用你原本定義好的 SecretView
        view = SecretView(self.secret_text.value)
        embed = discord.Embed(
            title="隱藏訊息發好囉",
            description="點擊下方按鈕解鎖內容",
            color=0x2b2d31
        )
        embed.set_footer(text=f"由 {interaction.user.display_name} 發布")
        await interaction.response.send_message(embed=embed, view=view)

# 修改後的 SecretView
class SecretView(discord.ui.View):
    def __init__(self, secret_content):
        super().__init__(timeout=None)
        self.content = secret_content

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.secondary)
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 點擊時才讀取檔案，實現即時顯示
        allowed_ids = load_allowed_users()
        if str(interaction.user.id) in allowed_ids:
            await interaction.response.send_message(f"{self.content}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 你的 ID 不在授權名單中。", ephemeral=True)

# 音樂 UI
class ProMusicView(discord.ui.View):
    def __init__(self, voice_client, filename):
        super().__init__(timeout=None)
        self.vc = voice_client
        self.filename = filename

    @discord.ui.button(label="上一首", style=discord.ButtonStyle.secondary, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("目前僅播放單一本地檔案。", ephemeral=True)

    @discord.ui.button(label="暫停/恢復", style=discord.ButtonStyle.primary, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_playing():
            self.vc.pause()
            await interaction.response.send_message("⏸️ 已暫停播放", ephemeral=True)
        elif self.vc.is_paused():
            self.vc.resume()
            await interaction.response.send_message("▶️ 已恢復播放", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 目前沒在播放", ephemeral=True)

    @discord.ui.button(label="下一首", style=discord.ButtonStyle.success, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("後面沒有歌囉！", ephemeral=True)

    @discord.ui.button(label="循環：關閉", style=discord.ButtonStyle.secondary, row=0)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("單曲循環功能開發中。", ephemeral=True)

    @discord.ui.button(label="查看列表", style=discord.ButtonStyle.secondary, row=1)
    async def list_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"📋 目前播放清單：\n1. {self.filename}", ephemeral=True)


    import yt_dlp

# 天氣 UI
class WeatherView(discord.ui.View):
    def __init__(self, forecast_data, city_name, cwa_url):
        super().__init__(timeout=60)
        self.forecast_data = forecast_data
        self.city_name = city_name
        self.cwa_url = cwa_url

        # 修正處：在這裡直接把 Link Button 加進去，確保它一定有 URL
        self.add_item(discord.ui.Button(
            label="7日報導 (CWA)",
            url=self.cwa_url,
            style=discord.ButtonStyle.link,
            emoji="📅"
        ))

    def create_weather_embed(self, day_index):
        # Forecast 每 3 小時一筆，+8 筆大約是 24 小時後
        data = self.forecast_data['list'][day_index * 8]
        dt_txt = data['dt_txt']
        temp = round(data['main']['temp'])
        feel = round(data['main']['feels_like'])
        desc = data['weather'][0]['description']
        hum = data['main']['humidity']
        icon = data['weather'][0]['icon']

        day_label = "今日" if day_index == 0 else "明日"

        embed = discord.Embed(
            title=f"🌤️ {self.city_name} {day_label}天氣預報",
            description=f"**預測狀況**：{desc}\n預報時間：`{dt_txt}`",
            color=0x3498db if day_index == 0 else 0xe67e22,
            url=self.cwa_url,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{icon}@2x.png")
        embed.add_field(name="🌡️ 溫度 / 體感", value=f"`{temp}°C` / `{feel}°C`", inline=True)
        embed.add_field(name="💧 濕度", value=f"`{hum}%`", inline=True)

        # 取得該時段的最高/最低 (注意：這是該 3 小時區間的)
        temp_max = round(data['main']['temp_max'])
        temp_min = round(data['main']['temp_min'])
        embed.add_field(name="📊 預計區間", value=f"最高 `{temp_max}°C` | 最低 `{temp_min}°C`", inline=False)
        embed.set_footer(text="點擊下方按鈕切換日期")
        return embed

    @discord.ui.button(label="今日天氣", style=discord.ButtonStyle.primary, emoji="🏠")
    async def today_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.create_weather_embed(0)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="明天天氣", style=discord.ButtonStyle.success, emoji="⏭️")
    async def tomorrow_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.create_weather_embed(1)
        await interaction.response.edit_message(embed=embed, view=self)

# 播放音樂 UI
class YTMusicView(discord.ui.View):
    def __init__(self, voice_client, info, queue, cog):
        super().__init__(timeout=None)
        self.vc = voice_client
        self.info = info
        self.queue = queue
        self.cog = cog

    @discord.ui.button(label="暫停/恢復", style=discord.ButtonStyle.primary, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_playing():
            self.vc.pause()
            await interaction.response.send_message("⏸️ 已暫停", ephemeral=True)
        elif self.vc.is_paused():
            self.vc.resume()
            await interaction.response.send_message("▶️ 已恢復", ephemeral=True)

    @discord.ui.button(label="下一首", style=discord.ButtonStyle.success, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc:
            self.vc.stop() # 停止當前歌曲會自動觸發 play_next 播放下一首
            await interaction.response.send_message("⏭️ 跳過當前歌曲", ephemeral=True)

    @discord.ui.button(label="查看列表", style=discord.ButtonStyle.secondary, row=1)
    async def list_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.queue:
            return await interaction.response.send_message("📋 目前待播放清單是空的。", ephemeral=True)

        queue_text = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.queue[:10])])
        await interaction.response.send_message(f"📋 **待播放清單 (前10首)：**\n{queue_text}", ephemeral=True)

# 搶銀行 UI（主持人按確認才開始，無倒數）
class RobBankView(discord.ui.View):
    def __init__(self, interaction, cog_instance, cost):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.cog = cog_instance
        self.cost = cost
        self.participants = [interaction.user]

    @discord.ui.button(label="加入", style=discord.ButtonStyle.danger)
    async def join_rob(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id

        if uid in self.cog.active_robbers:
            return await interaction.response.send_message("❌ 你已經在行動中，不能重複參加！", ephemeral=True)

        if interaction.user in self.participants:
            return await interaction.response.send_message("你已經在隊伍中了！", ephemeral=True)

        bank = self.cog.bot.get_cog('BankMod')
        user_data = bank.add_stats(interaction.guild.id, uid, coin=0)
        if user_data['coin'] < self.cost:
            return await interaction.response.send_message(f"❌ 錢不夠支付準備金 {self.cost}！", ephemeral=True)

        self.participants.append(interaction.user)
        self.cog.active_robbers.add(uid)

        if interaction.message and len(interaction.message.embeds) > 0:
            embed = interaction.message.embeds[0]
            participant_list = "\n".join([f"• {p.display_name}" for p in self.participants])
            embed.description = (
                f"**發起人：** {self.interaction.user.mention}\n"
                f"**準備金：** `${self.cost}`\n\n"
                f"👥 **已加入成員 ({len(self.participants)} 人)：**\n{participant_list}\n\n"
                "📋 **主持人確認人數後按「確認開始」按鈕**"
            )
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="確認開始", style=discord.ButtonStyle.green)
    async def confirm_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message("❌ 只有發起人（主持人）可以確認開始！", ephemeral=True)

        for item in self.children:
            item.disabled = True
        if interaction.message and len(interaction.message.embeds) > 0:
            embed = interaction.message.embeds[0]
            participant_list = "\n".join([f"• {p.display_name}" for p in self.participants])
            embed.description = (
                f"**發起人：** {self.interaction.user.mention}\n"
                f"**準備金：** `${self.cost}`\n\n"
                f"👥 **已加入成員 ({len(self.participants)} 人)：**\n{participant_list}\n\n"
                "🚀 **行動開始中...**"
            )
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
        await self.cog.start_robbery_logic(self.interaction, self.participants)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except:
            pass

# 轉帳 UI
class TransferView(discord.ui.View):
    def __init__(self, bot, sender, receiver, amount, fee, total, bank_cog):
        super().__init__(timeout=30)
        self.bot = bot
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.fee = fee
        self.total = total
        self.bank_cog = bank_cog

    @discord.ui.button(label="確認轉帳", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.sender.id:
            return await interaction.response.send_message("❌ 這不是你的轉帳交易！", ephemeral=True)

        # 再次檢查餘額
        s_data = self.bank_cog.add_stats(interaction.guild.id, self.sender.id)
        r_data = self.bank_cog.add_stats(interaction.guild.id, self.receiver.id)

        if s_data["coin"] < self.total:
            return await interaction.response.send_message("❌ 餘額不足，轉帳取消。", ephemeral=True)

        # 執行扣款與撥款
        s_data["coin"] -= self.total
        r_data["coin"] += self.amount
        self.bank_cog.save_data()

        # 製作成功介面 (對應圖片 3)
        embed = discord.Embed(title="💸 轉錢成功", color=0x2ecc71) # 綠色邊框
        embed.set_author(name=f"{self.sender.display_name} ➔ {self.receiver.display_name}", 
                         icon_url=self.sender.avatar.url if self.sender.avatar else None)

        embed.description = f"{self.sender.mention} 成功轉錢給 {self.receiver.mention}"

        embed.add_field(name="轉帳金額", value=f"`{self.amount:,}` 💰", inline=True)
        embed.add_field(name="手續費 (3%)", value=f"`{self.fee:,}` 💰", inline=True)
        embed.add_field(name="發送方支付", value=f"`{self.total:,}` 💰", inline=True)

        embed.add_field(name=f"{self.sender.display_name} 餘額", value=f"`{s_data['coin']:,}` 💰", inline=True)
        embed.add_field(name=f"{self.receiver.display_name} 餘額", value=f"`{r_data['coin']:,}` 💰", inline=True)

        embed.set_footer(text="轉錢操作已完成 (已扣除手續費並記錄)")
        embed.timestamp = datetime.now()

        # 加上錢包圖示 (如果有網址的話可以放 thumbnail)
        # embed.set_thumbnail(url="錢包圖片網址")

        await interaction.response.edit_message(content=None, embed=embed, view=None)

    @discord.ui.button(label="取消", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ 交易已取消。", embed=None, view=None)

# tts
class NeuroSmartGenerator:
    def __init__(self):
        self.pa = pyaudio.PyAudio()

    def get_device_index(self, name_fragment):
        for i in range(self.pa.get_device_count()):
            dev = self.pa.get_device_info_by_index(i)
            if name_fragment in dev['name'] and dev['maxInputChannels'] > 0:
                return i
        return None

    def record_smart_task(self, frames, start_signal, stop_signal):
        dev_idx = self.get_device_index(RECORD_OUT)
        if dev_idx is None: return

        stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=44100,
                              input=True, input_device_index=dev_idx, frames_per_buffer=1024)

        recording_started = False
        last_sound_time = time.time()

        print("監聽中... 等待 Neuro 開口...")

        while not stop_signal.is_set():
            data = stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            peak = np.max(np.abs(audio_data))

            if not recording_started:
                # 只有當音量夠大，才開始錄製
                if peak > THRESHOLD:
                    print("檢測到有效音頻...")
                    recording_started = True
                    last_sound_time = time.time()
            else:
                frames.append(data)
                if peak > THRESHOLD:
                    last_sound_time = time.time()

                # 自動收尾
                if time.time() - last_sound_time > SILENCE_LIMIT and start_signal.is_set():
                    # 💡 絕招：移除最後幾塊可能包含「靜音底噪」的數據
                    for _ in range(3):
                        if frames: frames.pop()
                    print("💤 收尾完成。")
                    break
        stream.stop_stream()
        stream.close()

class MyCommands(commands.Cog):
    BANK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../bank.json")
    FISHER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C:/Peter/TR and M/Dc_Bot/mod/active_fishers.json")
    CLAIM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C:\\Peter\\TR and M\\Dc_Bot\\mod\\claimed_red_packets.json")
    KEYWORDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords.txt")
    BJ_CONTROL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json")
    FISH_POOL = [
        {"name": "核廢料", "price": -3000, "rarity": "災難", "emoji": "☢️", "chance": 10},
        {"name": "垃圾鞋子", "price": 10, "rarity": "垃圾", "emoji": "👟", "chance": 30},
        {"name": "小丑魚", "price": 150, "rarity": "普通", "emoji": "🐠", "chance": 30},
        {"name": "鮭魚", "price": 300, "rarity": "稀有", "emoji": "🐟", "chance": 15},
        {"name": "大白鯊", "price": 1500, "rarity": "史詩", "emoji": "🦈", "chance": 10},
        {"name": "亞特蘭提斯金幣", "price": 5000, "rarity": "傳說", "emoji": "🔱", "chance": 5},
    ]

    def __init__(self, bot, ai_logic_func=None):
        self.bot = bot
        self.ai_logic = ai_logic_func
        self._init_extra_vars()
        self.pa = pyaudio.PyAudio()
        self.is_processing = False

    def _build_fishing_embed(self, type_: str, data: dict) -> discord.Embed:
            """
            type_: 'result' 結算, 'progress' 進行中, 'start' 出海確認, 'done' 已出海
            data: 需包含 user_name, user_id, rarity_counts, total_reward, finish_time, 等
            """
            if type_ == 'result':
                summary = "\n".join([f"• {r}: {count}次" for r, count in data.get("rarity_counts", {}).items()])
                embed = discord.Embed(title="🎣 釣魚成果報告", color=0x2ecc71)
                display_name = data.get("user_name") or f"<@{data.get('user_id')}>"
                embed.description = f"{display_name} 任務已完成！這是你在這段期間的收穫："
                embed.add_field(name="📊 捕獲統計", value=f"```\n{summary}\n```", inline=False)
                embed.add_field(name="💰 最終收益", value=f"**`${data.get('total_reward',0):,}`**", inline=True)
                return embed
            elif type_ == 'progress':
                finish_display = data['finish_time'].strftime("%H:%M:%S")
                embed = discord.Embed(title="🎣 釣魚任務執行中", color=0x3498db)
                embed.description = f"目前正在作業中，預計 **{finish_display}** 回港。"
                return embed
            elif type_ == 'start':
                # 出海確認
                mm, ss = divmod(data['duration'], 60)
                time_str = f"{mm}分{ss}秒" if mm > 0 else f"{ss}秒"
                embed = discord.Embed(title="🚢 漁船出海確認", color=0x2ecc71)
                embed.description = (
                    f"👤 **釣客：** {data['user_mention']}\n"
                    f"🚤 **漁船等級：** `Lv.{data['boat_lv']}`\n"
                    f"🎣 **魚竿等級：** `Lv.{data['rod_lv']}`\n"
                    f"⏱️ **作業速度：** `{data['per_fish_time']:.1f}s` / 竿\n"
                    f"⏳ **總計耗時：** `約 {time_str}`\n"
                    f"🔔 **預計回港：** `{data['finish_time'].strftime('%H:%M:%S')}`\n"
                    f"💰 **消耗：** `${data['cost']:,}`\n\n"
                    "請按下 **確認出海** 開始任務"
                )
                return embed
            elif type_ == 'done':
                mm, ss = divmod(data['duration'], 60)
                time_str = f"{mm}分{ss}秒" if mm > 0 else f"{ss}秒"
                embed = discord.Embed(title="🚢 漁船已出海", color=0x2ecc71)
                embed.description = (
                    f"👤 **釣客：** <@{data['user_id']}>\n"
                    f"🚤 **漁船等級：** `Lv.{data['boat_lv']}`\n"
                    f"⏱️ **作業速度：** `{data['per_fish_time']:.1f}s` / 竿\n"
                    f"⏳ **總計耗時：** `約 {time_str}`\n"
                    f"🔔 **回港時間：** `{data['finish_time'].strftime('%H:%M:%S')}`"
                )
                return embed
            return discord.Embed(title="釣魚通知", description="未知狀態", color=0x95a5a6)

    def _load_json(self, path):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[JSON] 讀取 {path} 失敗: {e}")
        return {}

    def _save_json(self, path, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[JSON] 儲存 {path} 失敗: {e}")

    def record_smart_task(self, frames, start_signal, stop_signal):
        """智慧錄音任務：只錄取從 HitPaw 傳出來有聲音的部分"""
        # 這裡會呼叫你類別內的 get_device_index
        dev_idx = self.get_device_index(RECORD_OUT)
        if dev_idx is None:
            print("❌ 找不到錄音設備 (HitPaw)，請檢查設備名稱！")
            return

        # 初始化串流
        stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=44100,
                              input=True, input_device_index=dev_idx, frames_per_buffer=1024)

        recording_started = False
        last_sound_time = time.time()

        print("🎙️ 智慧監聽中... 等待變聲器輸出...")

        while not stop_signal.is_set():
            try:
                data = stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                peak = np.max(np.abs(audio_data))

                if not recording_started:
                    # 只有當音量超過門檻 (THRESHOLD)，才開始把數據存進 frames
                    if peak > THRESHOLD:
                        print("🔥 檢測到變聲器音頻，開始錄製...")
                        recording_started = True
                        last_sound_time = time.time()
                else:
                    frames.append(data)
                    if peak > THRESHOLD:
                        last_sound_time = time.time()

                    # 自動收尾邏輯：如果靜音超過 SILENCE_LIMIT 秒，且播放已結束
                    if time.time() - last_sound_time > SILENCE_LIMIT and start_signal.is_set():
                        # 移除結尾可能的靜音數據
                        for _ in range(3):
                            if frames: frames.pop()
                        print("💤 錄音收尾完成。")
                        break
            except Exception as e:
                print(f"❌ 錄音過程出錯: {e}")
                break

        stream.stop_stream()
        stream.close()

    def get_device_index(self, name_fragment):
        print("--- 正在掃描音訊設備 ---")
        for i in range(self.pa.get_device_count()):
            dev = self.pa.get_device_info_by_index(i)
            print(f"Index {i}: {dev['name']}") # 👈 這行會印出你電腦所有設備名稱
            if name_fragment in dev['name'] and dev['maxInputChannels'] > 0:
                print(f"✅ 成功找到匹配設備: {dev['name']} (Index {i})")
                return i
        print(f"❌ 找不到包含 '{name_fragment}' 的錄音設備！")
        return None

    def load_keywords(self):
        if not os.path.exists(self.KEYWORDS_PATH):
            with open(self.KEYWORDS_PATH, "w", encoding="utf-8") as f:
                f.write("大紅包\n")
        try:
            with open(self.KEYWORDS_PATH, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"[紅包] 讀取 keywords.txt 失敗: {e}")
            return ["大紅包"]

    def load_claims(self):
        if not os.path.exists(self.CLAIM_PATH):
            self._save_json(self.CLAIM_PATH, {})
        return self._load_json(self.CLAIM_PATH)

    def save_claims(self, claims):
        self._save_json(self.CLAIM_PATH, claims)

    def get_all_fishers(self):
        raw = self._load_json(self.FISHER_PATH)
        # 轉回 datetime
        for uid, info in raw.items():
            if "end_time" in info and isinstance(info["end_time"], str):
                try:
                    info["end_time"] = datetime.fromisoformat(info["end_time"])
                except Exception:
                    pass
            if "start_time" in info and isinstance(info.get("start_time"), str):
                try:
                    info["start_time"] = datetime.fromisoformat(info["start_time"])
                except Exception:
                    pass
        return raw

    def update_fisher(self, user_id, data):
        all_fishers = self.get_all_fishers()
        # datetime 轉字串
        for k in ("start_time", "end_time"):
            if k in data and isinstance(data[k], datetime):
                data[k] = data[k].isoformat()
        all_fishers[str(user_id)] = data
        self.save_active_fishers(all_fishers)

    def save_active_fishers(self, all_fishers):
        if not all_fishers:
            print("[釣魚] save_active_fishers 偵測到空字典，停止存檔以防資料遺失！")
            return
        # datetime 轉字串
        serialized = {}
        for uid, info in all_fishers.items():
            data = {}
            for k, v in info.items():
                if isinstance(v, datetime):
                    data[k] = v.isoformat()
                else:
                    data[k] = v
            serialized[str(uid)] = data
        self._save_json(self.FISHER_PATH, serialized)

    def remove_fisher(self, user_id):
        all_fishers = self.get_all_fishers()
        all_fishers.pop(str(user_id), None)
        self.save_active_fishers(all_fishers)

    def load_keywords(self):
        if not os.path.exists(self.KEYWORDS_PATH):
            with open(self.KEYWORDS_PATH, "w", encoding="utf-8") as f:
                f.write("大紅包\n")
        try:
            with open(self.KEYWORDS_PATH, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"[紅包] 讀取 keywords.txt 失敗: {e}")
            return ["大紅包"]

    def load_claims(self):
        if not os.path.exists(self.CLAIM_PATH):
            self._save_json(self.CLAIM_PATH, {})
        return self._load_json(self.CLAIM_PATH)

    def save_claims(self, claims):
        self._save_json(self.CLAIM_PATH, claims)

    def get_all_fishers(self):
        try:
            if os.path.exists(self.DATA_PATH):
                with open(self.DATA_PATH, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for uid, info in raw.items():
                        if "end_time" in info and isinstance(info["end_time"], str):
                            try:
                                info["end_time"] = datetime.fromisoformat(info["end_time"])
                            except Exception:
                                pass
                        if "start_time" in info and isinstance(info.get("start_time"), str):
                            try:
                                info["start_time"] = datetime.fromisoformat(info["start_time"])
                            except Exception:
                                pass
                    return raw
        except Exception:
            pass
        return {}

    def update_fisher(self, user_id, data):
        try:
            all_fishers = self.get_all_fishers()
            # datetime 轉字串
            for k in ("start_time", "end_time"):
                if k in data and isinstance(data[k], datetime):
                    data[k] = data[k].isoformat()
            all_fishers[str(user_id)] = data
            self.save_active_fishers(all_fishers)
        except Exception as e:
            print(f"[釣魚] update_fisher 寫入失敗: {e}")

    def remove_fisher(self, user_id):
        """刪除釣魚記錄，使用正確的序列化方法"""
        try:
            all_fishers = self.get_all_fishers()
            all_fishers.pop(str(user_id), None)
            self.save_active_fishers(all_fishers)
            print(f"✅ 已刪除玩家 {user_id} 的釣魚記錄")
        except Exception as e:
            print(f"❌ 刪除釣魚記錄失敗: {e}")

    def _find_bank_cog(self):

        # 1. 嘗試標準名稱
        bank = self.bot.get_cog("BankMod")
        if bank and hasattr(bank, 'add_stats'):
            return bank

        # 2. 遍歷所有已載入的 Cog，尋找擁有 add_stats 方法的模組
        for name, cog in self.bot.cogs.items():
            if hasattr(cog, 'add_stats') and name != "MyCommands":
                print(f"DEBUG: 透過特徵搜尋找到銀行模組: {name}")
                return cog
        return None

    def _init_extra_vars(self):
        self.last_word = ""
        self.idiom_file = r"C:\Peter\TR and M\Dc_Bot\idioms.txt"
        self.queues = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        self.stock_cache_file = os.path.join(root_dir, "C:\\Peter\\TR and M\\Dc_Bot\\stock_cache.json") # 快取檔案路徑
        # 優先從 bot.get_cog 獲取，若還沒載入則設為 None
        self.bank = self._find_bank_cog()
        self.active_robbers = set()
        self.DATA_PATH = "C:/Peter/TR and M/Dc_Bot/mod/active_fishers.json"
        self.BJ_CONTROL_PATH = os.path.join(current_dir, "C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json")
        self.GUILD_ID = 1446838276249096228  # 目標伺服器 ID
        self.load_active_fishers()

    def _load_bj_control(self):
        """讀取 C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json"""
        try:
            if os.path.exists(self.BJ_CONTROL_PATH):
                with open(self.BJ_CONTROL_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ 讀取 C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json 失敗: {e}")
        return {}

    def _save_bj_control(self, data):
        """寫入 C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json"""
        try:
            with open(self.BJ_CONTROL_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 寫入 C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json 失敗: {e}")

    def _get_bj_control_override(self, user_id):
        """若玩家在控制名單中，回傳 (result_type, result_text, color) 覆寫；否則回傳 None"""
        data = self._load_bj_control()
        uid_str = str(user_id)
        if uid_str not in data:
            return None
        ent = data[uid_str]
        mode = ent.get("mode", "").lower()
        if mode == "w":
            return ("win", "🎊 後台控制：強制勝利！", discord.Color.green())
        if mode == "l":
            return ("loss", "👻 後台控制：強制失敗。", discord.Color.red())
        return None

    def is_valid_idiom(self, word):
        if not os.path.exists(self.idiom_file):
            print(f"警告：找不到 {self.idiom_file}")
            return True
        try:
            with open(self.idiom_file, "r", encoding="utf-8") as f:
                idioms = {line.strip() for line in f.readlines()}
                return word in idioms
        except Exception as e:
            print(f"讀取成語庫出錯: {e}")
            return False

    def calculate_hand(self, hand):
        value = 0
        aces = 0
        for card in hand:
            # 提取卡牌的面值（牌格式為 "10♥️"、"J♠️" 等，花色佔最後 2 字元）
            rank = card[:-2] if card and len(card) >= 2 else (card[0] if card else '')

            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                aces += 1
                value += 11
            else:
                try:
                    value += int(rank)
                except ValueError:
                    pass  # 如果無法轉換則跳過
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def load_stock_cache(self):
        if os.path.exists(self.stock_cache_file):
            try:
                with open(self.stock_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: return {}
        return {}

    def save_stock_cache(self, cache_data):
        with open(self.stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=4, ensure_ascii=False)

    def create_music_embed(self, info, interaction, queue_len):
        embed = discord.Embed(title="🎵 正在播放", color=0x2ecc71)
        next_song_text = "無" if queue_len == 0 else f"清單中還有 {queue_len} 首歌"
        embed.description = (
            f"**[{info['title']}]({info['webpage_url']})**\n\n"
            f"**作者** **時長**\n"
            f"{info.get('uploader', '未知')}      {info.get('duration_string', '未知')}\n\n"
            f"**進度**\n"
            f"0:00 ▬▬▬▬▬▬▬▬▬▬▬🔘 {info.get('duration_string', '未知')}\n\n"
            f"**循環**：關閉\n"
            f"**下一首**：{next_song_text}"
        )
        if info.get('thumbnail'):
            embed.set_thumbnail(url=info['thumbnail'])
        embed.set_footer(text=f"由 {interaction.user.display_name} 點播", icon_url=interaction.user.display_avatar.url)
        return embed

    def save_active_fishers(self, all_fishers):
        """將完整掛機資料儲存至 JSON 檔案，防止覆蓋其他玩家"""
        if not all_fishers:
            print("[釣魚] save_active_fishers 偵測到空字典，停止存檔以防資料遺失！")
            return
        # datetime 轉字串
        serialized = {}
        for uid, info in all_fishers.items():
            data = {}
            for k, v in info.items():
                if isinstance(v, datetime):
                    data[k] = v.isoformat()
                else:
                    data[k] = v
            serialized[str(uid)] = data
        self._save_json(self.FISHER_PATH, serialized)

    def load_active_fishers(self):
        """從 JSON 檔案載入掛機資料"""
        if os.path.exists(self.DATA_PATH):
            try:
                with open(self.DATA_PATH, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for uid_str, info in raw.items():
                        # 轉回 datetime（若包含 start_time 與 end_time）
                        if "end_time" in info and isinstance(info["end_time"], str):
                            try:
                                info["end_time"] = datetime.fromisoformat(info["end_time"])
                            except Exception:
                                pass
                        if "start_time" in info and isinstance(info.get("start_time"), str):
                            try:
                                info["start_time"] = datetime.fromisoformat(info["start_time"])
                            except Exception:
                                pass
                        # self.active_fishers[int(uid_str)] = info  # 不再用記憶體快取
            except Exception as e:
                print(f"載入釣魚存檔失敗: {e}")

    def cleanup_temp_file(self, file_path):
        """播放完後的清理工作"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🧹 已清理臨時檔案: {file_path}")
        except Exception as e:
            print(f"⚠️ 清理檔案失敗: {e}")

    # --- 訊息處理中心 ---
    @commands.Cog.listener()
    async def on_message(self, message):
        # 排除機器人自己的訊息
        if message.author.bot:
            return

        content = message.content.lower()

        # --- 邏輯 A: 成語接龍 ---
        # 檢查是否存在 last_word 且內容長度為 4 (成語)
        if hasattr(self, 'last_word') and self.last_word and len(content) == 4:
            if message.reference and message.reference.message_id:
                try:
                    replied_msg = message.reference.cached_message or await message.channel.fetch_message(message.reference.message_id)
                    if replied_msg.author.id == self.bot.user.id and self.last_word in replied_msg.content:
                        if content[0] == self.last_word[-1]:
                            # 假設你有 is_valid_idiom 函式
                            if hasattr(self, 'is_valid_idiom') and self.is_valid_idiom(content):
                                self.last_word = content
                                await message.reply(f"✅ **判定成功！**\n下一個字：**{self.last_word[-1]}**")
                                return
                except:
                    pass

        # --- 邏輯 B: 關鍵字反應 ---
        if "nuso" in content:
            await message.add_reaction("✨")

        # --- 邏輯 C: Neuro 對話 (標記時觸發) ---

        if message.reference:
            return
        if self.bot.user.mentioned_in(message):
            if self.is_processing:
                return

            # 設定狀態為忙碌
            self.is_processing = True
            # 清理標記文字
            user_input = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()
            async with message.channel.typing():
                try:
                # 1. 思考 (文字生成)
                    response_text = await self.get_neuro_response(user_input)

                # 2. 回覆文字
                    await message.reply(response_text)

                # 3. 語音處理 (若使用者在語音頻道)
                    if message.author.voice:
                        # 接收產出的隨機檔名 (例如 neuro_2024...wav)
                        produced_wav_path = await self.generate_and_convert(response_text)

                        # 檢查是否有成功產出檔案，再傳給播放器
                        if produced_wav_path:
                            await self.play_neuro_file(message, produced_wav_path)
                        else:
                            print("⚠️ 錄音失敗，沒有產出語音檔案。")

                except Exception as e:
                    print(f"❌ Neuro 邏輯崩潰: {e}")
                finally:
                    # 不論成功或失敗，最後一定要把狀態改回「不忙」，否則機器人會永遠不理人
                    self.is_processing = False
    async def generate_and_convert(self, text):
        # 1. 取得目前路徑並印出
        current_dir = os.getcwd()
        print(f"📂 機器人目前資料夾 (CWD): {current_dir}")

        # 2. 使用時間戳記生成唯一檔名，防止 Permission denied
        # 使用 microsecond 確保即使連發也不會撞名
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_tts = f"temp_{ts}.mp3"
        final_wav = f"neuro_{ts}.wav"

        # 完整路徑印出來給你看
        full_temp_path = os.path.join(current_dir, temp_tts)
        print(f"📝 正在寫入 TTS 暫存檔: {full_temp_path}")

        try:
            # TTS 轉換
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            await communicate.save(temp_tts)
            print(f"✅ TTS 生成成功")
        except Exception as e:
            print(f"❌ 無法寫入 TTS 檔案: {e}")
            return None

        # --- 錄音與播放邏輯 ---
        recorded_frames = []
        play_done_signal = threading.Event()
        force_stop_signal = threading.Event()

        record_thread = threading.Thread(
            target=self.record_smart_task,
            args=(recorded_frames, play_done_signal, force_stop_signal)
        )
        record_thread.start()

        # 播放到變聲器
        pygame.mixer.init()
        devices = sdl2_audio.get_audio_device_names(False)
        target_play = next((d for d in devices if VB_CABLE_IN in d), None)
        pygame.mixer.quit()
        pygame.mixer.init(devicename=target_play)

        pygame.mixer.music.load(temp_tts)
        pygame.mixer.music.play()
        print(f"🔈 正在播放暫存檔到變聲器...")

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        play_done_signal.set()
        record_thread.join(timeout=10)
        force_stop_signal.set()

        # 3. 存成最後的 WAV
        if recorded_frames:
            with wave.open(final_wav, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.pa.get_sample_size(pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(b''.join(recorded_frames))

            print(f"語音成品已儲存: {os.path.abspath(final_wav)}")

            # 播放完畢，卸載音樂並嘗試刪除暫存檔
            pygame.mixer.music.unload()
            try:
                os.remove(temp_tts)
            except:
                pass

            return final_wav # 回傳這個路徑給播放器
        return None
    async def play_neuro_file(self, message, file_path):
        if not os.path.exists(file_path):
            print(f"❌ 找不到要播放的檔案: {file_path}")
            return
        try:
            # 取得語音頻道
            channel = message.author.voice.channel
            vc = discord.utils.get(self.bot.voice_clients, guild=message.guild)

            # 如果機器人不在頻道裡，就進去；如果不在，就跳過來
            if not vc:
                vc = await channel.connect()
            elif vc.channel != channel:
                await vc.move_to(channel)

            # 如果正在播別的（例如音樂），先停掉
            if vc.is_playing():
                vc.stop()

            # 開始播放
            print(f"🎵 Discord 正在播放: {file_path}")
            # 使用 after 參數在播放完後自動清理檔案，防止硬碟爆掉
            vc.play(discord.FFmpegPCMAudio(file_path), after=lambda e: self.cleanup_temp_file(file_path))

        except Exception as e:
            print(f"❌ Discord 播放失敗: {e}")
    async def command_log(self, interaction: discord.Interaction, command: app_commands.Command):
        LOG_CHANNEL_ID = 1471923362581446676
        user = interaction.user
        cmd_name = command.name
        guild = interaction.guild.name if interaction.guild else "私訊"
        # 取得輸入參數
        options = interaction.data.get('options', [])
        args = {opt['name']: opt['value'] for opt in options} if options else "無參數"
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 2. 同時保留 Terminal 顯示 (方便除錯)
        print(f"[{time_str}] {user.display_name} 使用了 /{cmd_name}")
        # 3. 發送到 Discord 頻道
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="📑 指令使用日誌",
                color=0x3498db,
                timestamp=datetime.now()
            )
            embed.add_field(name="使用者", value=f"{user.mention} ({user.id})", inline=False)
            embed.add_field(name="伺服器", value=guild, inline=False)
            embed.add_field(name="指令", value=f"`/{cmd_name}`", inline=False)
            embed.add_field(name="參數內容", value=f"```json\n{args}\n```", inline=False)
            await log_channel.send(embed=embed)


        # 啟動終端監聽線程
        print(f'--- NuSo Online ---')
        await self.bot.change_presence(activity=discord.Game(name="Loss 3.5"))
        threading.Thread(target=self.console_listener, daemon=True).start()
    async def _send_fishing_embed(self, ctx, type_, data, ephemeral=True):
        embed = self._build_fishing_embed(type_, data)
        try:
            if hasattr(ctx, "response") and not ctx.response.is_done():
                await ctx.response.send_message(embed=embed, ephemeral=ephemeral)
            else:
                await ctx.send(embed=embed, ephemeral=ephemeral)
        except Exception as e:
            print(f"⚠️ 發送釣魚 UI 失敗: {e}")

        async def _send_fishing_embed(self, ctx, type_, data, ephemeral=True):
            embed = self._build_fishing_embed(type_, data)
            try:
                if hasattr(ctx, "response") and not ctx.response.is_done():
                    await ctx.response.send_message(embed=embed, ephemeral=ephemeral)
                else:
                    await ctx.send(embed=embed, ephemeral=ephemeral)
            except Exception as e:
                print(f"⚠️ 發送釣魚 UI 失敗: {e}")
    async def process_bj_control(self, args):
        """處理終端指令 bj <display_name> <mode>（由 main.py 終端機轉發）"""
        try:
            parts = args.split(None, 1)
            if len(parts) < 2:
                print("❌ 格式：bj <顯示名稱> <w|l|p>")
                return
            display_name, mode = parts[0], parts[1].lower()
            if mode not in ("w", "l", "p"):
                print("❌ mode 須為 w(必贏)、l(必輸)、p(清除)")
                return

            found = None
            for guild in self.bot.guilds:
                for member in guild.members:
                    if member.display_name == display_name or member.name == display_name:
                        found = member
                        break
                if found:
                    break

            if not found:
                print(f"❌ 找不到成員：{display_name}")
                return

            data = self._load_bj_control()
            uid_str = str(found.id)
            if mode == "p":
                if uid_str in data:
                    del data[uid_str]
                    self._save_bj_control(data)
                    print(f"✅ 已清除 {found.display_name} ({uid_str}) 的 21 點控制紀錄")
                else:
                    print(f"ℹ️ {found.display_name} 無控制紀錄")
            else:
                data[uid_str] = {"mode": mode, "display_name": found.display_name}
                self._save_bj_control(data)
                m = "必贏" if mode == "w" else "必輸"
                print(f"✅ 已設定 {found.display_name} ({uid_str})：{m}")
        except Exception as e:
            print(f"⚠️ 21點控制指令錯誤: {e}")
    async def get_neuro_response(self, user_input):
        """呼叫 Llama 模型生成文字"""
        try:
            # 從 bot 物件中取得模型和 Tokenizer
            tokenizer = self.bot.tokenizer
            model = self.bot.neuro_model

            if model is None:
                return "My brain is not loaded yet..."

            # 你的簡化 Prompt
            prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n你現在是 Neuro-sama。短促、毒舌、傲嬌。<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256).to("cuda")

            # 使用 executor 避免卡住主執行緒
            loop = asyncio.get_event_loop()
            outputs = await loop.run_in_executor(None, lambda: model.generate(
                **inputs,
                max_new_tokens=40,
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
                repetition_penalty=1.2,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            ))

            full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # 取得 assistant 之後的文字
            return full_response.split("assistant")[-1].strip()
        except Exception as e:
            print(f"❌ AI 生成失敗: {e}")
            return "嘖，腦袋轉不動了..."

    @app_commands.command(name="claim", description="輸入密語領取新春紅包！")
    @app_commands.describe(code="請輸入紅包密語")
    async def claim(self, interaction: discord.Interaction, code: str):
        uid = str(interaction.user.id)
        code = code.strip()
        keywords = self.load_keywords()
        if code not in keywords:
            return await interaction.response.send_message("❌ 密語錯誤，請再檢查一下喔！", ephemeral=True)
        claims = self.load_claims()
        user_claims = claims.get(uid, [])
        if code in user_claims:
            return await interaction.response.send_message("⚠️ 這個紅包你已經領過囉！", ephemeral=True)
        # 發錢
        bank = self.bot.get_cog('BankMod')
        if not bank:
            return await interaction.response.send_message("❌ 系統錯誤，找不到銀行模組！", ephemeral=True)
        try:
            bank.add_stats(interaction.guild.id, interaction.user.id, coin=100000)
            bank.save_data()
        except Exception as e:
            print(f"[紅包] 發錢失敗: {e}")
            return await interaction.response.send_message("❌ 發放金幣時發生錯誤，請聯絡管理員。", ephemeral=True)
        # 更新紀錄
        user_claims.append(code)
        claims[uid] = user_claims
        self.save_claims(claims)
        # Embed UI
        embed = discord.Embed(title="🧧 新春大紅包領取成功！", color=0xFF0000)
        embed.description = "恭喜你獲得了 100,000 金幣！祝你大年初一開春大吉！"
        embed.set_footer(text=f"本次領取密語：{code}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 抽籤指令
    @app_commands.command(name="choose", description="幫你從多個選項中選一個")
    @app_commands.describe(選項="請輸入選項，空格分隔")
    async def choose(self, interaction: discord.Interaction, 選項: str):
        selection_list = 選項.split()
        picked = random.choice(selection_list) if selection_list else "沒給選項標題"
        await interaction.response.send_message(f"NuSo 幫你選了：**{picked}**")

    # Ping 指令
    @app_commands.command(name="ping", description="檢查延遲")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"機器人延遲為 {round(self.bot.latency * 1000)}ms")

    # 成語接龍指令
    @app_commands.command(name="idiom_start", description="開始一個成語接龍遊戲")
    @app_commands.describe(word="請輸入一個四字成語作為開頭")
    async def idiom_start(self, interaction: discord.Interaction, word: str):
        if len(word) != 4:
            await interaction.response.send_message("請輸入一個四字成語！", ephemeral=True)
            return
        self.last_word = word
        await interaction.response.send_message(f"🏁 成語接龍開始！\n當前成語：**{word}**\n請接下一個字：**{word[-1]}**")

    # 整合 Bank 系統的 21 點
    @app_commands.command(name="blackjack", description="跟我玩一場 21 點！")
    @app_commands.describe(bet="下注金額")
    async def blackjack_cmd(self, interaction: discord.Interaction, bet: int):
        await self.start_blackjack(interaction, bet)
    async def start_blackjack(self, interaction: discord.Interaction, bet: int):
        # 確保 bank 已正確載入
        if not self.bank or not hasattr(self.bank, 'add_stats'):
            self.bank = self._find_bank_cog()

        if not self.bank:
            print("ERROR: 21點無法獲取銀行模組 (BankMod)")
            return await (interaction.followup.send if interaction.response.is_done() else interaction.response.send_message)("❌ 銀行系統尚未就緒或未載入，請聯繫管理員！", ephemeral=True)

        try:
            user_data = self.bank.add_stats(interaction.guild.id, interaction.user.id, coin=0)
        except Exception as e:
            print(f"ERROR: 呼叫銀行模組失敗: {e}")
            return await (interaction.followup.send if interaction.response.is_done() else interaction.response.send_message)("❌ 銀行系統通訊錯誤！", ephemeral=True)

        if user_data['coin'] < bet:
            return await (interaction.followup.send if interaction.response.is_done() else interaction.response.send_message)("❌ 錢不夠！", ephemeral=True)
        if bet > 500000:
            return await (interaction.followup.send if interaction.response.is_done() else interaction.response.send_message)("❌ 太多了！最多五十萬", ephemeral=True)

        self.bank.add_stats(interaction.guild.id, interaction.user.id, coin=-bet)
        self.bank.save_data()

        # 初始化牌組
        suits = ["♠️", "♥️", "♦️", "♣️"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        deck = [f"{v}{s}" for s in suits for v in ranks]
        random.shuffle(deck)

        # 動態控制起手牌
        control = None
        try:
            bj_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C:\\Peter\\TR and M\\Dc_Bot\\mod\\blackjack_control.json")
            if os.path.exists(bj_path):
                with open(bj_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                control = data.get(str(interaction.user.id))
        except Exception as e:
            print(f"[BJ控制] 開局讀取失敗: {e}")

        # 起手兩張牌必須完全隨機
        p_hand = [deck.pop(), deck.pop()]
        d_hand = [deck.pop(), deck.pop()]

        # 這裡的 calculate_hand 應該是你 Cog 裡原有的函式
        view = BlackjackView(interaction, p_hand, d_hand, deck, self.calculate_hand, self.bank, bet, self)

        d_val = self.calculate_hand([d_hand[0]])
        dealer_display = f"# {d_val} {view.get_card_emoji(d_hand[0])} {view.get_card_emoji(None, use_card_back=True)}"
        p_val = self.calculate_hand(p_hand)
        p_emojis = " ".join([view.get_card_emoji(c) for c in p_hand])
        embed = discord.Embed(
            title="🕐 21點遊戲進行中",
            description=f"**莊家手牌：**\n{dealer_display}\n\n**你的手牌：**\n# {p_val} {p_emojis}",
            color=0x3498db
        )

        user_data = self.bank.add_stats(interaction.guild.id, interaction.user.id, coin=0)
        bj_pnl = user_data.get("blackjack_pnl", 0)
        pnl_str = f"{bj_pnl:+,}" if bj_pnl != 0 else "0"
        embed.set_footer(text=f"下注: {bet} | 餘額: {user_data.get('coin', 0):,} | 總盈虧: {pnl_str}")
        if BLACKJACK_AVATAR_URL:
            embed.set_thumbnail(url=BLACKJACK_AVATAR_URL)

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)

    # 股票查詢指令
    @app_commands.command(name="stock_search", description="查詢股票(目前僅限美股)")
    @app_commands.describe(股票代碼="請輸入美股代碼，例如 AAPL 或 NVDA")
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def stock(self, interaction: discord.Interaction, 股票代碼: str):
        await interaction.response.defer()
        data, source = await self.get_stock_data(股票代碼.upper())

        if not data:
            await interaction.followup.send(f"❌ 找不到股票代碼 `{股票代碼}`")
            return

        color = 0x2ecc71 if data['change'] >= 0 else 0xe74c3c
        embed = discord.Embed(title=f"📈 {data['name']} ({data['ticker']})", color=color, timestamp=datetime.now())
        embed.add_field(name="當前價格", value=f"**{data['price']:.2f} {data['currency']}**", inline=True)
        embed.add_field(name="漲跌幅", value=f"{data['change']:+.2f} ({data['percent']:+.2f}%)", inline=True)
        embed.set_footer(text=f"來源: {source} | 更新時間: {data['update_time']}")
        await interaction.followup.send(embed=embed)
    async def get_stock_data(self, ticker):
        today = datetime.now().strftime("%Y-%m-%d")
        cache = self.load_stock_cache()

        # 檢查快取
        if today in cache and ticker in cache[today]:
            return cache[today][ticker], "JSON 快取"

        # 呼叫 API (Twelve Data)
        API_KEY = "7b125e135ebb41a89911571ba40e6f94" # 你的 Key
        url = f"https://api.twelvedata.com/quote?symbol={ticker}&apikey={API_KEY}"

        try:
            res = requests.get(url).json()
            # 台股自動修正邏輯
            if ("code" in res and res["code"] != 200) and ticker.isdigit():
                ticker_tpe = f"{ticker}:TWSE"
                res = requests.get(f"https://api.twelvedata.com/quote?symbol={ticker_tpe}&apikey={API_KEY}").json()
                ticker = ticker_tpe

            if "code" in res and res["code"] != 200:
                return None, None

            # 整理資料
            stock_info = {
                "name": res.get("name", ticker),
                "ticker": ticker,
                "price": float(res['close']),
                "change": float(res['change']),
                "percent": float(res['percent_change']),
                "currency": res.get("currency", "USD"),
                "update_time": datetime.now().strftime("%H:%M:%S")
            }

            # 更新快取
            if today not in cache: cache = {today: {}}
            cache[today][ticker] = stock_info
            self.save_stock_cache(cache)
            return stock_info, "Twelve Data API"
        except:
            return None, None

    # 購買股票
    @app_commands.command(name="stock_buy", description="購買股票並記錄成本")
    @app_commands.describe(股票代碼="股票代碼 (如: AAPL, NVDA)", 數量="購買的股數")
    @app_commands.guild_only()
    async def buy_stock(self, interaction: discord.Interaction, 股票代碼: str, 數量: int):
        if 數量 <= 0:
            await interaction.response.send_message("❌ 購買數量須大於 0", ephemeral=True)
            return

        await interaction.response.defer()
        bank = self.bot.get_cog('BankMod')
        data, source = await self.get_stock_data(股票代碼.upper())
        if not data:
            await interaction.followup.send(f"❌ 無法取得 `{股票代碼}` 的價格，交易取消。")
            return

        ticker = data['ticker']
        current_price = data['price']
        total_cost = int(current_price * 數量)
        gid, uid = str(interaction.guild.id), str(interaction.user.id)

        bank.users = bank.load_data()
        user_coin = bank.users.get(gid, {}).get(uid, {}).get("coin", 0)

        if user_coin < total_cost:
            await interaction.followup.send(f"❌ 金幣不足！需要 `{total_cost}`，你目前只有 `{user_coin}`。")
            return

        # 執行扣款
        bank.add_stats(gid, uid, coin=-total_cost)
        user_data = bank.users[gid][uid]

        # 初始化擴充欄位
        if "stocks" not in user_data: user_data["stocks"] = {}
        if "stock_costs" not in user_data: user_data["stock_costs"] = {}

        # 增加持股與累計成本
        user_data["stocks"][ticker] = user_data["stocks"].get(ticker, 0) + 數量
        user_data["stock_costs"][ticker] = user_data["stock_costs"].get(ticker, 0) + total_cost
        bank.save_data()

        embed = discord.Embed(title="✅ 買入成交", color=0x2ecc71, timestamp=datetime.now())
        embed.description = f"已購入 **{數量}** 股 **{data['name']}**"
        embed.add_field(name="成交單價", value=f"`{current_price}`", inline=True)
        embed.add_field(name="總計花費", value=f"`💰 {total_cost}`", inline=True)
        embed.set_footer(text=f"來源: {source}")
        await interaction.followup.send(embed=embed)

    # 查看投資組合
    @app_commands.command(name="stock_mine", description="查看投資組合")
    @app_commands.guild_only()
    async def portfolio(self, interaction: discord.Interaction):
        await interaction.response.defer()
        bank = self.bot.get_cog('BankMod')
        if not bank: return await interaction.followup.send("銀行系統異常。")

        bank.users = bank.load_data()
        gid, uid = str(interaction.guild.id), str(interaction.user.id)
        user_data = bank.users.get(gid, {}).get(uid, {})
        user_stocks = user_data.get("stocks", {})
        user_costs = user_data.get("stock_costs", {}) # 取得成本資料

        if not user_stocks:
            return await interaction.followup.send("💡 你目前手頭上沒有任何持股。")

        cache = self.load_stock_cache()
        today = datetime.now().strftime("%Y-%m-%d")
        daily_cache = cache.get(today, {})
        embed = discord.Embed(title=f"📊 {interaction.user.display_name} 的投資組合", color=0x3498db, timestamp=datetime.now())
        total_market_value = 0
        total_investment = 0
        for ticker, amount in user_stocks.items():
            stock_info = daily_cache.get(ticker)
            cost = user_costs.get(ticker, 0) # 該股票總投入成本
            total_investment += cost

            if stock_info:
                current_price = stock_info['price']
                market_value = current_price * amount
                total_market_value += market_value

                # 計算損益
                profit = market_value - cost
                profit_percent = (profit / cost * 100) if cost > 0 else 0

                # 決定符號與圖示
                indicator = "🔺" if profit >= 0 else "🔻"
                profit_text = f"{indicator} `{int(profit):+}` ({profit_percent:+.2f}%)"

                price_text = (
                    f"現價: `{current_price}` | 市值: `💰{int(market_value)}`\n"
                    f"淨收益: **{profit_text}**"
                )
            else:
                price_text = "*請先使用 /stock_search 更新報價以計算損益*"

            embed.add_field(name=f"📌 {ticker} ({amount} 股)", value=price_text, inline=False)

        # 總結算
        total_profit = total_market_value - total_investment
        total_profit_percent = (total_profit / total_investment * 100) if total_investment > 0 else 0
        profit_color = "🟢" if total_profit >= 0 else "🔴"

        summary_val = (
            f"💵 現金餘額: `{user_data.get('coin', 0)}`\n"
            f"🏛️ 持股市值: `{int(total_market_value)}`\n"
            f"📈 總盈虧: {profit_color} **`{int(total_profit):+}`** (`{total_profit_percent:+.2f}%`)"
        )
        embed.add_field(name="💰 資產總結", value=summary_val, inline=False)

        await interaction.followup.send(embed=embed)

    # 賣出股票指令
    @app_commands.command(name="stock_sell", description="賣出股票並結算收益")
    @app_commands.describe(股票代碼="請輸入股票代碼", 數量="請輸入賣出數量")
    @app_commands.guild_only()
    async def sell_stock(self, interaction: discord.Interaction, 股票代碼: str, 數量: int):
        if 數量 <= 0:
            await interaction.response.send_message("賣出數量必須大於 0！", ephemeral=True)
            return

        await interaction.response.defer()
        bank = self.bot.get_cog('BankMod')

        # 1. 取得最新股價
        data, source = await self.get_stock_data(股票代碼.upper())
        if not data:
            await interaction.followup.send(f"❌ 無法取得股票 `{股票代碼}` 的市價，交易取消。")
            return

        ticker = data['ticker']
        gid, uid = str(interaction.guild.id), str(interaction.user.id)

        # 2. 檢查持股
        bank.users = bank.load_data()
        user_data = bank.users.get(gid, {}).get(uid, {})
        user_stocks = user_data.get("stocks", {})

        # --- 核心修正：防禦性初始化 stock_costs ---
        if "stock_costs" not in user_data:
            user_data["stock_costs"] = {}

        current_hold = user_stocks.get(ticker, 0)
        if current_hold < 數量:
            await interaction.followup.send(f"❌ 持股不足！你手上的 `{ticker}` 只有 `{current_hold}` 股。")
            return

        # 3. 計算收益與成本扣除
        sell_price = data['price']
        total_revenue = int(sell_price * 數量)

        # 取得該股票的原始總成本
        original_total_cost = user_data["stock_costs"].get(ticker, 0)

        # 成本扣除額 = (賣出數量 / 總持股) * 總成本
        # 加上 max(1, ...) 避免除以 0 錯誤
        cost_to_remove = int((數量 / max(1, current_hold)) * original_total_cost)

        # 4. 更新資料
        user_data["stocks"][ticker] -= 數量
        user_data["stock_costs"][ticker] = max(0, original_total_cost - cost_to_remove)

        # 如果持股歸零，刪除紀錄
        if user_data["stocks"][ticker] <= 0:
            user_data["stocks"].pop(ticker, None)
            user_data["stock_costs"].pop(ticker, None)

        # 增加金幣並存檔
        bank.add_stats(gid, uid, coin=total_revenue)
        bank.save_data()

        # 5. 回傳結算 (美化面板)
        embed = discord.Embed(title="📉 賣出成交", color=0xe67e22, timestamp=datetime.now())
        embed.add_field(name="股票", value=f"{data['name']} ({ticker})", inline=True)
        embed.add_field(name="賣出數量", value=f"{數量} 股", inline=True)
        embed.add_field(name="成交單價", value=f"{sell_price} {data['currency']}", inline=True)
        embed.add_field(name="獲得金幣", value=f"💰 **{total_revenue}**", inline=False)

        # 計算這筆賣出的預估損益 (參考用)
        estimated_profit = total_revenue - cost_to_remove
        profit_indicator = "🟢" if estimated_profit >= 0 else "🔴"
        embed.add_field(name="本次賣出損益", value=f"{profit_indicator} `{estimated_profit:+}`", inline=True)

        embed.set_footer(text=f"餘額：{user_data['coin']} | 剩餘持股：{user_data['stocks'].get(ticker, 0)}")

        await interaction.followup.send(embed=embed)

    # 只有特定 ID 才能解鎖內容
    @app_commands.command(name="secret", description="丟出一個只有特定人才能解鎖的訊息")
    @app_commands.guild_only()
    async def drop_secret(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SecretModal())

    # 管理員專用：新增/移除授權觀看隱藏Msg
    @app_commands.command(name="manage_secret", description="【Admin】Manage the secret message access list")
    @app_commands.describe(action="add or remove", target="User")
    async def manage_secret(self, interaction: discord.Interaction, action: str, target: discord.Member):
        YOUR_ID = 1170599058717560875  # <--- 請改為你的 ID
        if interaction.user.id != YOUR_ID:
            await interaction.response.send_message("❌ You are not the Admin.", ephemeral=True)
            return

        current_list = load_allowed_users()
        target_id = str(target.id)

        if action.lower() == "add":
            if target_id not in current_list:
                current_list.append(target_id)
                save_allowed_users(current_list)
                await interaction.response.send_message(f"✅ 已將 {target.display_name} 加入授權名單。")
            else:
                await interaction.response.send_message(f"ℹ️ {target.display_name} 已經在名單中了。")

        elif action.lower() == "remove":
            if target_id in current_list:
                current_list.remove(target_id)
                save_allowed_users(current_list)
                await interaction.response.send_message(f"🈲 已將 {target.display_name} 從授權名單移除。")
            else:
                await interaction.response.send_message(f"ℹ️ 名單中找不到 {target.display_name}。")

    # 個人資料指令
    @app_commands.command(name="profile", description="查看你在本伺服器的個人資料與資產概況")
    @app_commands.guild_only()
    async def profile(self, interaction: discord.Interaction):
        await interaction.response.defer() # 因為要計算股票市值，建議先 defer

        gid, uid = str(interaction.guild.id), str(interaction.user.id)

        # 1. 取得銀行資料 (錢、等級、經驗值)
        bank = self.bot.get_cog('BankMod')
        if not bank:
            return await interaction.followup.send("❌ 銀行系統模組未啟動。")

        bank.users = bank.load_data()
        user_data = bank.add_stats(interaction.guild.id, interaction.user.id, coin=0)

        coin = user_data.get("coin", 0)
        exp = user_data.get("exp", 0)

        # 2. 取得股票資料與計算市值
        user_stocks = user_data.get("stocks", {})
        total_stock_value = 0
        cache = self.load_stock_cache()
        today = datetime.now().strftime("%Y-%m-%d")
        daily_cache = cache.get(today, {})

        stock_summary = ""
        if user_stocks:
            for ticker, amount in user_stocks.items():
                info = daily_cache.get(ticker)
                if info:
                    value = info['price'] * amount
                    total_stock_value += value
                stock_summary += f"📈 {ticker}: `{amount}` 股\n"
        else:
            stock_summary = "目前無持股"

        # 3. 製作 Embed 面板
        embed = discord.Embed(
            title=f"{interaction.user.display_name} 的個人檔案",
            color=interaction.user.color, # 自動抓取使用者的身分組顏色
            timestamp=datetime.now()
        )

        # 設定頭像
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        # 基礎資訊
        embed.add_field("經驗值: `{exp}`", inline=True)
        embed.add_field(name="💰 現金餘額", value=f"`{coin}` 金幣", inline=True)

        # 資產資訊
        net_worth = coin + int(total_stock_value)
        embed.add_field(name="🏦 總資產淨值", value=f"**`{net_worth}`** 金幣", inline=False)

        # 股票清單
        embed.add_field(name="📦 股票庫存", value=stock_summary, inline=False)

        embed.set_footer(text=f"{interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

    # 幸運轉盤指令
    @app_commands.command(name="spin", description="花費金幣進行幸運大轉盤 (下注 5000)")
    @app_commands.guild_only()
    async def spin(self, interaction: discord.Interaction):
        bank = self.bot.get_cog('BankMod')
        if not bank: return await interaction.response.send_message("❌ 銀行系統未啟動。")

        # 1. 檢查餘額 (固定每次下注 5000)
        bet = 5000
        user_data = bank.add_stats(interaction.guild.id, interaction.user.id, coin=0)
        if user_data["coin"] < bet:
            return await interaction.response.send_message(f"❌ 你的餘額不足！需要 `{bet}` 金幣。", ephemeral=True)

        # 2. 扣除賭金
        user_data["coin"] -= bet

        # 3. 轉盤邏輯
        items = ["🍎","🍋‍🟩","🍎", "🍋","🍋‍🟩","🍋", "🍇", "💎", "⭐"]
        result = [random.choice(items) for _ in range(3)]
        res_str = " | ".join(result)

        # 判定獎勵
        win_amount = 0
        if result[0] == result[1] == result[2]:
            if result[0] == "💎": win_amount = 100000 # 三個鑽石大獎
            elif result[0] == "⭐": win_amount = 5000
            else: win_amount = 50000
            msg = "🎊 **超級大獎！** 🎊"
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            win_amount = 11000 # 兩兩相同小獎
            msg = "✨ **小獎！** ✨"
        else:
            msg = "💀 **可惜沒中獎，下次加油！**"

        # 4. 發放獎勵
        user_data["coin"] += win_amount
        bank.save_data()

        # 5. 製作結果 Embed
        embed = discord.Embed(title="🎡 NuSo 幸運轉盤", color=0xff8c00)
        embed.add_field(name="🎰 轉盤結果", value=f"```\n[ {res_str} ]\n```", inline=False)
        embed.add_field(name="結果", value=msg, inline=True)
        if win_amount > 0:
            embed.add_field(name="獲得獎金", value=f"💰 `{win_amount}`", inline=True)
        embed.set_footer(text=f"消耗: {bet} | 剩餘餘額: {user_data['coin']}")
        await interaction.response.send_message(embed=embed)

    # 天氣查詢指令
    @app_commands.command(name="weather", description="查詢城市天氣，可點選按鈕查看明天預報")
    @app_commands.describe(city="請輸入城市名稱 (例如: Taipei)")
    async def weather(self, interaction: discord.Interaction, city: str):
        api_key = "b171e1ded37b0ad51a1a33157b263ea9"
        # 必須使用 forecast API
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=zh_tw"

        await interaction.response.defer()

        cwa_map = {
            "Taipei": "63", "New Taipei": "65", "Taoyuan": "68", "Taichung": "66",
            "Tainan": "67", "Kaohsiung": "64", "Keelung": "10017", "Hsinchu": "10018",
            "Miaoli": "10005", "Changhua": "10007", "Nantou": "10008", "Yunlin": "10009",
            "Chiayi": "10010", "Pingtung": "10013", "Yilan": "10002", "Hualien": "10015",
            "Taitung": "10014", "Penghu": "10016", "Kinmen": "09020", "Lienchiang": "09007"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    city_name = data['city']['name']

                    # 決定氣象局跳轉 URL
                    cwa_id = "index"
                    for key, val in cwa_map.items():
                        if key.lower() in city.lower():
                            cwa_id = f"County.html?CID={val}"
                            break
                    cwa_url = f"https://www.cwa.gov.tw/V8/C/W/County/{cwa_id}"

                    # 建立控制面板
                    view = WeatherView(data, city_name, cwa_url)

                    # 預設發送今日 (day_index=0) 的 Embed
                    embed = view.create_weather_embed(0)
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    await interaction.followup.send(f"❌ 找不到城市：`{city}`，請確認英文拼字。", ephemeral=True)

    # 播放音樂
    @app_commands.command(name="play", description="播放 YouTube 音樂")
    @app_commands.describe(search="輸入歌名或網址")
    async def play(self, interaction: discord.Interaction, search: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ 你必須先進入語音頻道！", ephemeral=True)

        await interaction.response.defer()
        guild_id = interaction.guild.id

        # 1. 取得 YouTube 資訊
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(search, download=False)
                if 'entries' in info: info = info['entries'][0]
            except Exception as e:
                return await interaction.followup.send(f"❌ 搜尋失敗: {e}")

        # 2. 初始化清單並排隊
        if guild_id not in self.queues:
            self.queues[guild_id] = []

        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()

        if vc.is_playing() or vc.is_paused():
            # 正在播歌，排進下一首
            self.queues[guild_id].append(info)
            await interaction.followup.send(f"✅ 已加入待播放清單：**{info['title']}** (目前排第 {len(self.queues[guild_id])} 位)")
        else:
            # 沒在播歌，加入清單並啟動播放
            self.queues[guild_id].append(info)
            await self.play_next(interaction, guild_id)
            await interaction.followup.send("🎶 開始播放音樂！", ephemeral=True)
    async def play_next(self, interaction, guild_id):
        if guild_id in self.queues and len(self.queues[guild_id]) > 0:
            info = self.queues[guild_id].pop(0)
            vc = interaction.guild.voice_client
            if not vc: return

            source = await discord.FFmpegOpusAudio.from_probe(info['url'], **FFMPEG_OPTIONS)
            # after 參數會在歌曲結束時自動執行下一首
            vc.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction, guild_id)))

            embed = self.create_music_embed(info, interaction, len(self.queues[guild_id]))
            view = YTMusicView(vc, info, self.queues[guild_id], self)
            await interaction.channel.send(embed=embed, view=view)

    @app_commands.command(name="leave", description="叫機器人離開語音頻道")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("👋 下次見！")
        else:
            await interaction.response.send_message("❌ 我不在語音頻道裡喔。", ephemeral=True)

    # 搶銀行指令
    @app_commands.command(name="rob_bank", description="發起一場大型搶劫行動（主持人確認後開始）")
    @app_commands.guild_only()
    async def rob_bank_cmd(self, interaction: discord.Interaction):
        uid = interaction.user.id
        cost = 10000
        # 1. 檢查玩家是否已在行動中
        if uid in self.active_robbers:
            return await interaction.response.send_message("❌ 你已經在隊伍中或行動中，不能重複發起！", ephemeral=True)

        bank = self.bot.get_cog('BankMod')
        user_data = bank.add_stats(interaction.guild.id, interaction.user.id, coin=0)

        if user_data['coin'] < cost:
            return await interaction.response.send_message(f"❌ 錢不夠支付準備金 {cost}！", ephemeral=True)

        # 2. 將發起人加入鎖定名單
        self.active_robbers.add(uid)

        # 3. 傳入 self (Cog 實例) 給 View，以便 View 操作 active_robbers
        view = RobBankView(interaction, self, cost)
        embed = discord.Embed(
            title="🏦 銀行大劫案：計畫啟動",
            description=(
                f"**發起人：** {interaction.user.mention}\n"
                f"**準備金：** `${cost}`\n\n"
                f"👥 **已加入成員 (1 人)：**\n• {interaction.user.display_name}\n\n"
                f"📋 **主持人確認人數後按「確認開始」按鈕**"
            ),
            color=0x2b2d31
        )
        await interaction.response.send_message(embed=embed, view=view)
    async def start_robbery_logic(self, interaction, participants):
        bank = self.bot.get_cog('BankMod')
        if not bank: return

        gid = interaction.guild.id
        cost = 10000
        fail_fee = 50000
        count = len(participants)

        try:
            # 1. 扣錢
            for p in participants:
                bank.add_stats(gid, p.id, coin=-cost)
            bank.save_data()

            # 2. 開始劇情
            current_content = f"👥 **參與成員：** {', '.join([p.display_name for p in participants])}\n🎬 **行動代號：百萬劫案**"
            try:
                drama_msg = await interaction.channel.send(current_content)
            except discord.Forbidden:
                # 這裡如果發生權限錯誤，也要確保能進到 finally 解鎖，所以用 return 沒關係
                return await interaction.followup.send("⚠️ 機器人缺少在該頻道『傳送訊息』的權限！", ephemeral=True)

            # 3. 跑劇情
            stages = ['prep', 'entry', 'vault_drill', 'vault_open', 'loot', 'police', 'skirmish', 'escape']
            for stage in stages:
                await asyncio.sleep(2.0)
                lucky_guy = random.choice(participants).display_name
                plot_template = random.choice(ROB_PLOTS[stage])
                new_line = f"\n> {plot_template.format(user=lucky_guy)}"
                current_content += new_line
                try:
                    await drama_msg.edit(content=current_content)
                except:
                    break
                if stage in ['vault_drill', 'skirmish']:
                    await asyncio.sleep(1.5)

            # 4. 結算
            success_chance = min(5 + ((count - 1) * 3), 50)
            is_success = random.randint(1, 100) <= success_chance
            await asyncio.sleep(3)

            if is_success:
                total_loot = 1000000 + (count - 1) * 150000
                each_get = total_loot // count
                for p in participants:
                    bank.add_stats(gid, p.id, coin=each_get)

                res_embed = discord.Embed(
                    title="🏆 劫案傳奇：成功撤離！",
                    description=f"你們衝出了包圍網！\n💰 **分贓總額：** `$1,000,000`\n🧧 **每人入帳：** `${each_get:,}`",
                    color=0x2ecc71
                )
                res_embed.set_image(url="https://blog.hamibook.com.tw/wp-content/uploads/2020/01/%E7%B6%93%E7%90%86%E4%BA%BA%E7%89%B9%E5%88%8A%E7%AC%AC30%E6%9C%9Fb01.jpg")
            else:
                for p in participants:
                    bank.add_stats(gid, p.id, coin=-fail_fee)
                res_embed = discord.Embed(
                    title="🚔 灰頭土臉：全軍覆沒！",
                    description=f"醒來時，你們已經在押運車上...\n❌ **每人損失保釋金：** `${fail_fee:,}`",
                    color=0xe74c3c
                )
                res_embed.set_image(url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSM6XWVCnEiOfbARjZn-0lzDo3PkDqSu4gjFA&s")

            bank.save_data()
            p_mentions = ",".join([p.mention for p in participants])
            await interaction.channel.send(content=p_mentions, embed=res_embed)

        except Exception as e:
            # 這是捕捉 Try 區塊內所有可能的意外錯誤
            print(f"🚨 搶劫邏輯發生錯誤: {e}")
            await interaction.channel.send(f"🚨 行動中途發生意外（系統錯誤），計畫被迫中止！")

        finally:
            # 無論成功、失敗或報錯，最後一定會跑這裡解除玩家鎖定
            for p in participants:
                if p.id in self.active_robbers:
                    self.active_robbers.remove(p.id)
            print("🔓 搶案流程結束，已釋放所有參與者狀態。")

    # 存入金庫
    @app_commands.command(name="deposit", description="將身上的現金存入金庫")
    @app_commands.guild_only()
    async def deposit(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ 存入金額必須大於 0！", ephemeral=True)

        # --- 跨模組抓取 BankMod ---
        bank_cog = self.bot.get_cog('BankMod')
        if not bank_cog:
            return await interaction.response.send_message("❌ 系統錯誤：找不到金庫模組！", ephemeral=True)

        # 使用 bank_cog 呼叫功能
        user_data = bank_cog.add_stats(interaction.guild.id, interaction.user.id)

        # 檢查現金
        current_cash = user_data.get("coin", 0)
        if current_cash < amount:
            return await interaction.response.send_message(f"❌ 你手上的現金不足！(目前持有: `${current_cash:,}`)", ephemeral=True)

        # 執行轉帳
        user_data["coin"] -= amount
        user_data["bank_balance"] = user_data.get("bank_balance", 0) + amount

        # 呼叫 bank_cog 的存檔
        bank_cog.save_data()

        embed = discord.Embed(title="🏦 金庫存款成功", color=0x2ecc71)
        embed.add_field(name="💰 存入金額", value=f"`${amount:,}`\n")
        embed.add_field(name="🏧 剩餘現金", value=f"`${user_data['coin']:,}` \n")
        embed.add_field(name="🏛️ 金庫總額", value=f"`${user_data['bank_balance']:,}` \n")
        await interaction.response.send_message(embed=embed)

    # 從銀行提領
    @app_commands.command(name="withdraw", description="從金庫提領現金到身上")
    @app_commands.guild_only()
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ 提領金額必須大於 0！", ephemeral=True)

        # --- 跨模組抓取 BankMod ---
        bank_cog = self.bot.get_cog('BankMod')
        if not bank_cog:
            return await interaction.response.send_message("❌ 系統錯誤：找不到金庫模組！", ephemeral=True)

        user_data = bank_cog.add_stats(interaction.guild.id, interaction.user.id)

        # 檢查存款
        current_bank = user_data.get("bank_balance", 0)
        if current_bank < amount:
            return await interaction.response.send_message(f"❌ 金庫存款不足！(目前存款: `${current_bank:,}`)", ephemeral=True)

        # 執行轉帳
        user_data["bank_balance"] -= amount
        user_data["coin"] += amount

        # 呼叫 bank_cog 的存檔
        bank_cog.save_data()

        embed = discord.Embed(title="💵 現金提領成功", color=0x3498db)
        embed.add_field(name="💰 提領金額", value=f"`${amount:,}`")
        embed.add_field(name="🏧 剩餘存款", value=f"`${user_data['bank_balance']:,}`")
        embed.add_field(name="👜 目前持有現金", value=f"`${user_data['coin']:,}`")
        await interaction.response.send_message(embed=embed)

    # 轉帳
    @app_commands.command(name="transfer", description="轉帳現金給其他玩家 (手續費 3%)")
    @app_commands.describe(user="收錢的對象", amount="要轉的金額")
    @app_commands.guild_only()
    async def transfer(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ 金額必須大於 0", ephemeral=True)
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ 不能轉錢給自己", ephemeral=True)
        if user.bot:
            return await interaction.response.send_message("❌ 不能轉錢給機器人", ephemeral=True)

        bank = self.bot.get_cog('BankMod')
        user_data = bank.add_stats(interaction.guild.id, interaction.user.id)

        # 計算費用
        fee = int(amount * 0.03)
        total_cost = amount + fee

        if user_data["coin"] < total_cost:
            return await interaction.response.send_message(f"❌ 餘額不足！你需要 `${total_cost:,}` (含手續費)，但目前只有 `${user_data['coin']:,}`", ephemeral=True)

        # 製作確認介面 (對應圖片 2)
        embed = discord.Embed(title="💸 確認轉錢", color=0xf39c12) # 橘色邊框
        embed.description = f"您確定要轉錢給 {user.mention} 嗎？\n\n**轉錢詳情**"

        embed.add_field(name="轉帳金額", value=f"`{amount:,}` 💰", inline=False)
        embed.add_field(name="手續費 (3%)", value=f"`{fee:,}` 💰", inline=False)
        embed.add_field(name="您需支付", value=f"`{total_cost:,}` 💰", inline=False)
        embed.add_field(name="對方收到", value=f"`{amount:,}` 💰", inline=False)
        embed.add_field(name="您的當前餘額", value=f"`{user_data['coin']:,}` 💰", inline=False)
        embed.add_field(name="轉帳後餘額", value=f"`{user_data['coin'] - total_cost:,}` 💰", inline=False)

        embed.set_footer(text="請仔細確認轉錢資訊後再操作。")

        view = TransferView(self.bot, interaction.user, user, amount, fee, total_cost, bank)
        await interaction.response.send_message(embed=embed, view=view)

    # 釣魚
    @app_commands.command(name="fish", description="掛機釣魚：漁船等級影響速度，魚竿等級影響品質")
    @app_commands.describe(times="你要釣幾次？(1~500)")
    @app_commands.guild_only()
    async def fish(self, interaction: discord.Interaction, times: int = 1):
        """主流程分流，具體行為分派到獨立方法"""
        uid = interaction.user.id
        now = datetime.now()
        all_fishers = self.get_all_fishers()
        uid_str = str(uid)
        # 狀態分流
        if uid_str in all_fishers:
            status = all_fishers[uid_str]
            end_time = status.get("end_time")
            if isinstance(end_time, str):
                try:
                    end_time = datetime.fromisoformat(end_time)
                except Exception:
                    pass
            if end_time and now >= end_time:
                await self.finish_fishing(interaction, uid_str)
                return
            if end_time and now < end_time:
                await self._send_fishing_embed(interaction, 'progress', {
                    'finish_time': end_time
                })
                return
        if times < 1 or times > 500:
            await interaction.response.send_message("❌ 次數上限為 1~500 次。", ephemeral=True)
            return
        await self._handle_fish_start(interaction, times)
    async def finish_fishing(self, ctx, user_id_str):
        """結算釣魚，顯示 UI、給錢、清除紀錄（可供 /fish 與 on_ready 共用）"""
        all_fishers = self.get_all_fishers()
        data = all_fishers.get(user_id_str)
        if not data:
            return
        # 發錢
        bank = self.bot.get_cog('BankMod')
        if bank:
            try:
                bank.add_stats(data.get("guild_id"), int(user_id_str), coin=data.get("total_reward", 0))
                bank.save_data()
            except Exception as e:
                print(f"⚠️ 結算時寫入銀行失敗: {e}")
        # 刪除紀錄
        self.remove_fisher(user_id_str)
        # 發送 UI
        await self._send_fishing_embed(ctx, 'result', {
            'user_name': data.get('user_name'),
            'user_id': user_id_str,
            'rarity_counts': data.get('rarity_counts', {}),
            'total_reward': data.get('total_reward', 0)
        })
    async def do_fish_settlement(self, interaction_or_ctx, user_id_str):
        """結算釣魚，顯示 UI、給錢、清除紀錄"""
        # 1. 讀取資料
        all_fishers = self.get_all_fishers()
        data = all_fishers.get(user_id_str)
        if not data:
            return  # 無掛機紀錄
        # 2. 隨機決定魚種與金額（根據等級加成）
        boat_lv = data.get("boat_level", 1)
        rod_lv = data.get("rod_level", 1)
        times = data.get("times", 1)
        rarity_counts = data.get("rarity_counts", {})
        total_reward = data.get("total_reward", 0)
        # 3. UI 構建
        summary = "\n".join([f"• {r}: {count}次" for r, count in rarity_counts.items()])
        embed = discord.Embed(title="🎣 釣魚成果報告", color=0x2ecc71)
        display_name = data.get("user_name") or f"<@{user_id_str}>"
        embed.description = f"{display_name} 任務已完成！這是你在這段期間的收穫："
        embed.add_field(name="📊 捕獲統計", value=f"```\n{summary}\n```", inline=False)
        embed.add_field(name="💰 最終收益", value=f"**`${total_reward:,}`**", inline=True)
        # 4. 銀行更新
        bank = self.bot.get_cog('BankMod')
        if bank:
            try:
                bank.add_stats(data.get("guild_id"), int(user_id_str), coin=total_reward)
                bank.save_data()
            except Exception as e:
                print(f"⚠️ 結算時寫入銀行失敗: {e}")
        # 5. 移除紀錄
        self.remove_fisher(user_id_str)
        # 6. 發送 UI
        try:
            # Interaction or Context
            if hasattr(interaction_or_ctx, "response") and not interaction_or_ctx.response.is_done():
                await interaction_or_ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction_or_ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"⚠️ 發送釣魚結算 UI 失敗: {e}")
    async def _handle_fish_start(self, interaction, times):
        """新開始區：出海確認與扣款檢查"""
        bank = self.bot.get_cog('BankMod')
        user_data = bank.add_stats(interaction.guild.id, interaction.user.id)
        boat_lv = user_data.get("boat_level", 1)
        rod_lv = user_data.get("rod_level", 1)
        cost = times * 50
        if user_data.get("coin", 0) < cost:
            await interaction.response.send_message(f"❌ 現金不足！需要 `${cost:,}`。", ephemeral=True)
            return
        per_fish_time = max(0.5, 10.0 - (boat_lv - 1) * 0.5)
        duration = int(times * per_fish_time)
        finish_time = datetime.now() + timedelta(seconds=duration)
        data = {
            'user_mention': interaction.user.mention,
            'boat_lv': boat_lv,
            'rod_lv': rod_lv,
            'per_fish_time': per_fish_time,
            'duration': duration,
            'finish_time': finish_time,
            'cost': cost
        }
        view = FishConfirmView(interaction, self, times, cost, boat_lv, rod_lv, per_fish_time, duration, finish_time)
        embed = self._build_fishing_embed('start', data)
        await interaction.response.send_message(embed=embed, view=view)
    async def execute_fish_start(self, interaction: discord.Interaction, fish_view):
        """確認出海後執行：扣款、計算收益、儲存、啟動計時器"""
        uid = fish_view.uid
        times = fish_view.times
        cost = fish_view.cost
        boat_lv = fish_view.boat_lv
        rod_lv = fish_view.rod_lv
        duration = fish_view.duration
        finish_time = fish_view.finish_time

        bank = self.bot.get_cog('BankMod')
        user_data = bank.add_stats(interaction.guild.id, uid, coin=0)
        if user_data.get("coin", 0) < cost:
            return await interaction.response.send_message("❌ 餘額不足，請重新下指令。", ephemeral=True)

        user_data["coin"] -= cost
        bank.save_data()

        bonus = rod_lv - 1
        adj_weights = []
        for f in self.FISH_POOL:
            w = f["chance"]
            r = f["rarity"]
            if r == "傳說": w += bonus * 1
            elif r == "史詩": w += bonus * 1
            elif r == "稀有": w += int(bonus * 0.5)
            elif r == "垃圾": w = max(5, w - int(bonus * 1.3))
            elif r == "災難": w = max(1, w - int(bonus * 0.5))
            else: w = max(10, w - int(bonus * 0.8))
            adj_weights.append(w)

        total_reward = 0
        rarity_counts = {}
        for _ in range(times):
            fish_obj = random.choices(self.FISH_POOL, weights=adj_weights, k=1)[0]
            price = fish_obj["price"]
            if price > 0:
                price = int(price * (1 + (rod_lv - 1) * 0.1))
            total_reward += price
            r = fish_obj["rarity"]
            rarity_counts[r] = rarity_counts.get(r, 0) + 1

        # 記錄掛機資訊（包含 start_time, 裝備等）
        fisher_data = {
            "start_time": datetime.now(),
            "end_time": finish_time,
            "total_reward": total_reward,
            "times": times,
            "rarity_counts": rarity_counts,
            "guild_id": interaction.guild.id,
            "channel_id": interaction.channel.id,
            "boat_level": boat_lv,
            "rod_level": rod_lv,
            "user_name": interaction.user.display_name
        }
        self.update_fisher(uid, fisher_data)

        mm, ss = divmod(duration, 60)
        time_str = f"{mm}分{ss}秒" if mm > 0 else f"{ss}秒"

        for item in fish_view.children:
            item.disabled = True
        embed = discord.Embed(title="🚢 漁船已出海", color=0x2ecc71)
        embed.description = (
            f"👤 **釣客：** <@{uid}>\n"
            f"🚤 **漁船等級：** `Lv.{boat_lv}`\n"
            f"⏱️ **作業速度：** `{fish_view.per_fish_time:.1f}s` / 竿\n"
            f"⏳ **總計耗時：** `約 {time_str}`\n"
            f"🔔 **回港時間：** `{finish_time.strftime('%H:%M:%S')}`"
        )
        await interaction.response.edit_message(embed=embed, view=fish_view)
    async def background_fish_finisher(self, interaction, uid, duration):
        await asyncio.sleep(duration)

        all_fishers = self.get_all_fishers()
        if str(uid) in all_fishers:
            bank = self.bot.get_cog('BankMod')
            if not bank:
                return
            data = all_fishers[str(uid)]
            try:
                bank.add_stats(data.get("guild_id"), uid, coin=data.get("total_reward", 0))
                bank.save_data()
            except Exception as e:
                print(f"⚠️ background finisher 存入獎金失敗: {e}")
            try:
                self.remove_fisher(str(uid))
            except Exception:
                pass

            # 整理統計報告
            summary = "\n".join([f"• {r}: {count}次" for r, count in data["rarity_counts"].items()])

            embed = discord.Embed(title="🏁 漁船回港結算", color=0xf1c40f)
            # 如果你有圖片可以加上，沒有的話可以刪掉下一行
            # embed.set_thumbnail(url="https://i.imgur.com/your_fishing_image.png")
            embed.description = f"<@{uid}> 你的船隊已滿載而歸！"
            embed.add_field(name="📊 捕獲統計", value=f"```\n{summary}\n```", inline=False)
            embed.add_field(name="💰 最終收益", value=f"**`${data.get('total_reward',0):,}`**", inline=True)

            # 建立再次拋竿按鈕（若要）
            view = FishingView(interaction, self)

            sent = False
            try:
                channel = self.bot.get_channel(data.get("channel_id"))
                if channel:
                    try:
                        thread_name = f"{data.get('user_name','玩家')} 的釣魚成果"
                        thread = await channel.create_thread(name=thread_name)
                        await thread.send(embed=embed, view=view)
                        sent = True
                    except Exception:
                        await channel.send(embed=embed, view=view)
                        sent = True
            except Exception:
                sent = False

            if not sent:
                try:
                    user = self.bot.get_user(uid)
                    if user:
                        await user.send(embed=embed)
                        sent = True
                except Exception:
                    pass

    @app_commands.command(name="fish_shop", description="查看與升級你的釣魚設備")
    @app_commands.guild_only()
    async def fish_shop(self, interaction: discord.Interaction):
        bank = self.bot.get_cog('BankMod')
        user_data = bank.add_stats(interaction.guild.id, interaction.user.id)

        boat_lv = user_data.get("boat_level", 1)
        rod_lv = user_data.get("rod_level", 1)

        current_boat_speed = max(0.5, 10.0 - (boat_lv - 1) * 0.5)
        next_boat_speed = max(0.5, 10.0 - (boat_lv) * 0.5)
        current_rod_bonus = (rod_lv - 1) * 10
        next_rod_bonus = rod_lv * 10

        boat_upgrade_cost = boat_lv * 1000000
        rod_upgrade_cost = rod_lv * 1000000

        embed = discord.Embed(
            title="🛠️ 漁具整備中心 (Max Lv.20)",
            description=f"歡迎回來，{interaction.user.mention}！目前最高等級已開放至 20 等。",
            color=0x3498db
        )

        boat_text = f"**等級：** `Lv.{boat_lv}/20`\n**目前速度：** `{current_boat_speed:.1f}s` / 竿\n"
        if boat_lv < 20:
            boat_text += f"**下一級：** `{next_boat_speed:.1f}s` (費用: `${boat_upgrade_cost:,}`)"
        else:
            boat_text += "**狀態：** 已達到頂級 ✨"
        embed.add_field(name="🚤 工業級漁船", value=boat_text, inline=False)

        rod_text = f"**等級：** `Lv.{rod_lv}/20`\n**價值加成：** `+{current_rod_bonus}%` 收益\n"
        if rod_lv < 20:
            rod_text += f"**下一級：** `+{next_rod_bonus}%` (費用: `${rod_upgrade_cost:,}`)"
        else:
            rod_text += "**狀態：** 已達到頂級 ✨"
        embed.add_field(name="🎣 鈦合金魚竿", value=rod_text, inline=False)

        embed.set_footer(text="使用 /upgrade <項目> 進行升級")
        embed.set_author(name="NuSo 系統核心", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="upgrade", description="升級設備：漁船或魚竿")
    @app_commands.choices(item=[
        app_commands.Choice(name="🚤 漁船 (速度)", value="boat"),
        app_commands.Choice(name="🎣 魚竿 (品質)", value="rod")
    ])
    @app_commands.guild_only()
    async def upgrade(self, interaction: discord.Interaction, item: str):
        bank = self.bot.get_cog('BankMod')
        user_data = bank.add_stats(interaction.guild.id, interaction.user.id)

        is_boat = (item == "boat")
        current_lv = user_data.get("boat_level", 1) if is_boat else user_data.get("rod_level", 1)
        item_name = "🚤 漁船" if is_boat else "🎣 魚竿"

        if current_lv >= 20:
            return await interaction.response.send_message(f"❌ 你的 {item_name} 已達最高等級 (Lv.20)！", ephemeral=True)

        cost = current_lv * 1000000
        if user_data.get("coin", 0) < cost:
            return await interaction.response.send_message(f"❌ 錢不夠！升級需要 `${cost:,}`", ephemeral=True)

        user_data["coin"] -= cost
        if is_boat:
            user_data["boat_level"] = current_lv + 1
        else:
            user_data["rod_level"] = current_lv + 1
        bank.save_data()

        embed = discord.Embed(
            title="🔨 設備升級成功 / Equipment Upgraded",
            description=f"你已成功將 **{item_name}** 提升至 **Lv.{current_lv + 1}**",
            color=0xff0000 # 紅色邊框
        )
        embed.add_field(name="消耗金額", value=f"`${cost:,}`", inline=True)
        embed.add_field(name="目前餘額", value=f"`${user_data['coin']:,}`", inline=True)

        if is_boat:
            eff = f"作業速度提升至：`{max(0.5, 10.0 - (current_lv) * 0.5):.1f}s` / 竿"
        else:
            eff = f"漁獲價值加成提升至：`+{current_lv * 10}%`"
        embed.add_field(name="✨ 強化效果", value=eff, inline=False)

        embed.set_author(name="NuSo 系統核心", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text="From system")
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dragongate", description="玩一局刺激的射龍門！")
    @app_commands.describe(bet="你要下注的金額")
    async def dragongate(self, interaction: discord.Interaction, bet: int):
        if not self.bank or not hasattr(self.bank, 'add_stats'):
            self.bank = self._find_bank_cog()
        if bet < 100:
            return await interaction.response.send_message("❌ 最低下注金額為 $100！", ephemeral=True)

        #獲取資料 (傳入 coin=0)
        user_data = self.bank.add_stats(interaction.guild.id, interaction.user.id, coin=0)

        # 2. 檢查餘額
        if user_data['coin'] < bet:
            return await interaction.response.send_message(f"❌ 錢不夠！你目前只有 ${user_data['coin']}。", ephemeral=True)

        #  開始時先扣錢
        self.bank.add_stats(interaction.guild.id, interaction.user.id, coin=-bet)
        self.bank.save_data()

        # 準備遊戲
        suits = ["♠️", "♥️", "♦️", "♣️"]
        deck = [(s, v) for s in suits for v in range(1, 14)]
        random.shuffle(deck)

        # 這裡的 user_data 已經是最新扣完錢的狀態了
        view = DragonGateView(interaction, user_data, bet, deck, self, self.bank)

        embed = discord.Embed(title="🐉 射龍門 (Shoot the Dragon Gate)", color=0xf1c40f)
        embed.add_field(name="⚖️ 目前門柱", value=f"{view.card_to_str(view.gate[0])}  ↔️  {view.card_to_str(view.gate[1])}", inline=False)
        embed.add_field(name="💰 下注金額", value=f"`${bet:,}` (已扣除)", inline=True)
        embed.set_footer(text="提示：撞柱賠兩倍！")

        await interaction.response.send_message(embed=embed, view=view)

    # --- 終端監聽與控制功能 ---
    def console_listener(self):
        """在獨立線程中監聽終端輸入"""
        print("\n" + "═"*30)
        print(" NuSo 核心終端已啟動")
        print(" 輸入 'help' 展開權限指令清單")
        print("═"*30 + "\n")

        while True:
            try:
                line = input("").strip().split()
                if not line: continue
                cmd = line[0].lower()
                args = line[1:]

                # 1. 幫助清單
                if cmd == "help":
                    print("\n" + "═"*25 + " 終端指令表 " + "═"*25)
                    print("【一、伺服器核心 (Server)】")
                    print(f"  {'rename [名稱]':<23} | 變更伺服器名稱")
                    print(f"  {'security [0-4]':<25} | 調整驗證門檻 (0-4)")
                    print(f"  {'audit':<25} | 顯示最新 20 筆審核日誌")
                    print("\n【二、成員與身分組 (Members)】")
                    print(f"  {'kick [ID]':<25} | 驅逐成員")
                    print(f"  {'ban [ID] [天數]':<23} | 封鎖並刪除訊息 (0-7天)")
                    print(f"  {'add-admin [MID] [RID]':<25} | 🔴 賦予管理員身分組")
                    print(f"  {'rm-admin [MID] [RID]':<25} | 🔴 移除身分組權限")
                    print(f"  {'mute [ID] [分鐘]':<23} | 強制禁言 (Timeout)")
                    print(f"  {'nick [ID] [新名字]':<22} | 修改他人暱稱")
                    print("\n【三、頻道與內容 (Channels)】")
                    print(f"  {'rm-chan [ID]':<25} | 刪除頻道/類別")
                    print(f"  {'purge [ID] [量]':<24} | 批量刪除訊息")
                    print("\n【四、語音與視訊 (Voice)】")
                    print(f"  {'vckick [ID]':<25} | 強制斷開語音 (Disconnect)")
                    print(f"  {'vcmove [ID] [CID]':<25} | 強行拖拽至頻道 CID")
                    print(f"  {'vcmute [ID] [1/0]':<25} | 伺服器靜音 (1=開, 0=關)")
                    print(f"  {'vcdeaf [ID] [1/0]':<25} | 伺服器拒聽 (1=開, 0=關)")
                    print("\n【五、遊戲後台控制 (Game Control)】")
                    print(f"  {'bj [名稱] [w/l/p]':<23} | 21點控制 (w必贏/l必輸/p清除)")
                    print("\n【系 統】")
                    print(f"  {'ann:ID:msg':<25} | 發送系統公告 (舊格式)")
                    print(f"  {'r / cls / exit':<25} | 重載 / 清理 / 關閉")
                    print("═"*70 + "\n")

                # 2. 核心邏輯處理
                elif cmd == "rename":
                    asyncio.run_coroutine_threadsafe(self.bot.get_guild(self.GUILD_ID).edit(name=" ".join(args)), self.bot.loop)
                    print(f"✅ 伺服器已更名為: {' '.join(args)}")

                elif cmd == "audit":
                    # 🔍 顯示最新 20 筆審核日誌
                    guild = self.bot.get_guild(self.GUILD_ID)
                    print(f"\n--- 📡 伺服器最新審核日誌 ({guild.name}) ---")
                    # 使用 async for 迭代審核日誌
                    async def fetch_audit():
                        async for entry in guild.audit_logs(limit=20):
                            time = entry.created_at.strftime("%H:%M:%S")
                            print(f"[{time}] {entry.user.name} -> {entry.action.name} (對象: {entry.target})")
                    asyncio.run_coroutine_threadsafe(fetch_audit(), self.bot.loop)

                elif cmd == "security":
                    # 調整驗證等級 (0-4)
                    level = getattr(discord.VerificationLevel, ['none', 'low', 'medium', 'high', 'highest'][int(args[0])])
                    asyncio.run_coroutine_threadsafe(self.bot.get_guild(self.GUILD_ID).edit(verification_level=level), self.bot.loop)
                    print(f"✅ 驗證等級已調至: {level}")

                elif cmd == "add-admin":
                    guild = self.bot.get_guild(self.GUILD_ID)
                    member = guild.get_member(int(args[0])) # 第一個參數是成員 ID
                    role = guild.get_role(int(args[1]))     # 第二個參數是身分組 ID

                    if member and role:
                        asyncio.run_coroutine_threadsafe(member.add_roles(role), self.bot.loop)
                        print(f"✅ [身分組支配]：已將 {role.name} 賦予給 {member.display_name}")
                    else:
                        print("❌ 錯誤：找不到成員或身分組，請檢查 ID 是否正確。")

                elif cmd == "rm-admin":
                    guild = self.bot.get_guild(self.GUILD_ID)
                    member = guild.get_member(int(args[0]))
                    role = guild.get_role(int(args[1]))
                    if member and role:
                        asyncio.run_coroutine_threadsafe(member.remove_roles(role), self.bot.loop)
                        print(f"✅ [身分組支配]：已從 {member.display_name} 身上剝奪 {role.name}")
                    else:
                        print("❌ 錯誤：操作失敗，請確認 ID。")

                elif cmd == "kick":
                    guild = self.bot.get_guild(self.GUILD_ID)
                    m = guild.get_member(int(args[0]))
                    asyncio.run_coroutine_threadsafe(m.kick(reason="支配者指令"), self.bot.loop)
                    print(f"✅ 已驅逐: {m.display_name}")

                elif cmd == "ban":
                    # ban [ID] [天數]
                    guild = self.bot.get_guild(self.GUILD_ID)
                    m = guild.get_member(int(args[0]))
                    days = int(args[1]) if len(args) > 1 else 0
                    asyncio.run_coroutine_threadsafe(m.ban(delete_message_days=days, reason="支配者裁決"), self.bot.loop)
                    print(f"🔨 已封鎖 {m.display_name} (清理 {days} 天訊息)")

                elif cmd == "mute":
                    guild = self.bot.get_guild(self.GUILD_ID)
                    m = guild.get_member(int(args[0]))
                    time_min = int(args[1])
                    asyncio.run_coroutine_threadsafe(m.timeout(timedelta(minutes=time_min)), self.bot.loop)
                    print(f"✅ 已禁言 {m.display_name} {time_min} 分鐘")

                elif cmd == "nick":
                    # nick [ID] [新名字]
                    guild = self.bot.get_guild(self.GUILD_ID)
                    m = guild.get_member(int(args[0]))
                    new_name = " ".join(args[1:])
                    asyncio.run_coroutine_threadsafe(m.edit(nick=new_name), self.bot.loop)
                    print(f"📝 已將 {m.name} 改名為: {new_name}")

                elif cmd == "rm-chan":
                    # rm-chan [ID]
                    chan = self.bot.get_channel(int(args[0]))
                    if chan:
                        asyncio.run_coroutine_threadsafe(chan.delete(), self.bot.loop)
                        print(f"🗑️ 已刪除頻道: {chan.name}")

                elif cmd == "purge":
                    # purge [頻道ID] [量]
                    chan = self.bot.get_channel(int(args[0]))
                    limit = int(args[1])
                    asyncio.run_coroutine_threadsafe(chan.purge(limit=limit), self.bot.loop)
                    print(f"🧹 已在 {chan.name} 刪除 {limit} 條訊息")

                elif cmd == "vcmove":
                    # vcmove [成員ID] [目標頻道ID]
                    guild = self.bot.get_guild(self.GUILD_ID)
                    m = guild.get_member(int(args[0]))
                    chan = self.bot.get_channel(int(args[1]))
                    asyncio.run_coroutine_threadsafe(m.move_to(chan), self.bot.loop)
                    print(f"🏃 已強行拖移 {m.display_name} 至 {chan.name}")

                elif cmd == "vcdeaf":
                    # vcdeaf [成員ID] [1=開, 0=關]
                    guild = self.bot.get_guild(self.GUILD_ID)
                    m = guild.get_member(int(args[0]))
                    status = True if args[1] == "1" else False
                    asyncio.run_coroutine_threadsafe(m.edit(deafen=status), self.bot.loop)
                    print(f"🔇 伺服器拒聽狀態: {status}")

                elif cmd == "vckick":
                    guild = self.bot.get_guild(self.GUILD_ID)
                    m = guild.get_member(int(args[0]))
                    if m and m.voice:
                        asyncio.run_coroutine_threadsafe(m.move_to(None), self.bot.loop)
                        print(f"✅ 已斷開語音連線: {m.display_name}")

                elif cmd == "vcmute":
                    guild = self.bot.get_guild(self.GUILD_ID)
                    m = guild.get_member(int(args[0]))
                    status = True if args[1] == "1" else False
                    asyncio.run_coroutine_threadsafe(m.edit(mute=status), self.bot.loop)
                    print(f"✅ 伺服器靜音狀態已設為: {status}")

                elif cmd == "bj":
                    # bj <display_name> <w|l|p>
                    asyncio.run_coroutine_threadsafe(self.process_bj_control(" ".join(args)), self.bot.loop)

                elif cmd == "r":
                    asyncio.run_coroutine_threadsafe(self.reload_all_extensions(), self.bot.loop)

                elif cmd == "cls":
                    os.system('cls' if os.name == 'nt' else 'clear')

                elif cmd == "exit":
                    os._exit(0)

                elif cmd == "tts":
                    # 格式: tts [要說的話]
                    if not args:
                        print("❌ 請輸入文字。用法: tts 內容")
                        continue

                    speech_text = " ".join(args)

                    async def run_tts():
                        guild = self.bot.get_guild(self.GUILD_ID)
                        if not guild:
                            print("❌ 找不到伺服器。")
                            return

                        # 🔊 自動邏輯：找一個目前有人的語音頻道
                        target_chan = next((c for c in guild.voice_channels if len(c.members) > 0), None)

                        if not target_chan:
                            print("❌ 目前語音頻道沒人，機器人不知道要去哪裡說話。")
                            return

                        # 轉換語音
                        tts_file = "console_tts.mp3"
                        communicate = edge_tts.Communicate(
                        speech_text,
                            "zh-TW-HsiaoChenNeural",
                            rate="+25%",
                            pitch="+10Hz"
                        )
                        await communicate.save(tts_file)

                        # 連接並播放
                        vc = guild.voice_client
                        if not vc:
                            vc = await target_chan.connect()
                        elif vc.channel.id != target_chan.id:
                            await vc.move_to(target_chan)

                        if vc.is_playing():
                            vc.stop()

                        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=tts_file))
                        print(f"🎙️ [後台發言] 已在 {target_chan.name} 播放: {speech_text}")

                    # 丟回主執行緒執行
                    asyncio.run_coroutine_threadsafe(run_tts(), self.bot.loop)

                elif cmd == "play":
                    print(f"DEBUG: 收到 play 指令，路徑: {args}") # 確認有沒有進來
                    if not args:
                        print("❌ 請提供檔案路徑！")
                        continue
                    file_path = args[0]
                    if not os.path.exists(file_path):
                        print(f"❌ 找不到檔案: {file_path}")
                        continue

                    guild = self.bot.get_guild(self.GUILD_ID)
                    print(f"DEBUG: 抓取的伺服器名稱: {guild.name if guild else 'None'}")

                    async def auto_play():
                        try:
                            # 尋找有人的頻道
                            target_chan = next((c for c in guild.voice_channels if len(c.members) > 0), None)
                            if not target_chan:
                                print("❌ 錯誤：伺服器裡目前沒有人在語音頻道！請你自己先進去一個頻道。")
                                return
                            print(f"DEBUG: 準備連接頻道: {target_chan.name}")
                            vc = guild.voice_client or await target_chan.connect()
                            if vc.is_playing(): vc.stop()
                            print(f"DEBUG: 開始執行 FFmpeg...")
                            source = discord.FFmpegPCMAudio(executable="ffmpeg", source=file_path)
                            vc.play(source)
                            print(f"🎵 成功！正在 [{target_chan.name}] 播放: {file_path}")
                        except Exception as e:
                            print(f"❌ 播放內部出錯: {e}")

                    asyncio.run_coroutine_threadsafe(auto_play(), self.bot.loop)

                elif ":" in "".join(line):
                    raw_cmd = "".join(line)
                    parts = raw_cmd.split(":", 2)
                    if len(parts) == 3:
                        asyncio.run_coroutine_threadsafe(
                            self.send_controlled_message(parts[0], parts[1], parts[2]), self.bot.loop
                        )

                # --- 終端機專用播放指令 ---
            except Exception as e:
                print(f"❌ 執行錯誤: {e}")

    # --- 整合發送與重載函式 ---
    async def send_controlled_message(self, mode, target_id, content):
        try:
            target = self.bot.get_channel(int(target_id))
            if mode == "ann":
                embed = discord.Embed(description=f"# 📢 系統公告\n\n{content}", color=0xff0000)
                embed.set_author(name="NuSo 系統核心", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
                embed.timestamp = datetime.now()
                await target.send(embed=embed)
            else:
                await target.send(content)
            print(f"✅ 訊息已發送至 {target_id}")
        except Exception as e:
            print(f"❌ 發送失敗: {e}")

    async def reload_all_extensions(self):
        for ext in ['mod.bank', 'mod.Mod']:
            try:
                await self.bot.reload_extension(ext)
            except:
                pass
        await self.bot.tree.sync(guild=discord.Object(id=self.GUILD_ID))
        print("✅ 所有模組已重載並同步完成")

async def setup(bot):
    # 這裡檢查 bot 是否有 ai_func 屬性，如果沒有則傳入 None
    ai_func = getattr(bot, "ai_func", None)
    await bot.add_cog(MyCommands(bot, ai_func))
