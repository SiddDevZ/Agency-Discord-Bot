# -*- coding: utf-8 -*-
import discord
from discord import app_commands, TextStyle
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import datetime
import io
import requests
from typing import Optional, List, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Error: No Discord bot token found in .env file. Please add TOKEN=your_token_here")
    sys.exit(1)

try:
    GUILD = int(os.getenv("GUILD", "0"))
    if GUILD == 0:
        print("Warning: No GUILD ID found in .env file. Please add GUILD=your_guild_id")
except ValueError:
    print("Error: GUILD ID must be an integer")
    sys.exit(1)

try:
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))
    if LOG_CHANNEL == 0:
        print("Warning: No LOG_CHANNEL ID found in .env file. Transcript logging will be disabled.")
except ValueError:
    print("Error: LOG_CHANNEL ID must be an integer")
    LOG_CHANNEL = 0

ICON_URL = os.getenv("ICON_URL", "")
if not ICON_URL:
    print("Warning: No ICON_URL found in .env file. Default icons will not appear in embeds.")

CSS = os.getenv("CSS", "body{font-family:Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5}.messages{display:flex;flex-direction:column;gap:10px}.message{display:flex;flex-direction:column;padding:10px;border-radius:5px;background:white;box-shadow:0 1px 3px rgba(0,0,0,0.1)}.message img{width:30px;height:30px;border-radius:50%;margin-right:10px}.author{font-weight:bold;margin-right:10px}.timestamp{color:#666;font-size:0.8em}.content{margin-top:5px}")

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("-"), intents=intents)

# Error handling
@bot.event
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        embed = discord.Embed(
            description=f"Please try again in {error.retry_after:.2f}s.",
            colour=discord.Colour.from_rgb(21, 116, 0),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        raise error

# Ticket system modal classes
class Support(discord.ui.Modal, title="Support Ticket"):
    details = discord.ui.TextInput(
        label="Support Details",
        placeholder="Describe your issue or question in detail",
        style=TextStyle.long,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            guild = bot.get_guild(GUILD)
            ticket_category = discord.utils.get(guild.categories, name="━━━| 🎫 TICKETS |━━━")
            
            if not ticket_category:
                await interaction.response.send_message(
                    "Error: Ticket category not found. Please contact server administrators.",
                    ephemeral=True
                )
                return
                
            user = interaction.user
            user_avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            
            embed = discord.Embed(
                title=f"<:user:1351969175001759755> New Support Request",
                description=f"<:dot:996804674252439733> **Description:**\n> {self.details.value}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=user_avatar_url)

            ticket_channel = await guild.create_text_channel(
                f"❓〢{interaction.user.name.lower()}",
                category=ticket_category
            )
            
            await ticket_channel.set_permissions(guild.default_role,
                                                view_channel=False,
                                                read_messages=False,
                                                send_messages=False)
            await ticket_channel.set_permissions(interaction.user,
                                                read_messages=True,
                                                send_messages=True)
            
            em = discord.Embed(
                description=f"Your ticket has been created in {ticket_channel.mention}",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=em, ephemeral=True)
            damn = await ticket_channel.send("@everyone", embed=embed, view=TicketView(ticket_channel))
            await damn.pin()
            
            com = discord.Embed(
                title="<:check_yes:1351969576669151304> Request Submitted",
                description="Please wait while our team reviews your request.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            await ticket_channel.send(embed=com)
        except Exception as e:
            print(f"Support modal error: {e}")
            try:
                await interaction.response.send_message(
                    f"An error occurred creating your ticket: {str(e)[:100]}. Please try again or contact an administrator.",
                    ephemeral=True
                )
            except:
                try:
                    await interaction.followup.send(
                        "An error occurred creating your ticket. Please try again or contact an administrator.",
                        ephemeral=True
                    )
                except:
                    pass
                    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(f"Support modal error: {error}")
        await interaction.response.send_message(
            "An error occurred. Please try again or contact an administrator.",
            ephemeral=True
        )


class MyModal(discord.ui.Modal, title="Placing Order"):
    project_details = discord.ui.TextInput(
        label="Project Details",
        placeholder="Briefly describe your project",
        style=TextStyle.long,
        required=True
    )
    
    budget = discord.ui.TextInput(
        label="Budget (In USD)",
        placeholder="Provide your approximate budget",
        style=TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            guild = bot.get_guild(GUILD)
            ticket_category = discord.utils.get(guild.categories, name="━━━| 🎫 TICKETS |━━━")
            
            if not ticket_category:
                await interaction.response.send_message(
                    "Error: Ticket category not found. Please contact server administrators.",
                    ephemeral=True
                )
                return
                
            user = interaction.user
            user_avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            
            embed = discord.Embed(
                title=f"New Commission Request",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Project Details", value=f"```{self.project_details.value}```", inline=False)
            embed.add_field(name="Budget", value=f"```{self.budget.value}```", inline=True)
            embed.add_field(name="Submitted by", value=f"```{interaction.user.name}```", inline=True)
            embed.set_thumbnail(url=user_avatar_url)

            ticket_channel = await guild.create_text_channel(
                f"🎫〢{interaction.user.name.lower()}",
                category=ticket_category
            )
            
            await ticket_channel.set_permissions(guild.default_role,
                                                view_channel=False,
                                                read_messages=False,
                                                send_messages=False)
            await ticket_channel.set_permissions(interaction.user,
                                                read_messages=True,
                                                send_messages=True)
            
            em = discord.Embed(
                description=f"Your ticket has been created in {ticket_channel.mention}",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=em, ephemeral=True)
            damn = await ticket_channel.send("@everyone", embed=embed, view=TicketView(ticket_channel))
            await damn.pin()
            
            com = discord.Embed(
                title="<:check_yes:1351969576669151304> Request Submitted",
                description="Please wait while our team reviews your request.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            await ticket_channel.send(embed=com)
        except Exception as e:
            print(f"Order modal error: {e}")
            try:
                await interaction.response.send_message(
                    f"An error occurred creating your ticket: {str(e)[:100]}. Please try again or contact an administrator.",
                    ephemeral=True
                )
            except:
                try:
                    await interaction.followup.send(
                        "An error occurred creating your ticket. Please try again or contact an administrator.",
                        ephemeral=True
                    )
                except:
                    pass
                    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(f"Order modal error: {error}")
        await interaction.response.send_message(
            "An error occurred. Please try again or contact an administrator.",
            ephemeral=True
        )


class TicketView(discord.ui.View):
    def __init__(self, ticket_channel):
        super().__init__(timeout=None)
        self.ticket_channel = ticket_channel

    @discord.ui.button(label="Close", emoji="🔒", custom_id="ticket:close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        confirm_view = ConfirmCloseView(self.ticket_channel)

        confirm_embed = discord.Embed(
            title="Confirm Ticket Closure",
            description="Are you sure you want to close this ticket? This action cannot be undone.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view)


class ConfirmCloseView(discord.ui.View):
    def __init__(self, ticket_channel):
        super().__init__(timeout=60)
        self.ticket_channel = ticket_channel
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger, custom_id="confirm_close:yes")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_permissions = interaction.user.guild_permissions
        if not user_permissions.administrator:
            embed = discord.Embed(
                title="<a:alert:1351969965233934466> No Permission",
                description="You cannot close this ticket. If you created it by mistake, please contact a staff member."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        try:
            try:
                await interaction.message.delete()
            except:
                pass
            
            await interaction.response.defer()
            
            channel = interaction.channel
            if not channel:
                await interaction.followup.send("Error: Could not find the channel", ephemeral=True)
                return
                
            # Process ticket transcript if logging is enabled
            log_channel = bot.get_channel(LOG_CHANNEL)
            if log_channel:
                messages = []
                async for message in channel.history(limit=500, oldest_first=True):
                    messages.append(message)

                # Create a text preview for direct viewing in Discord
                text_preview = f"# Transcript for {channel.name}\n"
                text_preview += f"Closed by: {interaction.user.name} ({interaction.user.id}) at <t:{int(datetime.datetime.utcnow().timestamp())}:F>\n\n"
                
                # Get ticket creator from the channel name
                ticket_creator_name = channel.name.split('〢')[-1] if '〢' in channel.name else "Unknown"
                text_preview += f"Ticket created by: {ticket_creator_name}\n"
                text_preview += f"Total messages: {len(messages)}\n\n"
                
                # Create a summary of the transcript
                text_preview += "## Message Summary\n"
                
                # Add up to 15 messages to the preview (prioritize first and latest messages)
                message_limit = min(15, len(messages))
                if len(messages) <= message_limit:
                    # If we have fewer messages than the limit, include all of them
                    preview_messages = messages
                else:
                    # Otherwise, take first 5 and last 10 messages
                    preview_messages = messages[:5] + messages[-10:]
                    text_preview += f"*Showing {message_limit} out of {len(messages)} messages*\n\n"
                
                for msg in preview_messages:
                    timestamp = f"<t:{int(msg.created_at.timestamp())}:t>"
                    text_preview += f"**{msg.author.name}** ({timestamp}): {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}\n"
                
                # Generate a more detailed HTML transcript
                transcript = ""
                
                # Improved CSS for better styling
                enhanced_css = """
                body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f9f9f9; color: #333; }
                .ticket-info { background: #4A76A8; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
                .ticket-title { font-size: 22px; margin: 0; }
                .ticket-meta { font-size: 14px; opacity: 0.8; margin-top: 5px; }
                .messages { display: flex; flex-direction: column; gap: 15px; }
                .message { display: flex; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }
                .message-avatar { width: 50px; padding: 15px; }
                .message-avatar img { width: 50px; height: 50px; border-radius: 50%; }
                .message-content { flex: 1; padding: 15px 15px 15px 0; }
                .message-header { display: flex; align-items: center; margin-bottom: 5px; }
                .message-author { font-weight: bold; margin-right: 8px; }
                .message-timestamp { color: #888; font-size: 12px; }
                .message-text { margin-top: 5px; white-space: pre-wrap; }
                .message-attachments { margin-top: 10px; }
                .message-attachments a { display: inline-block; margin-right: 10px; color: #4A76A8; text-decoration: none; }
                .system-message { background: #f0f7ff; border-left: 4px solid #4A76A8; padding: 10px; margin: 5px 0; }
                """
                
                # HTML header with metadata
                transcript += f"""<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Ticket Transcript - {channel.name}</title>
                    <style>{enhanced_css}</style>
                </head>
                <body>
                    <div class="ticket-info">
                        <h1 class="ticket-title">Ticket: {channel.name}</h1>
                        <div class="ticket-meta">
                            <div>Created by: {ticket_creator_name}</div>
                            <div>Closed by: {interaction.user.name} on {datetime.datetime.utcnow().strftime('%Y-%m-%d at %H:%M:%S UTC')}</div>
                            <div>Total Messages: {len(messages)}</div>
                        </div>
                    </div>
                    <div class="messages">
                """
                
                # Add each message to the transcript
                for message in messages:
                    author_name = message.author.name
                    author_avatar = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                    message_content = message.content.replace('<', '&lt;').replace('>', '&gt;')
                    timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Handle embeds
                    embeds_html = ""
                    if message.embeds:
                        for embed in message.embeds:
                            embeds_html += f'<div class="system-message">'
                            if embed.title:
                                embeds_html += f'<strong>{embed.title}</strong><br>'
                            if embed.description:
                                embeds_html += f'{embed.description}<br>'
                            embeds_html += '</div>'
                    
                    # Handle attachments
                    attachments_html = ""
                    if message.attachments:
                        attachments_html = '<div class="message-attachments">'
                        for attachment in message.attachments:
                            attachments_html += f'<a href="{attachment.url}" target="_blank">{attachment.filename}</a> '
                        attachments_html += '</div>'
                    
                    # Add the message to the transcript
                    transcript += f"""
                    <div class="message">
                        <div class="message-avatar">
                            <img src="{author_avatar}" alt="{author_name}"/>
                        </div>
                        <div class="message-content">
                            <div class="message-header">
                                <span class="message-author">{author_name}</span>
                                <span class="message-timestamp">{timestamp}</span>
                            </div>
                            <div class="message-text">{message_content}</div>
                            {embeds_html}
                            {attachments_html}
                        </div>
                    </div>
                    """
                
                # Close the HTML
                transcript += "</div></body></html>"

                # Send text preview
                preview_embed = discord.Embed(
                    title=f"📝 Ticket Transcript Preview - {channel.name}",
                    description=text_preview[:4000] if len(text_preview) > 4000 else text_preview,
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.utcnow()
                )
                preview_embed.set_footer(text="Full HTML transcript attached below")
                await log_channel.send(embed=preview_embed)
                
                # Send the full HTML transcript
                with io.StringIO(transcript) as transcript_file:
                    await log_channel.send(
                        file=discord.File(transcript_file, filename=f"transcript-{channel.name}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.html")
                    )
            
            closing_embed = discord.Embed(
                title="<a:alert:1351969965233934466> Ticket Closing",
                description="This ticket is now being closed and will be deleted shortly.",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            await channel.send(embed=closing_embed)
            
            # Wait a short time for users to see the message
            await asyncio.sleep(3)
            
            # Delete the channel
            await channel.delete()
            
        except Exception as e:
            error_embed = discord.Embed(
                title="Error",
                description=f"An error occurred while closing the ticket: {str(e)}",
                color=discord.Color.red()
            )
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                await interaction.channel.send(embed=error_embed)

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary, custom_id="confirm_close:no")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except:
            pass
        
        await interaction.response.defer()
        self.stop()


class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 7200, commands.BucketType.user)
        self.add_item(
            discord.ui.Button(
                label="Terms of Service",
                url="https://discord.com/channels/1326998747841822740/1326998748315914250",
                # emoji="📕"
            )
        )

    @discord.ui.button(
        label="Order",
        style=discord.ButtonStyle.success,
        emoji="<:cart:1352016456174272664>",
        custom_id="persistent_view:ticket"
    )
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = bot.get_guild(GUILD)
        ticket_category = discord.utils.get(guild.categories, name="━━━| 🎫 TICKETS |━━━")
        
        if not ticket_category:
            await interaction.response.send_message(
                "Error: Ticket category not found. Please contact server administrators.",
                ephemeral=True
            )
            return
            
        # Allow admins to bypass the ticket limit check
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_modal(MyModal())
            return
            
        user_tickets = [
            channel for channel in ticket_category.channels 
            if channel.name.endswith(f"{interaction.user.name.lower()}")
        ]
        
        if len(user_tickets) >= 2:
            await interaction.response.send_message(
                "You already have 2 open tickets. Please close one before creating a new ticket.",
                ephemeral=True
            )
            return
        else:
            await interaction.response.send_modal(MyModal())

    @discord.ui.button(
        label="Support",
        style=discord.ButtonStyle.gray,
        # emoji="<:user:1351969175001759755>",
        custom_id="persistent_view:support"
    )
    async def support(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = bot.get_guild(GUILD)
        ticket_category = discord.utils.get(guild.categories, name="━━━| 🎫 TICKETS |━━━")
        
        if not ticket_category:
            await interaction.response.send_message(
                "Error: Ticket category not found. Please contact server administrators.",
                ephemeral=True
            )
            return
            
        # Allow admins to bypass the ticket limit check
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_modal(Support())
            return
            
        # Count user's existing tickets
        user_tickets = [
            channel for channel in ticket_category.channels 
            if channel.name.endswith(f"{interaction.user.name.lower()}")
        ]
        
        if len(user_tickets) >= 2:
            await interaction.response.send_message(
                "You already have 2 open tickets. Please close one before creating a new ticket.",
                ephemeral=True
            )
            return
        else:
            await interaction.response.send_modal(Support())


@bot.command(name="send")
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🎟️ Tickets",
        description=(
            "🛒 **Making a Purchase**\n"
            "> If you want to purchase any service or item, click the \"<:cart:1352016456174272664> Order\" button.\n\n"
            "<:user:1351969175001759755> **Need Help?**\n"
            "> For support, click the support button for assistance, fixes, or questions.\n\n"
            "📕 **Terms of Service**\n"
            "> Please review our Terms of Service before purchasing. We are not responsible for any misunderstandings.\n\n"
        ),
        color=discord.Color.from_rgb(66, 95, 71),
    )
    embed.set_footer(text="LuvoWeb • The Future of Freelance", icon_url=ICON_URL)
    embed.set_image(url="https://i.imgur.com/RTh8LFv.png")
    embed.set_thumbnail(url=ICON_URL)

    await ctx.channel.send(embed=embed, view=PersistentView())


@bot.command(name="embed")
async def about_command(ctx):
    # First embed with just the image
    embed1 = discord.Embed(color=discord.Color.from_rgb(48, 44, 52))
    embed1.set_image(url="https://i.imgur.com/h7zJWq5.png")
    
    # Second embed with all the text content
    embed2 = discord.Embed(
        title="Welcome to LuvoWeb Freelance!",
        color=discord.Color.from_rgb(48, 44, 52),
        description=(
            "> LuvoWeb offers top-quality services in Web Development, Discord bot development, and UI/UX design."
            " Our custom solutions are tailored to your needs and exceed expectations.\n\n"
            "**To place an order, open a ticket in <#1326998748315914247> or view our showcase in <#1326998748718698563>.**\n\n"
            "Contact us today to discuss your project and let us elevate your business."
        )
    )
    
    # Add fields from the third embed
    embed2.add_field(
        name="💎 **__LuvoWeb QuickLinks__**",
        value="> [Website](https://luvoweb.com)\n> [disboard.org](https://disboard.org/server/1326998747841822740)",
        inline=True
    )
    embed2.add_field(
        name="<:settings:1351970266825097337> **__Information__**",
        value="> Established in <t:1679423400:D>\n> Founder: <@273352781442842624>\n> Vote us: [disboard.org](https://disboard.org/server/1326998747841822740)",
        inline=True
    )
    
    embed2.set_thumbnail(url=ICON_URL)
    embed2.set_footer(text="LuvoWeb • The Future of Freelance", icon_url=ICON_URL)
    
    # Create simplified view with only the essential buttons
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="Order Now", 
        emoji="🛒", 
        url="https://discord.com/channels/1326998747841822740/1326998748315914247"
    ))
    view.add_item(discord.ui.Button(
        label="Terms of Service", 
        url="https://discord.com/channels/1326998747841822740/1326998748315914250"
    ))
    view.add_item(discord.ui.Button(
        label="Website", 
        url="https://luvoweb.com"
    ))

    # Send both embeds
    await ctx.send(embeds=[embed1, embed2], view=view)


@bot.command(name="rules")
async def rules_command(ctx):
    # First embed with just the image
    rules_intro = discord.Embed(
        title="LuvoWeb Community Guidelines",
        description="Please follow these rules to maintain a professional environment for our web development community.",
        color=discord.Color.from_rgb(48, 44, 52)
    )
    rules_intro.set_image(url="https://i.imgur.com/ltnEOM1.png")
    
    # Rules embed list - tailored for web development agency
    rule_embeds = [
        discord.Embed(
            title="<:dot:996804674252439733> RULE 1 - Do Not Spam",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Avoid sending repetitive messages, excessive emojis, or flooding channels with content. This includes project requests, portfolio shares, or technical questions. Use the appropriate channels for your inquiries and limit your messages to maintain a clean, professional environment."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 2 - No Discrimination",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Our agency values diversity and inclusion. Any form of racism, sexism, homophobia, or discriminatory behavior against clients, team members, or community participants will not be tolerated. Treat everyone with respect regardless of their technical experience, background, or business size."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 3 - No Harassment or Bullying",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Criticism of work should be constructive and professional. Do not belittle others' technical skills, design choices, or business decisions. We foster a supportive environment for learning and collaboration, not competition or negativity."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 4 - No NSFW Content",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Keep all content work-appropriate. This is a professional server for web development services. Do not share, request, or discuss explicit material, even in the context of website projects. We maintain a professional image and environment at all times."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 5 - No Unauthorized Selling",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Do not offer competing services or sell products within our community. Only LuvoWeb team members may offer development services here. Clients should not be solicited by other developers in any channel or via DM. Violations will result in immediate removal."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 6 - No Illegal Activities",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Do not request or offer services for illegal websites or applications (phishing, scamming, copyright infringement, etc.). All projects must comply with relevant laws and regulations. We will not participate in or facilitate illegal activities, including software piracy or unauthorized access systems."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 7 - No DM Advertising",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Do not send unsolicited messages to members offering services, requesting work, or promoting external businesses. All inquiries must go through proper channels. Respect others' privacy and our professional environment. Direct message advertising will result in immediate action."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 8 - Respect Staff Authority",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Our staff makes final decisions regarding projects, timelines, and pricing. Do not argue with staff about estimates, deadlines, or technical approaches in public channels. If you have concerns, address them privately through appropriate support channels or with senior management."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 9 - Follow Discord TOS & Industry Ethics",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Adhere to both Discord's Terms of Service and web development industry ethical standards. This includes respecting intellectual property, maintaining client confidentiality, and following accessibility guidelines where applicable. [Discord Terms of Service](https://discord.com/terms)"
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 10 - No Public Advertising",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Do not advertise external services, agencies, freelancers, or competing products in any public channel. This includes subtle references, portfolio links (unless requested by staff), or mentions of other development teams. Use designated channels for sharing resources when appropriate."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 11 - No Unsolicited Project Requests",
            color=discord.Color.from_rgb(48, 44, 52),
            description="All project inquiries must be made through the proper ticket system, not in public channels. Do not interrupt ongoing discussions with your project needs or repeatedly ask for quotes in community spaces. Respect our workflow and process for handling client requests."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> RULE 12 - Professional Conduct",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Maintain professional communication at all times. Use appropriate technical terminology, provide clear requirements when requesting services, and respect confidentiality agreements. Remember that this server represents a professional web development agency, not a casual community."
        )
    ]
    
    for embed in rule_embeds:
        embed.set_footer(text="LuvoWeb • The Future of Freelance", icon_url=ICON_URL)
    
    # Send the intro embed first
    await ctx.send(embed=rules_intro)
    
    # Then send each rule embed
    for embed in rule_embeds:
        await ctx.send(embed=embed)
        await asyncio.sleep(0.5)  # Brief delay between messages to prevent rate limiting


@bot.command(name="terms")
async def tos_command(ctx):
    # First embed with just the image
    tos_intro = discord.Embed(
        title="LuvoWeb Terms of Service",
        description="Please review our Terms of Service carefully before engaging our services.",
        color=discord.Color.from_rgb(48, 44, 52)
    )
    tos_intro.set_image(url="https://i.imgur.com/22VpVZg.jpeg")
    
    tos_embeds = [
        discord.Embed(
            title="<:dot:996804674252439733> Services Overview",
            color=discord.Color.from_rgb(48, 44, 52),
            description="LuvoWeb provides web development, UI/UX design, and Discord bot development services. All services are provided on an as-is basis with no guarantees except as expressly provided in these terms. We reserve the right to refuse service to anyone for any reason at any time."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Project Process",
            color=discord.Color.from_rgb(48, 44, 52),
            description="All projects begin with requirement gathering through our ticket system. Once requirements are confirmed, we provide a timeline and pricing quote. Work begins after initial payment is received. Regular updates will be provided throughout the development process."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Payment Terms",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Payment is structured in three phases: 33% upfront, 33% after demonstrable progress, and 34% upon project completion. Prices are quoted in USD. We accept payment via PayPal, bank transfer, crypto, or other methods as specified in your contract. Invoices must be paid within 7 days of issuance."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Intellectual Property Rights",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Upon final payment, clients receive full ownership rights to the final deliverables created specifically for them. LuvoWeb retains rights to any pre-existing code, frameworks, or tools used in development. We reserve the right to display work in our portfolio unless specifically agreed otherwise."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Revisions and Modifications",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Each project includes a predefined number of revision cycles as specified in your contract. Additional revisions beyond this limit will incur extra charges. Major changes to project scope may require renegotiation of timeline and costs. Minor adjustments after project completion are offered for 30 days at no additional cost."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Client Responsibilities",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Clients are responsible for providing timely feedback, necessary content, and access to accounts required for project completion. Delayed responses from clients may result in project timeline extensions. Clients must ensure they have proper rights to all content provided for use in the project."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Confidentiality",
            color=discord.Color.from_rgb(48, 44, 52),
            description="We treat all client information as confidential and will not share sensitive details with third parties without permission. Clients agree not to disclose proprietary information about our development processes. NDAs are available upon request for projects requiring additional confidentiality."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Cancellation Policy",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Project cancellation by the client after work has begun will result in payment for all work completed up to that point. The initial deposit is non-refundable. LuvoWeb reserves the right to terminate projects due to client inactivity (no response for 21+ days) or violation of these terms."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Refund Policy",
            color=discord.Color.from_rgb(48, 44, 52),
            description="No refunds are provided after project completion and delivery. For cancellations prior to completion, refunds are limited to payments for work not yet performed, minus the non-refundable deposit. Dispute resolution will be attempted before any refund is processed."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Limitation of Liability",
            color=discord.Color.from_rgb(48, 44, 52),
            description="LuvoWeb is not liable for any damages arising from the use of our services beyond the amount paid for the project. We do not guarantee specific business outcomes, traffic increases, or revenue generation. We are not responsible for third-party services integrated into client projects."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Hosting and Maintenance",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Unless specifically included in your contract, hosting, domain registration, and ongoing maintenance are not included in project fees. We offer separate maintenance packages that can be purchased after project completion. Clients are responsible for their hosting environment unless otherwise specified."
        ),
        discord.Embed(
            title="<:dot:996804674252439733> Dispute Resolution",
            color=discord.Color.from_rgb(48, 44, 52),
            description="Any disputes will be addressed through good-faith negotiation before other actions are taken. If negotiation fails, disputes will be resolved according to the laws of our registered jurisdiction. By using our services, you agree to these terms in their entirety."
        )
    ]
    
    for embed in tos_embeds:
        embed.set_footer(text="LuvoWeb • The Future of Freelance", icon_url=ICON_URL)
    
    await ctx.send(embed=tos_intro)
    
    for embed in tos_embeds:
        await ctx.send(embed=embed)
        await asyncio.sleep(0.5) 

async def get_ai_response(prompt, max_attempts=3):
    model = "gpt-4o"
    providers = ["Blackbox", "DarkAI", "PollinationsAI"]
    api_url = "https://chat-api-rp7a.onrender.com/v1/chat/completions"
    
    # Format message history (simplified for a single prompt)
    messages = [{"role": "user", "content": prompt}]
    
    # Function to query a single provider
    def query_provider(provider):
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "provider": provider,
                        "stream": False
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"], provider
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"Error with {provider}: {str(e)}")
        
        return None, provider
    
    result = None
    successful_provider = None
    
    with ThreadPoolExecutor(max_workers=len(providers)) as executor:
        future_to_provider = {executor.submit(query_provider, provider): provider for provider in providers}
        
        for future in as_completed(future_to_provider):
            response, provider = future.result()
            if response:
                result = response
                successful_provider = provider
                break
    
    if result:
        # print(f"Response received from {successful_provider}")
        return result
    else:
        return "Sorry, I couldn't get a response from any AI provider at the moment."

@bot.tree.command(name='meme', description='Shows a random meme')
@app_commands.checks.cooldown(1, 7)
async def meme(interaction: discord.Interaction):
    try:
        response = requests.get('https://meme-api.com/gimme/dankmemes')
        response.raise_for_status()
        data = response.json()
        
        embed = discord.Embed(title=data['title'])
        embed.set_image(url=data['preview'][-1])
        embed.set_footer(text=f"👍: {data['ups']} | Luvo Freelance")
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error fetching meme: {str(e)}", ephemeral=True)


@bot.tree.command(name='quote', description='Gives an inspirational quote')
@app_commands.checks.cooldown(1, 4)
async def quote(interaction: discord.Interaction):
    try:
        response = requests.get("https://zenquotes.io/api/random")
        response.raise_for_status()
        data = response.json()
        
        quote_text = f"{data[0]['q']} - {data[0]['a']}"
        
        embed = discord.Embed(
            description=quote_text, 
            colour=discord.Colour.blue()
        )
        embed.set_footer(text=f"Command executed by {interaction.user.name} | Luvo Freelance")
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error fetching quote: {str(e)}", ephemeral=True)


@bot.tree.command(name="version", description="Shows bot version information")
async def version(interaction: discord.Interaction):
    embed = discord.Embed(
        title="About LuvoBot",
        # description="`Version Beta`: Released in <t:1686772380:d>",
        color=discord.Color.green()
    )
    embed.add_field(name="Language", value="```Python 3.11```", inline=True)
    embed.add_field(name="Main Library", value="```discord.py```", inline=True)
    embed.add_field(name="Developer", value="```@siddharthz```", inline=True)
    embed.add_field(name="Latency", value=f"```{bot.latency*1000:.2f}ms```", inline=True)
    embed.set_thumbnail(url=ICON_URL)
    embed.set_footer(text="LuvoWeb Freelance")

    await interaction.response.send_message(embed=embed)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    
    try:
        # Sync commands with Discord
        guild = discord.Object(id=GUILD) if GUILD != 0 else None
        await bot.tree.sync(guild=guild)
        print(f"Slash commands synced {'to guild' if guild else 'globally'}")
        
        # Add persistent views
        bot.add_view(PersistentView())
        
        # Add views for ticket system persistence by registering their custom IDs
        bot.add_view(TicketView(None))  
        bot.add_view(ConfirmCloseView(None))
        print("Persistent views added")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


async def evaluate_message_content(message_content):
    """
    Send message to AI to evaluate if it violates community guidelines
    
    Returns:
        str: "DELETE", "REDIRECT", or "GOOD" based on AI evaluation
    """
    prompt = (
        "As the owner of a web development agency Discord server, your focus is on fostering natural "
        "discussions, collaboration, and knowledge sharing about web development. Promotions, advertisements, "
        "self-promotion, or soliciting — such as offering services, seeking clients, or posting personal "
        "project links with commercial intent, or even just saying they are a web developer — are strictly prohibited. Direct requests for services, hiring, "
        "or any transactional conversations should be redirected to proper channels. Your task is to evaluate "
        "messages and respond with \"DELETE\" for those that break these guidelines, \"REDIRECT\" for clients "
        "seeking services, or \"GOOD\" for messages that align with the community's purpose. Message is \"\"\""
        f"{message_content}\"\"\""
    )
    
    response = await get_ai_response(prompt)
    
    if "DELETE" in response:
        return "DELETE"
    elif "REDIRECT" in response:
        return "REDIRECT"
    else:
        return "GOOD"


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Process commands first before any other logic
    await bot.process_commands(message)
    
    if message.author.id in [273352781442842624]:
        return
    
    if message.channel.category and message.channel.category.name == "Community":
        evaluation = await evaluate_message_content(message.content)
        
        if evaluation == "DELETE":
            # Notify owner in designated channel for deleted messages
            try:
                deletion_channel = bot.get_channel(1352513103333560340)
                if deletion_channel:
                    embed = discord.Embed(
                        title="🚫 Message Deleted - Rule Violation",
                        description=f"A message by {message.author.mention} in {message.channel.mention} was deleted for violating community guidelines.",
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    
                    embed.add_field(
                        name="User",
                        value=f"{message.author.mention} (`{message.author.name}`)",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="Sent at",
                        value=f"<t:{int(message.created_at.timestamp())}:F>",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="Deleted Message",
                        value=f"```{message.content[:1000]}{'...' if len(message.content) > 1000 else ''}```",
                        inline=False
                    )
                    
                    # Add user avatar as thumbnail
                    user_avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                    embed.set_thumbnail(url=user_avatar_url)
                    
                    # Add footer with additional info
                    embed.set_footer(text="LuvoWeb • Moderation Alert", icon_url=ICON_URL)
                    
                    await deletion_channel.send(embed=embed)
                else:
                    print("Deletion notification channel not found")
            except Exception as e:
                print(f"Failed to send deletion notification: {str(e)}")
            
            # Delete the message
            await message.delete()
            
            muted_role = discord.utils.get(message.guild.roles, name="Muted")
            if muted_role:
                try:
                    await message.author.add_roles(muted_role)
                    
                    try:
                        await message.author.send(
                            "Your message was removed and you have been muted now because it violated our community guidelines. "
                            "Please refrain from posting promotional or advertisement content in our server."
                        )
                    except discord.errors.Forbidden:
                        pass
                        
                except discord.errors.Forbidden:
                    print(f"Couldn't mute user {message.author.name} - missing permissions")
            else:
                print("Muted role not found")
                
        elif evaluation == "REDIRECT":
            redirect_msg = await message.channel.send(
                f"{message.author.mention}, it seems you're looking for services. "
                f"Please message <@273352781442842624> directly or open a ticket in <#1326998748315914247> for assistance."
            )
            
            try:
                notification_channel = bot.get_channel(1352511817376731187)
                if notification_channel:
                    embed = discord.Embed(
                        title="💼 Potential Client Detected",
                        description=f"A user appears to be looking for services in {message.channel.mention}",
                        color=discord.Color.from_rgb(66, 95, 71),
                        timestamp=datetime.datetime.utcnow()
                    )
                    
                    embed.add_field(
                        name="User",
                        value=f"{message.author.mention} (`{message.author.name}`)",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="Sent at",
                        value=f"<t:{int(message.created_at.timestamp())}:F>",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="Original Message",
                        value=f"```{message.content[:1000]}{'...' if len(message.content) > 1000 else ''}```",
                        inline=False
                    )
                    
                    user_avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                    embed.set_thumbnail(url=user_avatar_url)
                    
                    embed.set_footer(text="LuvoWeb • Potential Lead Alert", icon_url=ICON_URL)
                    
                    await notification_channel.send(f"<@273352781442842624>", embed=embed)
                else:
                    print("Notification channel not found")
            except Exception as e:
                print(f"Failed to send notification: {str(e)}")
            
            await message.delete()
            
            await asyncio.sleep(300) 
            try:
                await redirect_msg.delete()
            except discord.errors.NotFound:
                pass


@bot.tree.command(name='ask', description='Ask a question to our AI assistant')
@app_commands.checks.cooldown(1, 10)
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer(ephemeral=False)
    
    try:
        ai_response = await get_ai_response(question)
        
        embed = discord.Embed(
            color=discord.Color.from_rgb(66, 95, 71),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.description = f"**Question:**\n```{question[:1000]}{'...' if len(question) > 1000 else ''}```"
        
        embed.add_field(
            name="AI Response",
            value=ai_response[:4000] if len(ai_response) > 4000 else ai_response,
            inline=False
        )
        
        user_avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        embed.set_thumbnail(url=user_avatar_url)
        
        embed.set_footer(
            text=f"Requested by {interaction.user.name} • LuvoWeb",
            icon_url=ICON_URL
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="<a:alert:1351969965233934466> Error",
            description=f"I couldn't process your request properly. Please try again later.\n\n```{str(e)[:1000]}```",
            color=discord.Color.red()
        )
        error_embed.set_footer(text="LuvoWeb • The Future of Freelance", icon_url=ICON_URL)
        await interaction.followup.send(embed=error_embed, ephemeral=True)


if __name__ == "__main__":
    bot.run(TOKEN)
