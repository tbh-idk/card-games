
"""
 - a bot that can host card games, such as
   - BlackJack
   - GoldFish
   - Crazy Eights
   - Idiot
   - Spoons (?)
   - Old Maid (?)
"""

import discord
from discord import Option, OptionChoice, Intents, Embed, SelectOption
from discord.ext import commands
from discord.ui import Button, Select, Modal, InputText, View
import asyncio

from botHelper2 import WAIT_BEFORE_GAME_STARTS
from botHelper2 import Card, Deck, Value, Suit

import os
from dotenv import load_dotenv
from math import prod

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(intents=intents)


@bot.slash_command(name="blackjack", 
                   description="Play a game of blackjack!")
async def BlackJack(ctx, 
                    decks: Option(int, "How many decks to use?", required=False, default=1)):

    async def wait_until(conditon, timeout=30, timeoutMessage=""): #, **kwargs
        nonlocal gameThread, gameThreadMembers, revealHandClicked, standPlayers
        count = 0
        while not(conditon()) and count<timeout:
            await asyncio.sleep(1)
            count += 1
        if count>=timeout and timeoutMessage: #time out clause
            await gameThread.send(timeoutMessage)

    channel = ctx.channel
    gameThread = await channel.create_thread(name=f"BlackJack {ctx.interaction.id}")
    gameThreadMembers = []
    # await gameThread.add_user(ctx.author)

    async def joinGameButtonCallback(interaction):
        nonlocal gameThread
        await gameThread.add_user(interaction.user)
        await interaction.response.send_message("Added you to game!", ephemeral=True)
    joinGameEmbed = Embed(title="Join a game of BlackJack",
                          description="Standard BlackJack rules. 1-7 players",
                          color=int("db0707", 16))
    joinGameButton = Button(label="Join",
                            style=discord.ButtonStyle.green)
    joinGameButton.callback = joinGameButtonCallback
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    joinGameMessage = await ctx.respond(embed=joinGameEmbed, view=joinGameView)

    await wait_until(lambda: gameThread.member_count-1 >= 7, WAIT_BEFORE_GAME_STARTS)

    joinGameButton.disabled = True
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    await joinGameMessage.edit_original_response(embed=joinGameEmbed, view=joinGameView)
    await gameThread.send("game to begin shortly")

    DECK = Deck(decks)

    gameThreadMembers = await gameThread.fetch_members()
    WINNERS_COUNT = {}
    for m in gameThreadMembers:
        if m.id == 1078119044240130108:
            gameThreadMembers.remove(m)
            continue
        WINNERS_COUNT[m.id] = 0

    
    while len(DECK) > len(gameThreadMembers) * 2:
        playerHands = {}
        for p in gameThreadMembers:
            playerHands[p.id] = [DECK.draw()] 
        for p in gameThreadMembers:
            playerHands[p.id].append(DECK.draw())

        revealHandClicked = set([])
        async def revealHandCallback(interaction):
            nonlocal revealHandClicked
            await interaction.response.send_message(f"{', '.join(str(card) for card in playerHands[interaction.user.id])} | Sum: {tuple(Card.Sum(*playerHands[interaction.user.id]))}", 
                                                    ephemeral=True)
            revealHandClicked.add(interaction.user.id)
        revealHandButton = Button(label="See hand",
                                style=discord.ButtonStyle.blurple)
        revealHandButton.callback = revealHandCallback
        revealHandView = View()
        revealHandView.add_item(revealHandButton)

        await gameThread.send("Click to see hand", view=revealHandView)

        await wait_until(lambda: len(revealHandClicked) == len(gameThreadMembers), 30)

        standPlayers = set()
        async def actionButtonHitCallback(interaction):
            if len(DECK) > 0:
                if not(interaction.user.id in standPlayers):
                    # print(playerHands[interaction.user.id])
                    if len(DECK) != 0: playerHands[interaction.user.id].append(DECK.draw())
                    # print(playerHands[interaction.user.id])
                    await interaction.response.send_message(f"{', '.join(str(card) for card in playerHands[interaction.user.id])} | Sum: {tuple(Card.Sum(*playerHands[interaction.user.id]))}", 
                                                            ephemeral=True)
                else:
                    await interaction.response.send_message(f"you cannot hit after you stand", ephemeral=True)
            else:
                await interaction.response.send_message(f"there are no more cards in the deck")
                for m in gameThreadMembers:
                    standPlayers.add(m.id)
        async def actionButtonStandCallback(interaction):
            nonlocal standPlayers
            standPlayers.add(interaction.user.id)
            await interaction.response.send_message(f"{interaction.user} stand")
        actionButtonHit = Button(label="Hit",
                                style=discord.ButtonStyle.green)
        actionButtonStand = Button(label="Stand",
                                style=discord.ButtonStyle.red)
        actionButtonHit.callback = actionButtonHitCallback
        actionButtonStand.callback = actionButtonStandCallback
        actionButtonView = View()
        actionButtonView.add_item(actionButtonHit)
        actionButtonView.add_item(actionButtonStand)

        await gameThread.send(view=actionButtonView)
        await wait_until(lambda: len(standPlayers) == len(gameThreadMembers), 600)

        playerScores = {}
        for m in gameThreadMembers:
            bestScore = Card.Sum(*playerHands[m.id])[0]
            for s in Card.Sum(*playerHands[m.id]):
                if s <= 21: bestScore = s
            await gameThread.send(f"{bot.get_user(m.id)}: {bestScore} | {', '.join(list(map(str, playerHands[m.id])))}")
            playerScores[m.id] = bestScore
        
        winner = {0:0}
        for p in playerScores:
            if playerScores[p] > list(winner.values())[0] and playerScores[p] <= 21:
                winner = {p:playerScores[p]}
            elif playerScores[p] == list(winner.values())[0]:
                winner[p] = playerScores[p]
        
        # if 0 not in winner:
        #     await gameThread.send(f"WINNER{'S' if len(winner) > 1 else ''}")
        #     for p in winner:
        #         await gameThread.send(f"{bot.get_user(p)}")
        #         WINNERS_COUNT[p] += 1
        # else:
        #     await gameThread.send(f"no winners")
        winnerEmbed = Embed(color=int("210201", 16))
        if 0 not in winner:
            winnerEmbed.title = (f"WINNER{'S' if len(winner) > 1 else ''}")
            for p in winner:
                winnerEmbed.add_field(name=f"{bot.get_user(p)}",
                                      value=f"{winner[p]}",
                                      inline=False)
                WINNERS_COUNT[p] += 1
        else:
            winnerEmbed.title = (f"no winners")
        await gameThread.send(embed=winnerEmbed)
    
    await gameThread.send(f"no more cards")
    # await gameThread.send(f"WINNER COUNT")
    # await gameThread.send("\n".join(f"{bot.get_user(x)}: {WINNERS_COUNT[x]}" for x in WINNERS_COUNT))
    winnerCountEmbed = Embed(title="WIN COUNT",
                             color=int("210201", 16))
    for x in WINNERS_COUNT:
        winnerCountEmbed.add_field(name=f"{bot.get_user(x)}",
                                   value=f"\t{WINNERS_COUNT[x]}", 
                                   inline=False)
    await gameThread.send(embed=winnerCountEmbed)

    await gameThread.archive(True)






@bot.slash_command(name="go_fish",
                   description="Play a game of Go Fish!",
                   guild_ids=[901191055028936774]) #
async def GoldFish(ctx):
    async def wait_until(conditon, timeout=30, timeoutMessage=""):
        nonlocal gameThread, gameThreadMembers, currentInteraction, previousInteraction, revealHandClicked#, playerInteraction
        count = 0
        while not(conditon()) and count<timeout:
            await asyncio.sleep(1)
            count += 1
        if count>=timeout and timeoutMessage: #time out clause
            await gameThread.send(timeoutMessage)
        if count>=timeout: return False
        else: return True

    channel = ctx.channel
    gameThread = await channel.create_thread(name=f"GoFish {ctx.interaction.id}")
    gameThreadMembers = []
    # await gameThread.add_user(ctx.author)

    async def joinGameButtonCallback(interaction):
        nonlocal gameThread
        gameThreadMembers.append(interaction.user)
        await gameThread.add_user(interaction.user)
        await interaction.response.send_message("Added you to game!", ephemeral=True)
    joinGameEmbed = Embed(title="Join a game of GoFish",
                          description="Standard GoFish rules. 2-5 players",
                          color=int("4287f5", 16))
    joinGameButton = Button(label="Join",
                            style=discord.ButtonStyle.green)
    joinGameButton.callback = joinGameButtonCallback
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    joinGameMessage = await ctx.respond(embed=joinGameEmbed, view=joinGameView)

    await wait_until(lambda: len(gameThreadMembers) >= 5 and len(gameThreadMembers) >= 2, WAIT_BEFORE_GAME_STARTS)
    if len(gameThreadMembers) == 1:
        joinGameButton.disabled = True
        await gameThread.send(f"not enough people\n{gameThread.member_count}")
        await gameThread.archive(True)
        return

    ## TODO: see if it works
    joinGameButton.disabled = True
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    await joinGameMessage.edit_original_response(embed=joinGameEmbed, view=joinGameView)
    await gameThread.send("game to begin shortly")

    DECK = Deck()

    gameThreadMembers = await gameThread.fetch_members()
    for m in gameThreadMembers:
        if m.id == 1078119044240130108:
            gameThreadMembers.remove(m)
            continue
    gameThreadMembers = list(set(gameThreadMembers))
    
    previousInteraction = {}
    currentInteraction = {}

    async def readyButtonCallback(interaction):
        currentInteraction[interaction.user.id] = interaction
        await interaction.response.defer()
    readyButton = Button(label="Ready", 
                         style=discord.ButtonStyle.gray)
    readyButton.callback = readyButtonCallback
    readyView = View()
    readyView.add_item(readyButton)
    await gameThread.send(view=readyView)

    ready = await wait_until(lambda: len(currentInteraction) == len(gameThreadMembers))
    if not(ready):
        await gameThread.send("not everyone is ready")
        await gameThread.archive(True)
        return

    playerHands = {}
    for m in gameThreadMembers:
        playerHands[m.id] = {"hand":[DECK.draw()], "revealed":[]}
    for _ in range(6):
        for m in gameThreadMembers:
            playerHands[m.id]["hand"].append(DECK.draw())
    
    previousInteraction = currentInteraction
    revealHandClicked = set([])
    async def revealHandCallback(interaction):
        nonlocal revealHandClicked, previousInteraction, currentInteraction
        currentInteraction[interaction.user.id] = interaction
        interaction = previousInteraction[interaction.user.id]
        await interaction.response.send_message(f"{', '.join(str(card) for card in Card.Sort(Value, *playerHands[interaction.user.id]['hand']))}", 
                                                ephemeral=True)
        #await interaction.followup.send("hi", ephemeral=True)
        revealHandClicked.add(interaction.user.id)
        # playerInteraction[interaction.user.id] = interaction
    revealHandButton = Button(label="See hand",
                            style=discord.ButtonStyle.blurple)
    revealHandButton.callback = revealHandCallback
    revealHandView = View()
    revealHandView.add_item(revealHandButton)

    await gameThread.send("Click to see hand", view=revealHandView)

    await wait_until(lambda: len(revealHandClicked) == len(gameThreadMembers), 30)      

    chosenRecipient = "" # type threadMember
    async def askRecipientCallback(interaction):
        nonlocal currentInteraction, chosenRecipient
        currentInteraction[interaction.user.id] = interaction
        chosenRecipient = askRecipient.values[0]
        interaction = await interaction.response.defer()
    chosenCard = "" # type Value
    async def askCardCallback(interaction):
        nonlocal currentInteraction, chosenCard
        currentInteraction[interaction.user.id] = interaction
        chosenCard = askCard.values[0]
        interaction = await interaction.response.defer()

    def revealQuads(p):
        cardCount = dict()
        for c in playerHands[p]['hand']:
            if c.getValue() in cardCount:
                cardCount[c.getValue()] += 1
            else:
                cardCount[c.getValue()] = 1
        for v in cardCount:
            if cardCount[v] == 4:
                for c in playerHands[p]['hand'].copy():
                    if c.getValue() == v:
                        playerHands[p]['revealed'].append(c)
                        playerHands[p]['hand'].remove(c)

    playing = True
    while playing: # while game can continue
        for p in playerHands: #m.id

            playerEmbedDict = {}
            for P in playerHands:
                    playerEmbedDict[P] = Embed(title=bot.get_user(P),
                        description=(("🂠 "*len(playerHands[P]["hand"]) + " | " + (", ".join(str(playerHands[P]["revealed"][card].getValue()) for card in range(0, len(playerHands[P]["revealed"]), 4))))))
            await gameThread.send(embeds=list(playerEmbedDict.values())) 

            chosenRecipient = ""
            chosenCard = ""

            askRecipient = Select()
            for m in gameThreadMembers: 
                if m.id != p: askRecipient.add_option(label=str(bot.get_user(m.id)), value=f"{m.id}")

            askRecipient.callback = askRecipientCallback
            askCard = Select()
            # for c in set(Card.Sort(*(playerHands[p]["hand"]))): askCard.add_option(label=str(c.getValue()), value=f"{c.getValue()}")
            for c in sorted(set(card.getValue() for card in playerHands[p]["hand"]), key = lambda card: (list(Value).index(card))): askCard.add_option(label=str(c), value=f"{c}")
            askCard.callback = askCardCallback
            askViewRecipient = View()
            askViewRecipient.add_item(askRecipient)
            askViewCard = View()
            askViewCard.add_item(askCard)
            # print(str([x.value for x in askRecipient.options])+"\n"+str([x.value for x in askCard.options]))
            # print(previousInteraction[p])
            await previousInteraction[p].followup.send(f"{', '.join(str(card) for card in Card.Sort(Value, *playerHands[previousInteraction[p].user.id]['hand']))}\nWho do you to take from?", view=askViewRecipient, ephemeral=True)
            await wait_until(lambda: chosenRecipient != "")

            await previousInteraction[p].followup.send(f"What card do you want?", view=askViewCard, ephemeral=True)
            await wait_until(lambda: chosenCard != "")

            await gameThread.send(f"<@{p}> asks <@{chosenRecipient}> for {chosenCard}")

            print("\n")
            print(playerHands)
            # print(chosenCard)
            # print(playerHands[int(chosenRecipient)])
            if chosenCard in [str(card.getValue()) for card in playerHands[int(chosenRecipient)]['hand']]:
                cardsTransferred = []
                for c in playerHands[int(chosenRecipient)]['hand'].copy():
                    if str(c.getValue()) == chosenCard:
                        cardsTransferred.append(c)
                        playerHands[int(chosenRecipient)]['hand'].remove(c)
                playerHands[p]['hand'].extend(cardsTransferred)
                revealQuads(p) # reveal groups of 4
                await gameThread.send(f"<@{chosenRecipient}> has {chosenCard}")
            else:
                if len(DECK) != 0: playerHands[p]['hand'].append(DECK.draw())
                revealQuads(p)
                await gameThread.send(f"<@{chosenRecipient}> hasnt {chosenCard}. {'go fish' if len(DECK) != 0 else 'no cards left to draw'}")
            
            # await gameThread.send("", view=revealHandView)

            if prod(len(playerHands[P]["hand"]) for P in playerHands) == 0: 
                playing = False
                break
                
        
        previousInteraction = currentInteraction
    
    quadsRevealed = dict()
    for p in playerHands:
        quadsRevealed[p] = len(playerHands[p]['revealed'])
    print(quadsRevealed)
    winners = dict()
    for p in quadsRevealed:
        if quadsRevealed[p] in winners.keys():
            winners[quadsRevealed[p]].append(p)
        else:
             winners[quadsRevealed[p]] = [p]
    winners = dict()
    print(winners)
    
    winnerEmbed = Embed(color=int("210201", 16))
    winnerEmbed.title = (f"WINNER{'S' if len(winners) > 1 else ''}")
    for p in winners[max(winners.keys())]:
        winnerEmbed.add_field(name=f"{bot.get_user(p)}",
                                value=f"{max(winners.keys())} quads completed",
                                inline=False)
    await gameThread.send(embed=winnerEmbed)

    await gameThread.archive(True)






@bot.slash_command(name="crazy8s",
                   description="Play a game of Crazy Eights!",
                   guild_ids=[901191055028936774])
async def CrazyEights(ctx):
    async def wait_until(conditon, timeout=30, timeoutMessage=""):
        nonlocal gameThread, gameThreadMembers, currentInteraction, previousInteraction, revealHandClicked#, playerInteraction
        count = 0
        while not(conditon()) and count<timeout:
            await asyncio.sleep(1)
            count += 1
        if count>=timeout and timeoutMessage: #time out clause
            await gameThread.send(timeoutMessage)
        if count>=timeout: return False
        else: return True

    channel = ctx.channel
    gameThread = await channel.create_thread(name=f"Crazy8s {ctx.interaction.id}")
    gameThreadMembers = []
    # await gameThread.add_user(ctx.author)

    async def joinGameButtonCallback(interaction):
        nonlocal gameThread
        gameThreadMembers.append(interaction.user)
        await gameThread.add_user(interaction.user)
        await interaction.response.send_message("Added you to game!", ephemeral=True)
    joinGameEmbed = Embed(title="Join a game of Crazy Eights!",
                          description="Standard Crazy Eights rules. 2-4 players",
                          color=int("f5a142", 16))
    joinGameButton = Button(label="Join",
                            style=discord.ButtonStyle.green)
    joinGameButton.callback = joinGameButtonCallback
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    joinGameMessage = await ctx.respond(embed=joinGameEmbed, view=joinGameView)

    await wait_until(lambda: len(gameThreadMembers) >= 4 and len(gameThreadMembers) >= 2, WAIT_BEFORE_GAME_STARTS)
    if len(gameThreadMembers) == 1:
        joinGameButton.disabled = True
        await gameThread.send(f"not enough people\n{gameThread.member_count}")
        await gameThread.archive(True)
        return
    
    joinGameButton.disabled = True
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    await joinGameMessage.edit_original_response(embed=joinGameEmbed, view=joinGameView)
    await gameThread.send("game to begin shortly")

    DECK = Deck()

    gameThreadMembers = await gameThread.fetch_members()
    for m in gameThreadMembers:
        if m.id == 1078119044240130108:
            gameThreadMembers.remove(m)
            continue
    gameThreadMembers = list(set(gameThreadMembers))
    
    previousInteraction = {}
    currentInteraction = {}

    async def readyButtonCallback(interaction):
        currentInteraction[interaction.user.id] = interaction
        await interaction.response.defer()
    readyButton = Button(label="Ready", 
                         style=discord.ButtonStyle.gray)
    readyButton.callback = readyButtonCallback
    readyView = View()
    readyView.add_item(readyButton)
    await gameThread.send(view=readyView)

    ready = await wait_until(lambda: len(currentInteraction) == len(gameThreadMembers))
    if not(ready):
        await gameThread.send("not everyone is ready")
        await gameThread.archive(True)
        return

    playerHands = {}
    for m in gameThreadMembers:
        playerHands[m.id] = [DECK.draw()]
    for _ in range(7):
        for m in gameThreadMembers:
            playerHands[m.id].append(DECK.draw())
    
    previousInteraction = currentInteraction
    revealHandClicked = set([])
    async def revealHandCallback(interaction):
        nonlocal revealHandClicked, previousInteraction, currentInteraction
        currentInteraction[interaction.user.id] = interaction
        interaction = previousInteraction[interaction.user.id]
        await interaction.response.send_message(f"{', '.join(str(card) for card in Card.Sort(Suit, *playerHands[interaction.user.id]))}", 
                                                ephemeral=True)
        #await interaction.followup.send("hi", ephemeral=True)
        revealHandClicked.add(interaction.user.id)
        # playerInteraction[interaction.user.id] = interaction
    revealHandButton = Button(label="See hand",
                            style=discord.ButtonStyle.blurple)
    revealHandButton.callback = revealHandCallback
    revealHandView = View()
    revealHandView.add_item(revealHandButton)

    await gameThread.send("Click to see hand", view=revealHandView)

    await wait_until(lambda: len(revealHandClicked) == len(gameThreadMembers), 30)


    chosenCard = "" # type CARD
    async def askCardCallback(interaction):
        nonlocal currentInteraction, chosenCard
        currentInteraction[interaction.user.id] = interaction
        chosenCard = askCard.values[0]
        interaction = await interaction.response.defer()
    newSuit = "" # type Suit
    async def suitSelectCallback(interaction):
        nonlocal currentInteraction, newSuit
        currentInteraction[interaction.user.id] = interaction
        newSuit = suitSelect.values[0]
        interaction = await interaction.response.defer()

    # [x] 8 (change suit)
    # [x] Q (skip)
    # [ ] A (reverse)
    # [ ] 2 (draw two)
    topCard = DECK.draw()
    topSuit = topCard.getSuit()
    topValue = topCard.getValue()
    playing = True
    await gameThread.send(f"top card is {topCard}")
    while playing:
        for p in playerHands:

            if chosenCard and chosenCard.getValue() == Value.QUEEN:
                await gameThread.send(f"<@{p}>'s turn is skipped")
                chosenCard = ""
                newSuit = ""
                continue

            playerEmbedDict = {}
            for P in playerHands:
                    playerEmbedDict[P] = Embed(title=bot.get_user(P),
                        description=("🂠 "*len(playerHands[P])))
            await gameThread.send(embeds=list(playerEmbedDict.values()))

            chosenCard = ""
            newSuit = ""

            askCard = Select()
            for card in playerHands[p]:
                if (topValue != Value.EIGHT and (card.getValue() == Value.EIGHT or card.getValue() == topValue or card.getSuit() == topSuit)) or (topValue == Value.EIGHT and str(card.getSuit()) == topSuit):
                    askCard.add_option(label=str(card), value=f"{card}")
            askCard.callback = askCardCallback
            askCardView = View()
            askCardView.add_item(askCard)

            if len(askCard.options) != 0: 
                await previousInteraction[p].followup.send(f"{', '.join(str(card) for card in Card.Sort(Suit, *playerHands[previousInteraction[p].user.id]))}\nChose a card to play", view=askCardView, ephemeral=True)
            else: 
                await previousInteraction[p].followup.send("Cannot play a card")
                playerHands[p].append(DECK.draw())
                chosenCard = None

            await wait_until(lambda: chosenCard != "")
            
            if chosenCard:
                for c in playerHands[p]: 
                    if (str(c) == chosenCard):
                        chosenCard = c
                        playerHands[p].remove(c)
                    else:
                        pass
                topSuit = chosenCard.getSuit()
                topValue = chosenCard.getValue()
                await gameThread.send(f"<@{p}> plays a {str(chosenCard)}")

                if chosenCard.getValue() == Value.EIGHT:
                    # print(chosenCard.getSuit())
                    suitSelect = Select()
                    suitSelect.callback = suitSelectCallback
                    for s in list(Suit): 
                        # print(f"{s}")
                        suitSelect.add_option(label=str(s), value=str(s))
                    suitSelectView = View()
                    suitSelectView.add_item(suitSelect)
                    await previousInteraction[p].followup.send("Chose a suit to change to", view=suitSelectView, ephemeral=True)
                    await wait_until(lambda: newSuit != "")

                    topSuit = newSuit
                    await gameThread.send(f"<@{p}> changed the suit to {newSuit}")

                    # for s in playerHands[p]:
                        # print(f"{s}: {s.getSuit()} == {topSuit}\t{type(s.getSuit())} -- {type(topSuit)}\t{s.getSuit() == topSuit}")

            # await gameThread.send("", view=revealHandView)

            if prod(len(playerHands[P]) for P in playerHands) == 0: 
                playing = False
                break 
        
        for p in playerHands:
            if len(playerHands[P]) == 0:
                await gameThread.send(f"<@{P}> won this round")






@bot.slash_command(name="tic-tac-toe",
                   description="Play a game of Tic- Tac-Toe!",
                   guild_ids=[901191055028936774])
async def TicTacToe(ctx):
    async def wait_until(conditon, timeout=30, timeoutMessage=""): #, **kwargs
        nonlocal gameThread, gameThreadMembers
        count = 0
        while not(conditon()) and count<timeout:
            await asyncio.sleep(1)
            count += 1
        if count>=timeout and timeoutMessage: #time out clause
            await gameThread.send(timeoutMessage)
        if count>=timeout: return False
        else: return True

        

    channel = ctx.channel
    gameThread = await channel.create_thread(name=f"TicTacToe {ctx.interaction.id}")
    gameThreadMembers = []
    # await gameThread.add_user(ctx.author)

    async def joinGameButtonCallback(interaction):
        nonlocal gameThread
        gameThreadMembers.append(interaction.user.id)
        await gameThread.add_user(interaction.user)
        await interaction.response.send_message("Added you to game!", ephemeral=True)
    joinGameEmbed = Embed(title="Join a game of Tic- Tac-Toe",
                          description="Standard Tic- Tac-Toe rules. 2 players",
                          color=int("015e0f", 16))
    joinGameButton = Button(label="Join",
                            style=discord.ButtonStyle.green)
    joinGameButton.callback = joinGameButtonCallback
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    joinGameMessage = await ctx.respond(embed=joinGameEmbed, view=joinGameView)

    await wait_until(lambda: len(gameThreadMembers) == 2, WAIT_BEFORE_GAME_STARTS)
    joinGameButton.disabled = True
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    await joinGameMessage.edit_original_response(embed=joinGameEmbed, view=joinGameView)
    if len(gameThreadMembers) == 1:
        joinGameButton.disabled = True
        await gameThread.send(f"not enough people\n{gameThread.member_count}")
        await gameThread.archive(True)
        return
    
    previousInteraction = {}
    currentInteraction = {}
    
    async def readyButtonCallback(interaction):
        currentInteraction[interaction.user.id] = interaction
        await interaction.response.defer()
    readyButton = Button(label="Ready", 
                         style=discord.ButtonStyle.gray)
    readyButton.callback = readyButtonCallback
    readyView = View()
    readyView.add_item(readyButton)
    await gameThread.send(view=readyView)

    ready = await wait_until(lambda: len(currentInteraction) == len(gameThreadMembers))
    if not(ready):
        await gameThread.send("not everyone is ready")
        await gameThread.archive(True)
        return

    ####

    board = [[None,None,None],[None,'.',None],[None,None,None]]
    position = [1,1] # [i,j]
    # 0 1 2
    # 1  
    # 2 

    def boardToEmoji():
        emojis = ""
        for i in range(len(board)):
            for j in range(len(board)):
                if board[i][j] == None: emojis += "⬛ "
                if board[i][j] == 'O': emojis += "⭕ "
                if board[i][j] == 'X': emojis += "❌ "
                if board[i][j] == '.': emojis += "🟨 "
            emojis += "\n"

        return emojis

    TTTBoard = Embed(title="Tic-Tac-Toe game")
    TTTBoard.add_field(name="", value=boardToEmoji())
    TTTBoardMessage = await gameThread.send(embed=TTTBoard)

    async def updateBoard():
        nonlocal TTTBoardMessage
        TTTBoard.remove_field(0)
        TTTBoard.add_field(name="", value=boardToEmoji())
        TTTBoardMessage = await TTTBoardMessage.edit(embed=TTTBoard)


    async def leftButtonCallback(interaction):
        nonlocal position, board
        print('left')
        # prev = board[position[0]][position[1]]
        newPosition = [position[0], (position[1] + 2)%3]
        if board[newPosition[0]][newPosition[1]] != None:
            newPosition = [position[0], (position[1] + 1)%3]
            if board[newPosition[0]][newPosition[1]] != None:
                return
        if board[position[0]][position[1]] == '.': board[position[0]][position[1]] = None
        position = newPosition
        board[position[0]][position[1]] = '.'
        await updateBoard()
        await interaction.response.defer()
    async def rightButtonCallback(interaction):
        nonlocal position, board
        print('right')
        # prev = board[position[0]][position[1]]
        newPosition = [position[0], (position[1] + 1)%3]
        if board[newPosition[0]][newPosition[1]] != None:
            newPosition = [position[0], (position[1] + 2)%3]
            if board[newPosition[0]][newPosition[1]] != None:
                return
        if board[position[0]][position[1]] == '.': board[position[0]][position[1]] = None        
        position = newPosition
        board[position[0]][position[1]] = '.'
        await updateBoard()
        await interaction.response.defer()
    async def upButtonCallback(interaction):
        nonlocal position, board
        print('up')
        # prev = board[position[0]][position[1]]
        newPosition = [(position[0] + 2)%3, position[1]]
        if board[newPosition[0]][newPosition[1]] != None:
            newPosition = [(position[0] + 1)%3, position[1]]
            if board[newPosition[0]][newPosition[1]] != None:
                return
        if board[position[0]][position[1]] == '.': board[position[0]][position[1]] = None
        position = newPosition
        board[position[0]][position[1]] = '.'
        await updateBoard()
        await interaction.response.defer()
    async def downButtonCallback(interaction):
        nonlocal position, board
        print('down')
        # prev = board[position[0]][position[1]]
        newPosition = [(position[0] + 1)%3, position[1]]
        if board[newPosition[0]][newPosition[1]] != None:
            newPosition = [(position[0] + 2)%3, position[1]]
            if board[newPosition[0]][newPosition[1]] != None:
                return
        if board[position[0]][position[1]] == '.': board[position[0]][position[1]] = None
        position = newPosition
        board[position[0]][position[1]] = '.'
        await updateBoard()
        await interaction.response.defer()
    async def upperRightButtonCallback(interaction):
        nonlocal position, board
        print('upperRight')
        newPosition = [(position[0] + 2)%3, (position[1] + 1)%3]
        if board[newPosition[0]][newPosition[1]] != None:
            newPosition = [(position[0] + 1)%3, (position[1] + 2)%3]
            if board[newPosition[0]][newPosition[1]] != None:
                return
        if board[position[0]][position[1]] == '.': board[position[0]][position[1]] = None
        position = newPosition
        board[position[0]][position[1]] = '.'
        await updateBoard()
        await interaction.response.defer()
    async def lowerRightButtonCallback(interaction):
        nonlocal position, board
        print('upperRight')
        newPosition = [(position[0] + 1)%3, (position[1] + 1)%3]
        if board[newPosition[0]][newPosition[1]] != None:
            newPosition = [(position[0] + 2)%3, (position[1] + 2)%3]
            if board[newPosition[0]][newPosition[1]] != None:
                return
        if board[position[0]][position[1]] == '.': board[position[0]][position[1]] = None
        position = newPosition
        board[position[0]][position[1]] = '.'
        await updateBoard()
        await interaction.response.defer()
    async def selectButtonCallback(interaction):
        print('ok\n')
        if board[position[0]][position[1]] == '.':
            nonlocal turnFinish
            turnFinish = True
            await interaction.response.defer()
        else: return

    leftButton = Button(label="⬅️")
    leftButton.callback = leftButtonCallback
    rightButton = Button(label="➡️")
    rightButton.callback = rightButtonCallback
    upButton = Button(label="⬆️")
    upButton.callback = upButtonCallback
    downButton = Button(label="⬇️")
    downButton.callback = downButtonCallback
    upperRightButton = Button(label="↗️")
    upperRightButton.callback = upperRightButtonCallback
    lowerRightButton = Button(label="↘️")
    lowerRightButton.callback = lowerRightButtonCallback
    selectButton = Button(label="✅")
    selectButton.callback = selectButtonCallback

    chooseSpotView = View()
    # chooseSpotView.add_item(leftButton)
    chooseSpotView.add_item(rightButton)
    chooseSpotView.add_item(upButton)
    # chooseSpotView.add_item(downButton)
    chooseSpotView.add_item(upperRightButton)
    chooseSpotView.add_item(lowerRightButton)
    chooseSpotView.add_item(selectButton)
    chooseSpotView.disable_all_items()

    symbols = ['O','X']
    controlMessage = dict()
    turnFinish = False
    for p in gameThreadMembers:
        # print(p)
        # print(p.id)
        controlMessage[p] = await currentInteraction[p].followup.send(f"You are {symbols[gameThreadMembers.index(p)]}. \nNot your turn", view=chooseSpotView, ephemeral=True)

    def gameOver():
        nonlocal board
        # check row
        if not(None in [item for r in board for item in r]): return [True, None]
        for i in range(len(board)):
            if board[i][0] != None and board[i][0] == board[i][1] and board[i][1] == board[i][2]: return [True, board[i][0]]
        # check column
        for j in range(len(board)):
            if board[0][j] != None and board[0][j] == board[1][j] and board[1][j] == board[2][j]: return [True, board[0][j]]
        # check diagonal
        if board[0][0] != None and board[0][0] == board[1][1] and board[1][1] == board[2][2]: return [True, board[0][0]]
        if board[2][0] != None and board[2][0] == board[1][1] and board[1][1] == board[0][2]: return [True, board[2][0]]

        return [False]
    playing = True
    while playing:
        for p in gameThreadMembers:
            turnFinish = False
            chooseSpotView.enable_all_items()
            controlMessage[p] = await controlMessage[p].edit(f"You are {symbols[gameThreadMembers.index(p)]}. \nYour turn", view=chooseSpotView) #, ephemeral=True

            await wait_until(lambda: turnFinish)
            # print(turnFinish)
            board[position[0]][position[1]] = symbols[gameThreadMembers.index(p)]
            await updateBoard()

            chooseSpotView.disable_all_items()
            controlMessage[p] = await controlMessage[p].edit(f"You are {symbols[gameThreadMembers.index(p)]}. \nNot your turn", view=chooseSpotView) #, ephemeral=True

            if gameOver()[0]: 
                await gameThread.send("Game Over!")
                winner = gameOver()[1]
                if winner: await gameThread.send(f"{winner}'s (<@{gameThreadMembers[symbols.index(winner)]}>) won!")
                else: await gameThread.send("Draw!")
                playing = False
                await gameThread.archive(True)
                break

            if board[position[0]][(position[1] + 2)%3] != None and board[position[0]][(position[1] + 1)%3] != None and board[(position[0] + 2)%3][position[1]] != None and board[(position[0] + 1)%3][position[1]] != None:
                firstEmpty = [item for r in board for item in r].index(None)
                position = [firstEmpty//3, firstEmpty%3]






@bot.slash_command(name="idiot",
                   description="Play a game of Idiot!",
                   guild_ids=[901191055028936774])
async def Idiot(ctx):
    async def wait_until(conditon, timeout=30, timeoutMessage=""):
        nonlocal gameThread, gameThreadMembers, currentInteraction, previousInteraction, revealHandClicked#, playerInteraction
        count = 0
        while not(conditon()) and count<timeout:
            await asyncio.sleep(1)
            count += 1
        if count>=timeout and timeoutMessage: #time out clause
            await gameThread.send(timeoutMessage)
        if count>=timeout: return False
        else: return True

    channel = ctx.channel
    gameThread = await channel.create_thread(name=f"Idiot {ctx.interaction.id}")
    gameThreadMembers = []
    # await gameThread.add_user(ctx.author)

    async def joinGameButtonCallback(interaction):
        nonlocal gameThread
        gameThreadMembers.append(interaction.user)
        await gameThread.add_user(interaction.user)
        await interaction.response.send_message("Added you to game!", ephemeral=True)
    joinGameEmbed = Embed(title="Join a game of Idiot!",
                          description="Standard Idiot rules. 2-4 players",
                          color=int("f5a142", 16))
    joinGameButton = Button(label="Join",
                            style=discord.ButtonStyle.green)
    joinGameButton.callback = joinGameButtonCallback
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    joinGameMessage = await ctx.respond(embed=joinGameEmbed, view=joinGameView)

    await wait_until(lambda: len(gameThreadMembers) >= 4 and len(gameThreadMembers) >= 2, WAIT_BEFORE_GAME_STARTS)
    if len(gameThreadMembers) == 1:
        joinGameButton.disabled = True
        await gameThread.send(f"not enough people\n{gameThread.member_count}")
        await gameThread.archive(True)
        return
    
    joinGameButton.disabled = True
    joinGameView = View()
    joinGameView.add_item(joinGameButton)
    await joinGameMessage.edit_original_response(embed=joinGameEmbed, view=joinGameView)
    await gameThread.send("game to begin shortly")

    DECK = Deck()

    gameThreadMembers = await gameThread.fetch_members()
    for m in gameThreadMembers:
        if m.id == 1078119044240130108:
            gameThreadMembers.remove(m)
            continue
    gameThreadMembers = list(set(gameThreadMembers))
    
    previousInteraction = {}
    currentInteraction = {}

    async def readyButtonCallback(interaction):
        currentInteraction[interaction.user.id] = interaction
        await interaction.response.defer()
    readyButton = Button(label="Ready", 
                         style=discord.ButtonStyle.gray)
    readyButton.callback = readyButtonCallback
    readyView = View()
    readyView.add_item(readyButton)
    await gameThread.send(view=readyView)

    ready = await wait_until(lambda: len(currentInteraction) == len(gameThreadMembers))
    if not(ready):
        await gameThread.send("not everyone is ready")
        await gameThread.archive(True)
        return

    playerHands = {}
    for m in gameThreadMembers:
        playerHands[m.id] = {'hand':[DECK.draw()],'threeUp':[],'threeDown':[]}
    for _ in range(2):
        for m in gameThreadMembers:
            playerHands[m.id]['hand'].append(DECK.draw())

    previousInteraction = currentInteraction
    revealHandClicked = set([])
    async def revealHandCallback(interaction):
        nonlocal revealHandClicked, previousInteraction, currentInteraction
        currentInteraction[interaction.user.id] = interaction
        interaction = previousInteraction[interaction.user.id]
        await interaction.response.send_message(f"{', '.join(str(card) for card in Card.Sort(Value, *playerHands[interaction.user.id]['hand']))}", 
                                                ephemeral=True)
        #await interaction.followup.send("hi", ephemeral=True)
        revealHandClicked.add(interaction.user.id)
        # playerInteraction[interaction.user.id] = interaction
    revealHandButton = Button(label="See hand",
                            style=discord.ButtonStyle.blurple)
    revealHandButton.callback = revealHandCallback
    revealHandView = View()
    revealHandView.add_item(revealHandButton)

    await gameThread.send("Click to see hand", view=revealHandView)

    await wait_until(lambda: len(revealHandClicked) == len(gameThreadMembers), 30)

    ## swap face up cards

    async def askCards(p):
        nonlocal askCard, previousInteraction, playerHands, discards, chosenCard, topCard
        if len(askCard.options) != 0: 
            askCard.max_values = len(askCard.options) if len(askCard.options) <= 3 else 4
            shownHand = ""
            if playerHands[p]['hand']:
                shownHand = ', '.join(str(card) for card in Card.Sort(Value, *playerHands[p]['hand']))
            elif playerHands[p]['threeUp']:
                shownHand = ', '.join(str(card) for card in Card.Sort(Value, *playerHands[p]['threeUp']))
            elif playerHands[p]['threeDown']:
                shownHand = ', '.join('🂠'*len(playerHands[p]['threeDown']))
            await previousInteraction[p].followup.send(f"{shownHand}\n", view=askCardView, ephemeral=True)
        else: 
            await previousInteraction[p].followup.send("Cannot play a card")
            playerHands[p]['hand'].extend(discards)
            discards.clear()
            chosenCard = None
            topCard = ""
    chosenCard = "" # type CARD
    async def askCardCallback(interaction):
        nonlocal currentInteraction, chosenCard
        currentInteraction[interaction.user.id] = interaction
        print(askCard.values)
        if len(set([c[0] for c in askCard.values])) == 1:
            # print(set([c[0] for c in askCard.values])) 
            chosenCard = askCard.values
            interaction = await interaction.response.defer()
        else: 
            # print(f"{set([c[0] for c in askCard.values])}\t{len(set([c[0] for c in askCard.values]))}")
            # interaction = await interaction.response.defer()
            askCard.placeholder = "Multiple cards must match value"
            await askCards(interaction.user.id)
        

    playing = True
    topCard = ""
    valList = [*list(Value)[1:],list(Value)[0]]
    discards = list()
    while playing:
        for p in playerHands:

            chosenCard = []

            if type(topCard) == Card:
                topValue = topCard.getValue()
            elif topCard == "":
                topValue = None

            playerHands[p]['hand'] = Card.Sort(Value, *playerHands[p]['hand'])
            # print(playerHands[p]['hand'])


            askCard = Select()
            if playerHands[p]['hand']:
                if (topValue == None):
                    for card in playerHands[p]['hand']:
                        askCard.add_option(label=str(card), value=f"{card}")
                elif (topValue != Value.FIVE):
                    for card in playerHands[p]['hand']:
                        if valList.index(card.getValue()) >= valList.index(topValue) or card.getValue() == Value.TWO or card.getValue() == Value.FIVE or card.getValue() == Value.TEN:
                            askCard.add_option(label=str(card), value=f"{card}")
                elif (topValue == Value.FIVE):
                    for card in playerHands[p]['hand']:
                        if valList.index(card.getValue()) <= valList.index(topValue) or card.getValue() == Value.TWO or card.getValue() == Value.FIVE or card.getValue() == Value.TEN:
                            askCard.add_option(label=str(card), value=f"{card}")
            elif playerHands[p]['threeUp']:
                if (topValue == None):
                    for card in playerHands[p]['threeUp']:
                        askCard.add_option(label=str(card), value=f"{card}")
                elif (topValue != Value.FIVE):
                    for card in playerHands[p]['threeUp']:
                        if valList.index(card.getValue()) >= valList.index(topValue) or card.getValue() == Value.TWO or card.getValue() == Value.FIVE or card.getValue() == Value.TEN:
                            askCard.add_option(label=str(card), value=f"{card}")
                elif (topValue == Value.FIVE):
                    for card in playerHands[p]['threeUp']:
                        if valList.index(card.getValue()) <= valList.index(topValue) or card.getValue() == Value.TWO or card.getValue() == Value.FIVE or card.getValue() == Value.TEN:
                            askCard.add_option(label=str(card), value=f"{card}")
            elif playerHands[p]['threeDown']:
                pass
                # if (topValue == None):
                #     for card in playerHands[p]['threeDown']:
                #         askCard.add_option(label=str(card), value=f"{card}")
                # elif (topValue != Value.FIVE):
                #     for card in playerHands[p]['threeDown']:
                #         if valList.index(card.getValue()) >= valList.index(topValue) or card.getValue() == Value.TWO or card.getValue() == Value.FIVE or card.getValue() == Value.TEN:
                #             askCard.add_option(label=str(card), value=f"{card}")
                # elif (topValue == Value.FIVE):
                #     for card in playerHands[p]['threeDown']:
                #         if valList.index(card.getValue()) <= valList.index(topValue) or card.getValue() == Value.TWO or card.getValue() == Value.FIVE or card.getValue() == Value.TEN:
                #             askCard.add_option(label=str(card), value=f"{card}")
            askCard.placeholder = "Chose a card to play"
            askCard.callback = askCardCallback
            askCardView = View()
            askCardView.add_item(askCard)

            # if len(askCard.options) != 0: 
            #     askCard.max_values = len(askCard.options) if len(askCard.options) <= 3 else 4
            #     await previousInteraction[p].followup.send(f"{', '.join(str(card) for card in Card.Sort(Value, *playerHands[p]['hand']))}\nChose a card to play", view=askCardView, ephemeral=True)
            # else: 
            #     await previousInteraction[p].followup.send("Cannot play a card")
            #     playerHands[p]['hand'].extend(discards)
            #     discards.clear()
            #     chosenCard = None
            await askCards(p)

            await wait_until(lambda: chosenCard == None or len(chosenCard) != 0)

            if chosenCard:
                for c in playerHands[p]['hand'].copy():
                    if (str(c) in chosenCard):
                        chosenCard[chosenCard.index(str(c))] = c
                        playerHands[p]['hand'].remove(c)
                    else:
                        pass
                await gameThread.send(f"<@{p}> plays {','.join(str(c) for c in chosenCard)}")
                topCard = chosenCard[0]
                topValue = chosenCard[0].getValue()
                discards.extend(chosenCard)

                if topValue == Value.TEN: 
                    topCard = ""
                    topValue = None
                    discards.clear() 
                    await gameThread.send(f"<@{p}> bombed the discard pile")
           

            while len(playerHands[p]['hand']) < 3 and len(DECK) > 0:
                playerHands[p]['hand'].append(DECK.draw())
            
            if len(DECK) == 0:
                playing = False
                break


bot.run(TOKEN)
