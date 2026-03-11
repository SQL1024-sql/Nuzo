import asyncio
import random
from datetime import datetime, timedelta

import discord
from discord import app_commands


class FishCommandsMixin:
    @app_commands.command(name="fish", description="開始掛機釣魚（漁船影響速度、魚竿影響品質；次數 1~5000）")
    @app_commands.describe(times="釣魚次數（1~5000，預設 1）")
    @app_commands.guild_only()
    async def fish(self, interaction: discord.Interaction, times: int = 1):
        uid = interaction.user.id
        now = datetime.now()
        all_fishers = self.get_all_fishers()
        uid_str = str(uid)
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
                remaining = end_time - now
                rm, rs = divmod(int(remaining.total_seconds()), 60)
                rh, rm = divmod(rm, 60)
                if rh > 0:
                    remain_str = f"{rh}時{rm}分{rs}秒"
                elif rm > 0:
                    remain_str = f"{rm}分{rs}秒"
                else:
                    remain_str = f"{rs}秒"
                active_view = self._make_fish_active_view(uid)
                embed = discord.Embed(title="🎣 釣魚任務執行中", color=0x3498db)
                embed.description = (
                    f"👤 **釣客：** <@{uid}>\n"
                    f"🚤 **漁船等級：** `Lv.{status.get('boat_level', '?')}`\n"
                    f"🎣 **魚竿等級：** `Lv.{status.get('rod_level', '?')}`\n"
                    f"🔔 **預計回港：** `{end_time.strftime('%H:%M:%S')}`\n"
                    f"⏳ **剩餘時間：** `{remain_str}`\n"
                    f"🎯 **釣魚次數：** `{status.get('times', '?')}` 次"
                )
                await interaction.response.send_message(embed=embed, view=active_view)
                return
        if times < 1 or times > 5000:
            await interaction.response.send_message("❌ `times` 必須介於 1~5000（例如：`/fish times:100`）。", ephemeral=True)
            return
        await self._handle_fish_start(interaction, times)

    async def finish_fishing(self, ctx, user_id_str):
        all_fishers = self.get_all_fishers()
        data = all_fishers.get(user_id_str)
        if not data:
            return

        bank = self.bot.get_cog('BankMod')
        if bank:
            try:
                bank.add_stats(data.get("guild_id"), int(user_id_str), coin=data.get("total_reward", 0))
                bank.save_data()
            except Exception as e:
                print(f"⚠️ 結算時寫入銀行失敗: {e}")

        self.remove_fisher(user_id_str)

        await self._send_fishing_embed(ctx, 'result', {
            'user_name': data.get('user_name'),
            'user_id': user_id_str,
            'rarity_counts': data.get('rarity_counts', {}),
            'total_reward': data.get('total_reward', 0)
        })

    async def do_fish_settlement(self, interaction_or_ctx, user_id_str):
        all_fishers = self.get_all_fishers()
        data = all_fishers.get(user_id_str)
        if not data:
            return

        rarity_counts = data.get("rarity_counts", {})
        total_reward = data.get("total_reward", 0)

        summary = "\n".join([f"• {r}: {count}次" for r, count in rarity_counts.items()])
        embed = discord.Embed(title="🎣 釣魚成果報告", color=0x2ecc71)
        display_name = data.get("user_name") or f"<@{user_id_str}>"
        embed.description = f"{display_name} 任務已完成！這是你在這段期間的收穫："
        embed.add_field(name="📊 捕獲統計", value=f"```\n{summary}\n```", inline=False)
        embed.add_field(name="💰 最終收益", value=f"**`${total_reward:,}`**", inline=True)

        bank = self.bot.get_cog('BankMod')
        if bank:
            try:
                bank.add_stats(data.get("guild_id"), int(user_id_str), coin=total_reward)
                bank.save_data()
            except Exception as e:
                print(f"⚠️ 結算時寫入銀行失敗: {e}")

        self.remove_fisher(user_id_str)

        try:
            if hasattr(interaction_or_ctx, "response") and not interaction_or_ctx.response.is_done():
                await interaction_or_ctx.response.send_message(embed=embed)
            else:
                await interaction_or_ctx.send(embed=embed)
        except Exception as e:
            print(f"⚠️ 發送釣魚結算 UI 失敗: {e}")

    async def _handle_fish_start(self, interaction, times):
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
        view = self._make_fish_confirm_view(interaction, times, cost, boat_lv, rod_lv, per_fish_time, duration, finish_time)
        embed = self._build_fishing_embed('start', data)
        await interaction.response.send_message(embed=embed, view=view)

    async def execute_fish_start(self, interaction: discord.Interaction, fish_view):
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
            if r == "傳說":
                w += bonus * 1
            elif r == "史詩":
                w += bonus * 1
            elif r == "稀有":
                w += int(bonus * 0.5)
            elif r == "垃圾":
                w = max(5, w - int(bonus * 1.3))
            elif r == "災難":
                w = max(1, w - int(bonus * 0.5))
            else:
                w = max(10, w - int(bonus * 0.8))
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

        hh, remainder = divmod(duration, 3600)
        mm, ss = divmod(remainder, 60)
        time_str = (f"{hh}小時" if hh > 0 else "") + (f"{mm}分" if mm > 0 else "") + f"{ss}秒"

        active_view = self._make_fish_active_view(uid)
        embed = discord.Embed(title="🚢 漁船已出海", color=0x2ecc71)
        embed.description = (
            f"👤 **釣客：** <@{uid}>\n"
            f"🚤 **漁船等級：** `Lv.{boat_lv}`\n"
            f"⏱️ **作業速度：** `{fish_view.per_fish_time:.1f}s` / 竿\n"
            f"⏳ **總計耗時：** `約 {time_str}`\n"
            f"🔔 **回港時間：** `{finish_time.strftime('%H:%M:%S')}`\n\n"
            "💡 可隨時利用/fish指令查看進度或中途返航"
        )
        await interaction.response.edit_message(embed=embed, view=active_view)

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

            summary = "\n".join([f"• {r}: {count}次" for r, count in data["rarity_counts"].items()])

            embed = discord.Embed(title="🏁 漁船回港結算", color=0xf1c40f)
            embed.description = f"<@{uid}> 你的船隊已滿載而歸！"
            embed.add_field(name="📊 捕獲統計", value=f"```\n{summary}\n```", inline=False)
            embed.add_field(name="💰 最終收益", value=f"**`${data.get('total_reward',0):,}`**", inline=True)

            view = self._make_fishing_view(interaction)

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
            color=0xff0000
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
