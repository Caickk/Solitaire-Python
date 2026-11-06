"""Simulações automáticas, para estatísticas de pontuação (RF03).

Uso:  python -m solitaire.simulate -n 1000 --seed 0
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .game import Game

MAX_STEPS = 2000  # limite de segurança: atingi-lo indicaria um ciclo (RF30)


def play_automatically(game: Game, max_steps: int = MAX_STEPS) -> int:
    """Joga até não haver jogada. Devolve o número de jogadas efetivas."""
    steps = 0
    while True:
        action = game.auto_play()
        if not action.has_effect:
            return steps
        steps += 1
        if steps >= max_steps:
            raise RuntimeError("Jogo automático não terminou: possível ciclo.")


@dataclass(frozen=True)
class SimulationResult:
    scores: Sequence[int]
    moves: Sequence[int]

    @property
    def games(self) -> int:
        return len(self.scores)

    @property
    def wins(self) -> int:
        return sum(1 for s in self.scores if s == 52)

    @property
    def average_score(self) -> float:
        return sum(self.scores) / len(self.scores)

    @property
    def average_moves(self) -> float:
        return sum(self.moves) / len(self.moves)


def simulate(games: int, seed: int = 0) -> SimulationResult:
    scores: List[int] = []
    moves: List[int] = []
    for i in range(games):
        game = Game(random.Random(seed + i))
        moves.append(play_automatically(game))
        scores.append(game.score)
    return SimulationResult(scores, moves)


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Simula partidas automáticas de Solitaire.")
    parser.add_argument("-n", "--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    result = simulate(args.games, args.seed)
    print(f"Partidas: {result.games}")
    print(f"Vitórias: {result.wins} ({100 * result.wins / result.games:.1f}%)")
    print(f"Pontuação média: {result.average_score:.2f} (mín {min(result.scores)}, máx {max(result.scores)})")
    print(f"Jogadas médias por partida: {result.average_moves:.1f}")


if __name__ == "__main__":
    main()
