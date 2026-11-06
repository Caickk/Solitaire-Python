"""Núcleo do jogo (RF01-RF03, RF11-RF13, RF16, RF19, RF21, RF25-RF27, RNF01-RNF03).

``Game`` é o único mecanismo central: todas as jogadas (do jogador ou da
estratégia) passam por ``execute``, que valida a legalidade, executa a ação,
registra no histórico e notifica os observadores.

O mundo externo (interface, estratégia) só recebe dados imutáveis: tuplas de
cartas, ``LocationRef``, booleanos. As pilhas mutáveis ficam encapsuladas aqui
(RF27, RNF03, RNF04).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, Tuple

from .action import Action
from .board import Board
from .card import Card
from .deck import Deck
from .location import STOCK_REF, LocationRef
from .play import DrawPlay, MovePlay, Play
from .strategy import AutoStrategy, Strategy
from .view import GameView

TOTAL_CARDS = 52


class IllegalPlayError(Exception):
    """Jogada rejeitada pelas regras do jogo (RF21)."""


class EventKind(Enum):
    NEW_GAME = "new_game"
    ACTION_DONE = "action_done"
    ACTION_UNDONE = "action_undone"


@dataclass(frozen=True)
class GameEvent:
    kind: EventKind
    action: Optional[Action] = None


Observer = Callable[[GameEvent], None]


class Game:
    def __init__(
        self,
        rng: Optional[random.Random] = None,
        board: Optional[Board] = None,
        strategy: Optional[Strategy] = None,
    ) -> None:
        """``rng`` permite partidas reprodutíveis. ``board`` permite iniciar de
        uma posição pronta (sem distribuir cartas), útil em testes. ``strategy``
        define o jogo automático (padrão: ``AutoStrategy``)."""
        self._rng = rng if rng is not None else random.Random()
        self._strategy: Strategy = strategy if strategy is not None else AutoStrategy()
        self._view = GameView(self)
        self._board = board if board is not None else Board()
        self._history: List[Action] = []
        self._observers: List[Observer] = []
        if board is None:
            self._deal()

    # --- partida (RF01, RF16) -------------------------------------------------

    def _deal(self) -> None:
        deck = Deck.standard()
        deck.shuffle(self._rng)
        cards = list(deck.cards)
        for i, column in enumerate(self._board.columns):
            for j in range(i + 1):
                column.push(cards.pop(), face_up=(j == i))  # só a última começa visível
        for card in cards:
            self._board.stock.push(card, face_up=False)

    def new_game(self) -> None:
        self._board.clear()
        self._history.clear()
        self._deal()
        self._notify(GameEvent(EventKind.NEW_GAME))

    def draw(self) -> None:
        """Ação de comprar. Com o monte vazio, reaproveitada para iniciar nova partida (RF01)."""
        if self._board.stock.is_empty():
            self.new_game()
        else:
            self.execute(DrawPlay())

    # --- observadores (RF26) ----------------------------------------------------

    def add_observer(self, observer: Observer) -> None:
        self._observers.append(observer)

    def remove_observer(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def _notify(self, event: GameEvent) -> None:
        for observer in tuple(self._observers):
            observer(event)

    # --- jogo automático (RF28, RF31) -------------------------------------------

    def set_strategy(self, strategy: Strategy) -> None:
        """Troca a estratégia. Use ``NullStrategy`` para desativar o jogo automático."""
        self._strategy = strategy

    def auto_play(self) -> Action:
        """Faz uma jogada automática, em duas etapas separadas (RF31).

        1. Decidir: a estratégia analisa o jogo só por consultas somente leitura.
        2. Executar: o mecanismo central valida (RF21), executa, registra (RF25) e
           notifica (RF26), exatamente como para uma jogada do jogador.
        Sem jogada possível (ou estratégia desativada), o resultado é uma ação nula.
        """
        play = self._strategy.suggest(self._view)
        return self.execute(play)

    # --- execução, histórico e desfazer (RF21, RF22, RF25) ------------------------

    def is_legal(self, play: Play) -> bool:
        return play.is_legal(self._board)

    def execute(self, play: Play) -> Action:
        """Valida (RF21), executa, registra (RF25) e notifica (RF26).

        Jogadas sem efeito (ex.: ``NoPlay``) não entram no histórico nem notificam,
        sem que este método precise saber o tipo da jogada (RNF02).
        """
        if not play.is_legal(self._board):
            raise IllegalPlayError(f"Jogada ilegal: {play!r}")
        action = play.build_action(self._board)
        action.do()
        if action.has_effect:
            self._history.append(action)
            self._notify(GameEvent(EventKind.ACTION_DONE, action))
        return action

    def move(self, card: Card, destination: LocationRef) -> Action:
        return self.execute(MovePlay(card, destination))

    def can_undo(self) -> bool:
        return bool(self._history)

    def undo(self) -> bool:
        """Desfaz a última jogada. Devolve ``False`` se não houver nenhuma."""
        if not self._history:
            return False
        action = self._history.pop()
        action.undo()
        self._notify(GameEvent(EventKind.ACTION_UNDONE, action))
        return True

    @property
    def moves_made(self) -> int:
        return len(self._history)

    # --- consultas somente leitura (RF03, RF09, RF10, RF20, RF27) -----------------

    @property
    def view(self) -> GameView:
        """Visão com apenas consultas (para a interface e para estratégias)."""
        return self._view

    @property
    def score(self) -> int:
        """Número de cartas nas fundações (RF03)."""
        return sum(len(f) for f in self._board.foundations)

    @property
    def is_won(self) -> bool:
        return self.score == TOTAL_CARDS  # RF02

    def locations(self) -> Tuple[LocationRef, ...]:
        return tuple(loc.ref for loc in self._board.locations)

    def cards_at(self, ref: LocationRef) -> Tuple[Card, ...]:
        return self._board.get(ref).cards

    def is_empty(self, ref: LocationRef) -> bool:
        return self._board.get(ref).is_empty()

    def top_card(self, ref: LocationRef) -> Optional[Card]:
        location = self._board.get(ref)
        return None if location.is_empty() else location.peek()

    def can_draw(self) -> bool:
        return not self._board.stock.is_empty()

    def can_start_new_game(self) -> bool:
        return self.is_empty(STOCK_REF)

    def can_move(self, card: Card, destination: LocationRef) -> bool:
        return self.is_legal(MovePlay(card, destination))

    def location_of(self, card: Card) -> Optional[LocationRef]:
        """Local da carta, se ela estiver acessível para movimentação (RF10)."""
        location = self._board.location_of(card)
        return None if location is None else location.ref

    def is_face_up(self, card: Card) -> bool:
        return self._locate(card).is_face_up(card)

    def sequence_from(self, card: Card) -> Tuple[Card, ...]:
        """Cartas de ``card`` até o topo: o que seria movido junto com ela (RF20)."""
        return self._locate(card).sequence_from(card)

    def is_bottom_most_face_up(self, card: Card) -> bool:
        return self._locate(card).is_bottom_most_face_up(card)

    def is_king_already_at_base(self, card: Card) -> bool:
        return self._locate(card).is_king_already_at_base(card)

    def _locate(self, card: Card):
        location = self._board.location_of(card, accessible_only=False)
        if location is None:
            raise ValueError(f"{card!r} não está no tabuleiro.")
        return location
