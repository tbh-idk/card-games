# card-games
Games currently supported:
 - BlackJack (2-7 players)
 - Go Fish (2-5 players)
 - Crazy 8s (2-4 players)
 - Tic-Tac-Toe (2 players)
 - Idiot (2-4 players)
 - Hearts (4 players)

## BlackJack
- the goal of the game is to reach 21 points
- numerical cards are worth the same as their number
- face cards are worth 10
- ace is worth either 1 or 11

## Go Fish
- the goal of the game is to be the first to get rid of your cards by collecting all 4 cards of the same value
- each turn you chose a person and ask for a card. they give you the card if they have it, else you draw a random card from the deck
- there are no repeated turns

## Crazy 8s
- the goal of the game is to get rid of your cards first
- you can play cards if it is the same value or suit as the top discard
- 8s can be placed on any card, and can change the suit
- queens skip the next persons turn
- 2s have the next person draw two

## Tic-Tac-Toe
- the goal of the game is to have three in a row, either horizontal, vertical, or diagonal
- navigate to an open square using ➡️ ⬆️ ↗️ ↘️
- place holder is 🟨, and starts on the most recently placed symbol
- press ✔️ to confirm

## Idiot
- the goal of the game is to get rid of your cards first
- on each turn you must place a card (or multiple cards of the same value) that is of the same of greater value as the top discard (ace high)
- if a player cannot play a legal move, they take the discard pile
- 2s can be placed on any card and reset the pile, anything can be placed on a 2
- 5s can be placed on any card, and only cards less than 5 can be placed on top
- 10s can be placed on any card, and the discard pile is removed
- once the deck runs out and there are no cards in a players hand, they move to their face up cards
- the same rules apply, and if they cannot play a card, they take the discard pile
- once a players face up cards are played, they move onto the face down cards
- the same rules apply, but a player does not know what the card is before it is played

## Hearts
- trick taking game
- player with the two of clubs (2♣) starts the first trick
- player who placed the card with the highest rank of the leading suit takes the trick and leads the next trick
- rank order (low to high): 2 3 4 5 6 7 8 9 10 J Q K A
- each card of the hearts in the trick taken suit earns the player one point
- the queen of spades (Q♠) earns the trick taker 13 points
- the first player to reach a certain threshold (usually 100 or 200) loses the game


-----------
### Notes
This is in the process of being refactored...
