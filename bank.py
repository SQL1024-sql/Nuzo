import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from datetime import datetime

class BankMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 1. 取得路徑邏輯保持不變
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        self.data_file = os.path.join(root_dir, "user_stats.json")

        self.users = self.load_data()
        self.save_data()

        print(f"✅ 銀行系統已啟動 存檔路徑：{self.data_file}")

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=4, ensure_ascii=False)

    # 封裝增加金幣與經驗的邏輯，方便跨模組呼叫
    def add_stats(self, guild_id, user_id, coin=0, exp=0):
        gid = str(guild_id)
        uid = str(user_id)

        # 初始化伺服器層
        if gid not in self.users:
            self.users[gid] = {}
        # 初始化使用者層
        if uid not in self.users[gid]:
            self.users[gid][uid] = {
                "coin": 10000,
                "exp": 0,
                "stocks": {},
                "bank_balance": 0,
                "loan": 0,
                "boat_level": 1,
                "rod_level": 1
            }
        if "boat_level" not in self.users[gid][uid]: self.users[gid][uid]["boat_level"] = 1
        if "rod_level" not in self.users[gid][uid]: self.users[gid][uid]["rod_level"] = 1
        if "stocks" not in self.users[gid][uid]:
            self.users[gid][uid]["stocks"] = {}
        if "loan" not in self.users[gid][uid]:
            self.users[gid][uid]["loan"] = 0
        self.users[gid][uid]["coin"] += coin
        self.users[gid][uid]["exp"] += exp
        return self.users[gid][uid]


    # --- leaderboard 指令：查看伺服器內的財富排行榜 ---
    @app_commands.command(name="leaderboard", description="查看此伺服器的前 5 名富豪 (總資產排序)")
    @app_commands.guild_only()
    async def leaderboard(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid not in self.users or not self.users[gid]:
            await interaction.response.send_message("本伺服器目前還沒有人有錢喔！", ephemeral=True)
            return
        server_users = self.users[gid]
        # 1. 核心排序邏輯修改：將現金 (coin) 與 金庫 (bank_balance) 相加進行排序
        # 使用 .get(..., 0) 防止 KeyError
        sorted_users = sorted(
            server_users.items(),
            key=lambda x: x[1].get('coin', 0) + x[1].get('bank_balance', 0),
            reverse=True
        )[:5]

        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} 財富排行榜",
            description="統計包含 **手持現金** 與 **金庫存款**",
            color=0xFFD700
        )

        for i, (uid, data) in enumerate(sorted_users, 1):
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"神秘人({uid})"
            # 取得各項數值
            cash = data.get('coin', 0)
            bank_amt = data.get('bank_balance', 0)
            total = cash + bank_amt

            # 格式化顯示：顯示總額，並在括號內標註現金與存款
            embed.add_field(
                name=f"{i}. {name}",
                value=f"💎 **總資產：`${total:,}`**\n └ 💵 現金：`${cash:,}`\n └ 🏦 金庫：`${bank_amt:,}`",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    # --- balance 指令：查看個人餘額 ---
    @app_commands.command(name="balance", description="查詢餘額")
    async def balance(self, interaction: discord.Interaction):
        user_data = self.add_stats(interaction.guild.id, interaction.user.id)

        # 使用 .get(key, default) 確保找不到欄位時不會報錯，而是顯示 0
        cash = user_data.get('coin', 0)
        bank = user_data.get('bank_balance', 0)
        loan = user_data.get('loan', 0)
        embed = discord.Embed(title="💰 帳戶餘額查詢", color=0xf1c40f)
        embed.add_field(name="💵 持有現金", value=f"`${cash:,}`", inline=False)
        embed.add_field(name="🏦 金庫存款", value=f"`${bank:,}`", inline=False)
        embed.add_field(name="🏧 債務金額", value=f"`${loan:,}`", inline=False)
        embed.set_footer(text=f"查詢對象：{interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add_coins", description="[管理員] 增加金幣")
    @app_commands.describe(member="要加錢的對象", amount="金幣數量")
    @app_commands.guild_only()
    async def add_coins(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        # --- 權限檢查：將 "你的ID" 替換成你真正的 Discord ID ---
        YOUR_ID = [1170599058717560875, 665170783181733898, 1449416191272816650]  # 請在此處輸入你的數位 ID
        if interaction.user.id not in YOUR_ID:
            await interaction.response.send_message("❌ 權限不足：只有指定人員可以執行此操作。", ephemeral=True)
            return

        # 執行加錢邏輯
        gid = str(interaction.guild.id)
        uid = str(member.id) # 使用目標成員的 ID
        # 重新讀取確保資料即時
        self.users = self.load_data()
        user_data = self.add_stats(interaction.guild.id, member.id, coin=amount)
        self.save_data()
        await interaction.response.send_message(
            f"✅ 已成功為 {member.mention} 增加 `{amount}` 金幣。\n該使用者目前餘額：`{user_data['coin']}`"
        )

    # daily 指令：每日簽到
    @app_commands.command(name="daily", description="每日簽到")
    @app_commands.guild_only()
    async def daily(self, interaction: discord.Interaction):
        # 1. 強制讀取最新 JSON，防止手動修改檔案後資料不同步
        self.users = self.load_data()

        gid = str(interaction.guild.id)
        uid = str(interaction.user.id)
        today = datetime.now().strftime("%Y-%m-%d")

        # 2. 確保使用者資料初始化 (這會回傳 self.users[gid][uid] 的引用)
        user_data = self.add_stats(interaction.guild.id, interaction.user.id, coin=0)
        # 3. 檢查日期
        last_checkin = user_data.get("last_checkin", "")
        if last_checkin == today:
            await interaction.response.send_message(f"❌ {interaction.user.display_name}，你今天已經領過囉！", ephemeral=True)
            return

        # 4. 發放獎勵
        reward = 10000
        user_data["coin"] += reward
        user_data["last_checkin"] = today
        # 5. 儲存回 JSON
        self.save_data()

        embed = discord.Embed(
            title="📅 每日簽到成功",
            description=f"{interaction.user.mention} 獲得了 **{reward}** 金幣！",
            color=0x2ecc71
        )
        embed.add_field(name="💰 目前餘額", value=f"`{user_data['coin']}`", inline=True)
        embed.set_footer(text=f"伺服器：{interaction.guild.name} | 日期：{today}")

        await interaction.response.send_message(embed=embed)

    # hourly 指令：每小時領取零用錢
    @app_commands.command(name="hourly", description="每小時領取一次零用錢 (整點重置)")
    @app_commands.guild_only()
    async def hourly(self, interaction: discord.Interaction):
        self.users = self.load_data()

        # 1. 取得目前整點
        now = datetime.now()
        current_hour_slot = now.replace(minute=0, second=0, microsecond=0)
        current_hour_ts = int(current_hour_slot.timestamp())

        user_data = self.add_stats(interaction.guild.id, interaction.user.id, coin=0)
        last_hourly_slot = user_data.get("last_hourly_slot", 0)

        # 2. 判斷是否領過
        if last_hourly_slot == current_hour_ts:
            # 計算下個整點的時間戳記 (當前整點 + 3600 秒)
            next_hour_ts = current_hour_ts + 3600
            # 使用 Discord 的 t (Short Time) 或 R (Relative Time) 格式
            # 注意：這裡不可以加任何 ` 符號，否則會變成純文字
            await interaction.response.send_message(
                f"❌ 這小時領過囉！請在 <t:{next_hour_ts}:t> (約 <t:{next_hour_ts}:R>) 再來。",
                ephemeral=True
            )
            return

        # 3. 發放獎勵
        reward = 5000
        user_data["coin"] += reward
        user_data["last_hourly_slot"] = current_hour_ts
        self.save_data()

        # 下次領取時間顯示
        next_ts = current_hour_ts + 3600
        embed = discord.Embed(
            title="⏰ 整點簽到成功",
            description=f"{interaction.user.mention} 領到了 **{reward}** 金幣！\n"
                        f"餘額：{user_data['coin']} 金幣\n"
                        f"下次開放領取時間：<t:{next_ts}:t>",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="borrow", description="向銀行貸款 (最高上限 $200,000)")
    @app_commands.guild_only()
    async def borrow(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ 貸款金額必須大於 0！", ephemeral=True)

        user_data = self.add_stats(interaction.guild.id, interaction.user.id)
        current_loan = user_data.get("loan", 0)
        max_limit = 200000

        # 1. 檢查是否已經有欠款
        if current_loan > 0:
            return await interaction.response.send_message(
                f"❌ 你還有未清償的債務 `${current_loan:,}`。請先還款後再借貸！",
                ephemeral=True
            )

        # 2. 檢查是否超過固定上限 20 萬
        if amount > max_limit:
            return await interaction.response.send_message(
                f"❌ 信用額度不足！最高貸款上限為 `${max_limit:,}`。",
                ephemeral=True
            )

        # 3. 撥款邏輯
        user_data["loan"] = amount
        user_data["coin"] += amount # 貸款直接給現金
        self.save_data()

        embed = discord.Embed(title="🏦 銀行貸款批准", color=0xe67e22)
        embed.description = (
            f"✅ 已成功撥款 `${amount:,}` 至你的錢包。\n\n"
            f"💰 目前持有現金：`${user_data['coin']:,}`\n"
            f"🧾 待償還債務：`${user_data['loan']:,}`"
        )
        embed.set_footer(text="提示：你可以使用 /repay 進行還款")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="repay", description="償還銀行貸款")
    @app_commands.guild_only()
    async def repay(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ 還款金額必須大於 0！", ephemeral=True)

        user_data = self.add_stats(interaction.guild.id, interaction.user.id)
        current_loan = user_data.get("loan", 0)

        if current_loan <= 0:
            return await interaction.response.send_message("✅ 你目前沒有任何債務，不需要還款！", ephemeral=True)

        # 檢查身上現金是否夠還
        if user_data["coin"] < amount:
            return await interaction.response.send_message(
                f"❌ 你身上的現金不足！目前持有：`${user_data['coin']:,}`",
                ephemeral=True
            )

        # 計算實際還款額 (不能還超過欠的錢)
        actual_repay = min(amount, current_loan)

        user_data["coin"] -= actual_repay
        user_data["loan"] -= actual_repay
        self.save_data()

        embed = discord.Embed(title="🧾 還款證明", color=0x2ecc71)
        embed.description = (
            f"✅ 你已償還 `${actual_repay:,}`。\n\n"
            f"📉 剩餘債務：`${user_data['loan']:,}`\n"
            f"👜 剩餘現金：`${user_data['coin']:,}`"
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BankMod(bot))