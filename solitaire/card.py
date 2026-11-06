"""Cartas, naipes e ranks (RF04, RF05, RF06, RNF05).

Decisões de projeto:
- ``Card`` é um *flyweight*: existe exatamente uma instância por combinação
  (rank, naipe). Assim, "qualquer referência à carta se comporta como a mesma
  carta" (RF04) é garantido pela identidade do objeto, e reconstituir uma carta
  a partir de seu identificador devolve o mesmo objeto (RNF05).
- A visibilidade (carta virada para cima ou para baixo) NÃO é um atributo da
  carta: ela pertence à posição que a carta ocupa. Isso evita que a visibilidade
  de uma jogada anterior "vaze" para a situação atual (RNF01).
"""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import ClassVar, Dict, Iterator, Tuple


class Color(Enum):
    RED = "red"
    BLACK = "black"


class Suit(Enum):
    """Naipe, com letra de identificação e cor (RF06)."""

    HEARTS = ("H", Color.RED, "Copas")
    DIAMONDS = ("D", Color.RED, "Ouros")
    CLUBS = ("C", Color.BLACK, "Paus")
    SPADES = ("S", Color.BLACK, "Espadas")

    def __init__(self, letter: str, color: Color, label: str) -> None:
        self.letter = letter
        self.color = color
        self.label = label

    def has_same_color_as(self, other: "Suit") -> bool:
        return self.color is other.color

    @classmethod
    def from_letter(cls, letter: str) -> "Suit":
        for suit in cls:
            if suit.letter == letter:
                return suit
        raise ValueError(f"Naipe desconhecido: {letter!r}")


class Rank(IntEnum):
    """Rank com ordem total: Ás < 2 < ... < Valete < Dama < Rei (RF05)."""

    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    @property
    def symbol(self) -> str:
        return _RANK_SYMBOLS[self]

    def is_immediately_above(self, other: "Rank") -> bool:
        return int(self) == int(other) + 1

    def is_immediately_below(self, other: "Rank") -> bool:
        return int(self) == int(other) - 1

    @classmethod
    def from_symbol(cls, symbol: str) -> "Rank":
        for rank in cls:
            if rank.symbol == symbol:
                return rank
        raise ValueError(f"Rank desconhecido: {symbol!r}")


_RANK_SYMBOLS = {
    Rank.ACE: "A", Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4",
    Rank.FIVE: "5", Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8",
    Rank.NINE: "9", Rank.TEN: "10", Rank.JACK: "J", Rank.QUEEN: "Q",
    Rank.KING: "K",
}

_CREATION_KEY = object()


class Card:
    """Carta imutável e única. Use ``Card.of(rank, suit)`` ou ``Card.from_id``."""

    __slots__ = ("_rank", "_suit")
    _instances: ClassVar[Dict[Tuple[Rank, Suit], "Card"]] = {}

    def __init__(self, rank: Rank, suit: Suit, _key: object = None) -> None:
        if _key is not _CREATION_KEY:
            raise TypeError("Use Card.of(rank, suit) para obter uma carta.")
        self._rank = rank
        self._suit = suit

    # --- criação / identidade -------------------------------------------

    @classmethod
    def of(cls, rank: Rank, suit: Suit) -> "Card":
        key = (Rank(rank), Suit(suit))
        card = cls._instances.get(key)
        if card is None:
            card = cls(key[0], key[1], _CREATION_KEY)
            cls._instances[key] = card
        return card

    @classmethod
    def all_cards(cls) -> Iterator["Card"]:
        """As 52 cartas, sem repetição (RF04), agrupadas por naipe."""
        for suit in Suit:
            for rank in Rank:
                yield cls.of(rank, suit)

    # --- atributos --------------------------------------------------------

    @property
    def rank(self) -> Rank:
        return self._rank

    @property
    def suit(self) -> Suit:
        return self._suit

    @property
    def color(self) -> Color:
        return self._suit.color

    # --- comparações usadas pelas regras (RF05, RF06) -----------------------

    def is_immediately_above(self, other: "Card") -> bool:
        return self._rank.is_immediately_above(other._rank)

    def is_immediately_below(self, other: "Card") -> bool:
        return self._rank.is_immediately_below(other._rank)

    def has_same_suit_as(self, other: "Card") -> bool:
        return self._suit is other._suit

    def has_same_color_as(self, other: "Card") -> bool:
        return self._suit.has_same_color_as(other._suit)

    # --- serialização (RNF05) ---------------------------------------------

    @property
    def id(self) -> str:
        """Identificador estável, por exemplo ``"10H"`` ou ``"AS"``."""
        return f"{self._rank.symbol}{self._suit.letter}"

    @classmethod
    def from_id(cls, card_id: str) -> "Card":
        if len(card_id) < 2:
            raise ValueError(f"Identificador inválido: {card_id!r}")
        return cls.of(Rank.from_symbol(card_id[:-1]), Suit.from_letter(card_id[-1]))

    def __reduce__(self):
        # pickle/copy reconstituem a MESMA instância (identidade preservada).
        return (Card.from_id, (self.id,))

    def __copy__(self) -> "Card":
        return self

    def __deepcopy__(self, memo) -> "Card":
        return self

    def __repr__(self) -> str:
        return f"Card({self.id})"
