import discord
from discord.ext import commands
from tabulate import tabulate
from datetime import datetime

from models.member import Member
from models.historical import Historical
from utils import *

class Add:
    """Add commands."""

    def __init__(self, bot):
        self.bot = bot

    async def __get_rank_and_discord_id(self, author, user, roles):
        if not user:
            discord_id = author.id
            rank = 'Officer' if ADMIN_USER in roles else 'Member'
            if Member.objects(discord = author.id).count() >= 1:
                await self.bot.say(codify("Cannot add more than one character to this discord id. "
                                    "Try rerolling with gsbot reroll"))
                return (None, None)
        else:
            try:
                user_roles = [u.name for u in user.roles]
                rank = 'Officer' if ADMIN_USER in user_roles else 'Member'
            except Exception as e:
                rank = 'Member'
                print(e)
            discord_id = user.id
            if ADMIN_USER not in roles:
                await self.bot.say(codify("Only officers may perform this action"))
                return (None, None)
        
        return (rank, discord_id)

    @commands.command(pass_context=True)
    async def add(self,
                  ctx,
                  fam_name,
                  char_name,
                  level: int,
                  ap : int,
                  dp: int,
                  char_class,
                  user: discord.User = None):
        """Adds yourself as a member to the database. This member is linked with your
        discord id and can only be updated by either that member or an officer.
        **Officers can add a user by tagging them at the end. eg @drawven**
        Note: Total gear score and rank is auto calculated."""

        try:
            # if char_class is shorthand for a class name (EX. DK = DARKKNIGHT) then set it to the real name
            char_class = CHARACTER_CLASS_SHORT.get(char_class.upper()) if CHARACTER_CLASS_SHORT.get(char_class.upper()) else char_class

            # check for invalid class names
            if char_class.upper() not in CHARACTER_CLASSES:
                # find possible class names that user was trying to match
                possible_classes = list(filter(
                            lambda class_name: char_class.upper() in class_name,
                            CHARACTER_CLASSES,
                ))
                if len(possible_classes) > 1:
                    await self.bot.say(codify("Character class not recognized.\n"
                        "Did you mean {}?".format(", ".join(
                            possible_classes[:-1]) + " or " + possible_classes[-1])
                    ))
                elif len(possible_classes) == 1:
                    await self.bot.say(codify("Character class not recognized.\n"
                        "Did you mean {}?".format(possible_classes[0])
                    ))
                else:
                    await self.bot.say(
                            codify("Character class not recognized, here is a list "
                                    "of recognized classes\n "
                                    + "\n ".join(CHARACTER_CLASSES)))
                return

            author = ctx.message.author
            roles = [u.name for u in author.roles]

            rank, discord_id = await self.__get_rank_and_discord_id(author, user, roles)

            if rank is None or discord_id is None:
                return

            member = Member.create({
                'fam_name': fam_name,
                'char_name': char_name,
                'level': level,
                'ap': ap,
                'dp': dp,
                'char_class': char_class,
                'gear_score': ap + dp,
                'rank': rank,
                'discord': discord_id,
                'server': ctx.message.server.id
            })

            row = get_row([member], False)
            data = tabulate(row, HEADERS, 'simple')

            await self.bot.say(codify("Success Adding User\n\n" + data))

        except Exception as e:
            print(e)
            await self.bot.say("Something went horribly wrong")

    @commands.command(pass_context=True)
    async def reroll(self, ctx, new_char_name, level: int, ap : int, dp: int, new_char_class):
        """Just for someone special: Allows you to reroll """

        author = ctx.message.author.id
        member = Member.objects(discord = author).first()
        date = datetime.now()
        if not member:
            await self.bot.say("Can't reroll if you're not in the database :(, try adding yoursell first")
            return

        else:
            try:
                ## Adds historical data to todabase
                update = Historical.create({
                    'type': "reroll",
                    'char_class': member.char_class,
                    'timestamp': date,
                    'level': member.level + (round(member.progress, 2) * .01),
                    'ap': member.ap,
                    'dp': member.dp,
                    'gear_score': member.gear_score
                })

                historical_data = member.hist_data
                historical_data.append(update)

                member.update_attributes({
                    'char_name': new_char_name,
                    'ap': ap, 
                    'dp': dp,
                    'level': level,
                    'gear_score': ap + dp,
                    'char_class': new_char_class,
                    'updated': date,
                    'hist_data': historical_data
                })
                
                row = get_row([member], False)
                data = tabulate(row, HEADERS, 'simple')

                await self.bot.say(codify("Success Rerolling\n\n" + data))

            except Exception as e:
                print(e)
                await self.bot.say("Could not reroll")

def setup(bot):
    bot.add_cog(Add(bot))
