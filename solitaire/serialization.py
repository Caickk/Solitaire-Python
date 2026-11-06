"""Serialização de cartas e sequências (RNF05).

Usada, por exemplo, para "transportar" a sequência arrastada com o mouse (RF32).
A conversão não altera a identidade nem a ordem das cartas: ao reconstituir,
``Card.from_id`` devolve as MESMAS instâncias únicas (ver ``card.py``).
"""

from __future__ import annotations

from typing import Iterable, Tuple

from .card import Card

SEPARATOR = ","


def serialize_cards(cards: Iterable[Card]) -> str:
    """``(KH, QC, JD)`` -> ``"KH,QC,JD"`` (base -> topo)."""
    return SEPARATOR.join(card.id for card in cards)


def deserialize_cards(payload: str) -> Tuple[Card, ...]:
    if not payload:
        return ()
    cards = tuple(Card.from_id(part) for part in payload.split(SEPARATOR))
    if len(set(cards)) != len(cards):
        raise ValueError(f"Sequência com cartas repetidas: {payload!r}")
    return cards
