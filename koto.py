import discord
import interactions
from interactions import interactions
import sqlite3
import random
import asyncio
from collections import defaultdict

# Bot token from Discord Developer Portal
token = "TOKEN"

# Initialize the interactions client
bot = interactions.Client(token=token, default_scope="applications.commands")

# Initialize the discord.py client
discord_client = discord.Client(intents=discord.Intents.default())
slash = discord.Client(intents=discord.Intents.default())

# Initialize SQLite database
conn = sqlite3.connect('cards.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS cards (rarity TEXT, group_name TEXT, member_name TEXT)')

ITEMS_PER_PAGE = 10
RARITIES = ["EVENT", "VERYRARE", "RARE", "UNCOMMON", "COMMON"]  # Order of rarities

# Command to check the inventory
@bot.command(
    name="inv",
    description="Check the inventory",
)
async def inv(ctx: interactions.CommandContext):
    c.execute("SELECT * FROM cards")
    cards = c.fetchall()
    if cards:
        inventory = defaultdict(list)
        for card in cards:
            rarity, group, member = card
            inventory[rarity].append(f"{group}.{member}")

        sorted_rarities = sorted(inventory.keys(), key=lambda x: RARITIES.index(x))
        all_items = [inventory[rarity] for rarity in sorted_rarities if inventory[rarity]]

        if all_items:
            page_count = (len(all_items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            current_page = 1

            inventory_text = ""
            for items in all_items[(current_page - 1) * ITEMS_PER_PAGE: current_page * ITEMS_PER_PAGE]:
                inventory_text += "\n".join(items) + "\n"
            footer_text = f"Page {current_page}/{page_count}"
            message = await ctx.send(f"**Inventory**\n{inventory_text}\n\n{footer_text}")

            # React to the message with emoji names
            await message.add_reaction(":arrow_backward:")  # Replace with the actual emoji name
            await message.add_reaction(":arrow_forward:")  # Replace with the actual emoji name

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in [":arrow_backward:", ":arrow_forward:"]  # Replace with the actual emoji names
                    and reaction.message.id == message.id
                )

            while True:
                try:
                    reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == ":arrow_backward:" and current_page > 1:  # Replace with the actual emoji name
                        current_page -= 1
                    elif str(reaction.emoji) == ":arrow_forward:" and current_page < page_count:  # Replace with the actual emoji name
                        current_page += 1
                    else:
                        continue

                    inventory_text = ""
                    for items in all_items[(current_page - 1) * ITEMS_PER_PAGE: current_page * ITEMS_PER_PAGE]:
                        inventory_text += "\n".join(items) + "\n"
                    footer_text = f"Page {current_page}/{page_count}"
                    await message.edit(content=f"**Inventory**\n{inventory_text}\n\n{footer_text}")
                    await reaction.remove(user)
                except asyncio.TimeoutError:
                    break

            # Clear reactions after timeout
            await message.clear_reactions()

        else:
            await ctx.send("Inventory is empty!")
    else:
        await ctx.send("Inventory is empty!")









@discord_client.event
async def on_ready():
    print(f"Discord.py Client logged in as {discord_client.user}")
    await discord_client.change_presence(activity=discord.Game(name="Interactions"))

@discord_client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == discord_client.user.id:
        return

    if payload.channel_id != YOUR_CHANNEL_ID:
        return

    message = await discord_client.get_channel(payload.channel_id).fetch_message(payload.message_id)

    if payload.emoji.name in ["⬅️", "➡️"]:
        await discord_client.process_commands(message)

# Start the interactions client
bot.start()

# Start the discord.py client
discord_client.run(token)