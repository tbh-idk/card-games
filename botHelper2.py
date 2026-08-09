
"""
 - 

 CHANGE:
     WAIT_BEFORE_GAME_STARTS -> 60
"""

from enum import Enum, IntEnum
from random import shuffle as Shuffle

import asyncio

WAIT_BEFORE_GAME_STARTS = 10

class Suit(Enum):
    SPADES = "♠️"
    HEARTS = "♥️"
    DIAMONDS = "♦️"
    CLUBS = "♣️"
    def __str__(self):
        return(f"{self.name}")
    
class Value(Enum):
    ACE = "Ace"
    TWO = "Two"
    THREE = "Three"
    FOUR = "Four"
    FIVE = "Five"
    SIX = "Six"
    SEVEN = "Seven"
    EIGHT = "Eight"
    NINE = "Nine"
    TEN = "Ten"
    JACK = "Jack"
    QUEEN = "Queen"
    KING = "King"
    def __str__(self):
        return(f"{self.name}")

class Card:

    def __init__(self, suit, value) -> None:
        if type(suit) is Suit: self._suit = suit
        else: raise Exception('suit is wrong')
        if type(value) is Value: self._value = value #
        else: raise Exception('value is wrong')
    
    def getSuit(self):
        return self._suit
    def getValue(self):
        return self._value
    def getRank(self):
        ValueToRank = {Value.ACE: 14,
                      Value.TWO: 2,
                      Value.THREE: 3,
                      Value.FOUR: 4,
                      Value.FIVE: 5,
                      Value.SIX: 6,
                      Value.SEVEN: 7,
                      Value.EIGHT: 8,
                      Value.NINE: 9,
                      Value.TEN: 10,
                      Value.JACK: 11,
                      Value.QUEEN: 12,
                      Value.KING: 13}
        return ValueToRank[self._value]
    
    def __repr__(self) -> str:
        return f"<Card suit={self._suit} value={self._value}>"
    def __str__(self) -> str:
        ValueToAbbr = {Value.ACE: "A",
                      Value.TWO: "2",
                      Value.THREE: "3",
                      Value.FOUR: "4",
                      Value.FIVE: "5",
                      Value.SIX: "6",
                      Value.SEVEN: "7",
                      Value.EIGHT: "8",
                      Value.NINE: "9",
                      Value.TEN: "10",
                      Value.JACK: "J",
                      Value.QUEEN: "Q",
                      Value.KING: "K"}
        return f"{ValueToAbbr[self._value]} {self._suit.value}"
    def __int__(self) -> int:
        ValueToInt = {Value.ACE: 1,
                      Value.TWO: 2,
                      Value.THREE: 3,
                      Value.FOUR: 4,
                      Value.FIVE: 5,
                      Value.SIX: 6,
                      Value.SEVEN: 7,
                      Value.EIGHT: 8,
                      Value.NINE: 9,
                      Value.TEN: 10,
                      Value.JACK: 10,
                      Value.QUEEN: 10,
                      Value.KING: 10}
        return ValueToInt[self._value]
    
    ## Wrapper Class Functions ##
    def Sum(*args):
        cards = list(map(int, args))
        _sum = [sum(cards)]
        if 1 in cards:
            for x in range(1, cards.count(1)+1):
                _sum.append(_sum[0] + (10*x))
        
        return _sum
    def Sort(type=Value,*args): #by Value
        valueOrder = list(Value)
        suitOrder = list(Suit)
        if type == Value: return sorted(args, key = lambda card: (valueOrder.index(card.getValue()), suitOrder.index(card.getSuit())))
        elif type == Suit: return sorted(args, key = lambda card: (suitOrder.index(card.getSuit()), valueOrder.index(card.getValue())))

class Deck:

    def __init__(self, number=1) -> None:
        '''
        Param number: the number of decks to use. default 1
        '''
        self.deck = []
        number = int(number)

        for _ in range(number):
            for s in list(Suit):
                for v in list(Value):
                    self.deck.append(Card(s, v))
                
        Shuffle(self.deck)

    def draw(self) -> Card:
        if len(self.deck) > 0:
            return self.deck.pop(0)
        else:
            return    
    def reshuffle(self):
        Shuffle(self.deck)

    def __len__(self):
        return len(self.deck)
    
class Helper:
    async def wait_until(gameThread, conditon, timeout=30, timeoutMessage=""): #, **kwargs
        count = 0
        while not(conditon()) and count<timeout:
            await asyncio.sleep(1)
            count += 1
        if count>=timeout and timeoutMessage: #time out clause
            await gameThread.send(timeoutMessage)
        if count>=timeout: return False
        else: return True

