import discord
from discord.ext import commands
import interactions
import sqlite3
import random
import asyncio
from collections import defaultdict

# Bot token from Discord Developer Portal
bot = interactions.Client(token="MTEyNzI0NjEyMDQ2NTIwMzI5NA.Gp-EVI.idJLY4bvsjnN_eim8SyrQ44k2aZsaIo5QnKjvY", default_scope="applications.commands")

# Initialize SQLite database
conn = sqlite3.connect('cards.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS cards (rarity TEXT, group_name TEXT, member_name TEXT)')

ITEMS_PER_PAGE = 10
RARITIES = ["EVENT", "VERYRARE", "RARE", "UNCOMMON", "COMMON"]  # Order of rarities

def generate_inventory_embed(items, current_page, page_count):
    start_index = (current_page - 1) * ITEMS_PER_PAGE
    end_index = min(start_index + ITEMS_PER_PAGE, len(items))

    item_list = []
    for i in range(start_index, end_index):
        item_list.append(f"{i+1}. {items[i]}")

    if not item_list:
        item_list.append("No items found.")

    inventory_text = "\n".join(item_list)
    footer_text = f"Page {current_page}/{page_count}"

    embed = discord.Embed(title="Inventory", description=inventory_text, color=discord.Color.blue())
    embed.set_footer(text=footer_text)

    return embed

@bot.command(
    name="addcard",
    description="Adds a new card to the card database",
    options=[
        interactions.Option(
            name="card_code",
            description="The card code in the format of rarity_group_member",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def add_card(ctx: interactions.CommandContext, card_code: str):
    rarity, group, member = card_code.split(".")
    rarity = rarity.upper()
    group = group.upper()
    member = member.upper()
    insert_card(rarity, group, member)
    await ctx.send(f"Card {card_code.upper()} added!")

def insert_card(rarity, group, member):
    c.execute("INSERT INTO cards VALUES (?, ?, ?)", (rarity, group, member))
    conn.commit()
    


@bot.command(
    name="drop",
    description="Drops a random card",
)
async def drop(ctx: interactions.CommandContext):
    c.execute("SELECT * FROM cards")
    cards = c.fetchall()
    if cards:
        card = random.choice(cards)
        rarity, group, member = card
        card_code = f"{rarity}.{group}.{member}"
        await ctx.send(f"You got a {card_code.upper()} card!")
    else:
        await ctx.send("There are no cards in the database!")

@bot.command(
    name="gift",
    description="Gifts a random card to a user",
    options=[
        interactions.Option(
            name="user",
            description="The user to gift a card to",
            type=interactions.OptionType.USER,
            required=True,
        ),
    ],
)
async def gift(ctx: interactions.CommandContext, user: discord.User):
    c.execute("SELECT * FROM cards")
    cards = c.fetchall()
    if cards:
        card = random.choice(cards)
        rarity, group, member = card
        card_code = f"{rarity}.{group}.{member}"
        await ctx.send(f"You gifted a {card_code.upper()} card to {user.name}!")
    else:
        await ctx.send("There are no cards in the database!")
        
@bot.command(
    name="donotdothisone",
    description="Drops all cards from the card database. USE WITH CAUTION",
    options=[
        interactions.Option(
            name="password",
            description="Your password",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def reset_db(ctx: interactions.CommandContext, password: str):
    your_user_id = 868784129372725279  # Replace this with your actual Discord user ID
    correct_password = "Paok2004"  # Replace this with your desired password

    if ctx.author.id == your_user_id and password == correct_password:
        c.execute('DELETE FROM cards')
        conn.commit()
        await ctx.send("Database has been cleared.")
    else:
        await ctx.send("You do not have permission to use this command or the password is incorrect.")
        

@bot.command(name="inv", description="Check the inventory")
async def inv(ctx):
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
            for items in all_items[(current_page - 1) * ITEMS_PER_PAGE : current_page * ITEMS_PER_PAGE]:
                inventory_text += "\n".join(items) + "\n"
            footer_text = f"Page {current_page}/{page_count}"

            inventory_message = await ctx.send(content=f"**Inventory**\n{inventory_text}\n\n{footer_text}")
            await inventory_message.add_reaction(":backward_arrow:")  # Replace with the actual emoji name
            await inventory_message.add_reaction(":forward_arrow:")  # Replace with the actual emoji name

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in [":backward_arrow:", ":forward_arrow:"]  # Replace with the actual emoji names
                    and reaction.message.id == inventory_message.id
                )

            while True:
                try:
                    reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == ":backward_arrow:":  # Replace with the actual emoji name
                        if current_page > 1:
                            current_page -= 1
                    elif str(reaction.emoji) == ":forward_arrow:":  # Replace with the actual emoji name
                        if current_page < page_count:
                            current_page += 1

                    inventory_text = ""
                    for items in all_items[(current_page - 1) * ITEMS_PER_PAGE : current_page * ITEMS_PER_PAGE]:
                        inventory_text += "\n".join(items) + "\n"
                    footer_text = f"Page {current_page}/{page_count}"
                    await inventory_message.edit(content=f"**Inventory**\n{inventory_text}\n\n{footer_text}")
                    await inventory_message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    break

            await inventory_message.clear_reactions()
        else:
            await ctx.send("Inventory is empty!")
    else:
        await ctx.send("Inventory is empty!")








@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, interactions.errors.CommandError):
        await ctx.send(str(error))

@bot.event
async def on_shutdown():
    # Close the database connection when the bot is shutting down
    conn.close()

bot.start()
