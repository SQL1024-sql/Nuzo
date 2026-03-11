import asyncio
from datetime import datetime

import discord
import pyaudio


class FishingView(discord.ui.View):
    def __init__(self, interaction, cog_instance):
        super().__init__(timeout=None)
        self.cog = cog_instance
        self.uid = str(interaction.user.id)


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


class FishActiveView(discord.ui.View):
    def __init__(self, cog_instance, user_id):
        super().__init__(timeout=None)
        self.cog = cog_instance
        self.uid = str(user_id)

    @discord.ui.button(label="🚨 中途返航（不退費）", style=discord.ButtonStyle.danger)
    async def cancel_fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid:
            return await interaction.response.send_message("❌ 這不是你的釣魚任務！", ephemeral=True)

        all_fishers = self.cog.get_all_fishers()
        data = all_fishers.get(self.uid)
        if not data:
            return await interaction.response.send_message("⚠️ 找不到你的釣魚紀錄，可能已經結算了。", ephemeral=True)

        end_time = data.get("end_time")
        if isinstance(end_time, str):
            try:
                end_time = datetime.fromisoformat(end_time)
            except Exception:
                pass
        now = datetime.now()
        if end_time and now >= end_time:
            await interaction.response.send_message("🏁 你的漁船已經回港了！請使用 `/fish` 領取成果。", ephemeral=True)
            return

        times = data.get("times", 1)
        original_cost = times * 50

        confirm_view = FishCancelConfirmView(self.cog, self.uid, original_cost, self)
        embed = discord.Embed(title="⚠️ 確認中途返航？", color=0xff9900)
        embed.description = (
            f"你確定要取消釣魚任務嗎？\n\n"
            f"💸 **出海費用：** `${original_cost:,}`\n"
            f"❌ **費用不予退還**\n\n"
            "此操作無法撤銷！"
        )
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)


class FishCancelConfirmView(discord.ui.View):
    def __init__(self, cog_instance, user_id, original_cost, active_view):
        super().__init__(timeout=30)
        self.cog = cog_instance
        self.uid = str(user_id)
        self.original_cost = original_cost
        self.active_view = active_view

    @discord.ui.button(label="✅ 確認返航", style=discord.ButtonStyle.danger)
    async def confirm_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid:
            return

        all_fishers = self.cog.get_all_fishers()
        data = all_fishers.get(self.uid)
        if not data:
            return await interaction.response.edit_message(content="⚠️ 找不到你的釣魚紀錄，可能已經結算了。", embed=None, view=None)

        self.cog.remove_fisher(self.uid)

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(title="🚨 中途返航", color=0xe74c3c)
        embed.description = (
            f"<@{self.uid}> 已取消釣魚任務！\n\n"
            f"💸 **出海費用：** `${self.original_cost:,}`\n"
            f"⚠️ **費用不予退還**\n\n"
            "下次出海前請三思！"
        )
        await interaction.response.edit_message(content="✅ 已確認返航。", embed=None, view=None)
        await interaction.followup.send(embed=embed)

    @discord.ui.button(label="🔙 取消", style=discord.ButtonStyle.secondary)
    async def cancel_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid:
            return

        await interaction.response.edit_message(content="✅ 已取消返航，繼續釣魚中！", embed=None, view=None)
