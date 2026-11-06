import random
import unittest

from solitaire.action import Action
from solitaire.board import Board
from solitaire.card import Card, Rank, Suit
from solitaire.game import EventKind, Game, IllegalPlayError
from solitaire.location import column_ref, foundation_ref
from solitaire.play import DrawPlay, MovePlay, NoPlay
from solitaire.simulate import MAX_STEPS, play_automatically, simulate
from solitaire.strategy import AutoStrategy, NullStrategy, Strategy
from solitaire.view import GameView


def C(rank, suit):
    return Card.of(rank, suit)


def snapshot(game):
    return tuple(
        tuple((c.id, game.is_face_up(c)) for c in game.cards_at(ref))
        for ref in game.locations()
    )


def build(stock=(), waste=(), foundations=(), columns=()):
    """Cada carta é (Card, visível). Stock sempre virado para baixo."""
    board = Board()
    for card in stock:
        board.stock.push(card, False)
    for card in waste:
        board.waste.push(card, True)
    for i, cards in enumerate(foundations):
        for card in cards:
            board.foundations[i].push(card, True)
    for i, cards in enumerate(columns):
        for card, up in cards:
            board.columns[i].push(card, up)
    return Game(board=board)


AH, TWOH = C(Rank.ACE, Suit.HEARTS), C(Rank.TWO, Suit.HEARTS)
AS = C(Rank.ACE, Suit.SPADES)
THREES = C(Rank.THREE, Suit.SPADES)
SIXC, SEVENH = C(Rank.SIX, Suit.CLUBS), C(Rank.SEVEN, Suit.HEARTS)
KH, QS, NINEC = C(Rank.KING, Suit.HEARTS), C(Rank.QUEEN, Suit.SPADES), C(Rank.NINE, Suit.CLUBS)
SPARE = C(Rank.FIVE, Suit.DIAMONDS)


class PriorityTests(unittest.TestCase):
    """Uma prova por item do RF29: cada cenário também tem uma jogada de prioridade menor possível."""

    def suggest(self, game):
        return AutoStrategy().suggest(GameView(game))

    def test_1_draw_when_waste_is_empty_even_if_other_moves_exist(self):
        g = build(stock=[SPARE], columns=[[(AS, True)]])     # AS poderia ir à fundação (prioridade 4)
        self.assertEqual(self.suggest(g), DrawPlay())

    def test_2_waste_to_foundation_before_tableau(self):
        g = build(stock=[SPARE], waste=[TWOH], foundations=[[AH]],
                  columns=[[(THREES, True)]])                  # 2H também caberia sobre 3S
        self.assertEqual(self.suggest(g), MovePlay(TWOH, foundation_ref(0)))

    def test_3_waste_to_tableau(self):
        g = build(stock=[SPARE], waste=[SIXC], columns=[[(SEVENH, True)]])
        self.assertEqual(self.suggest(g), MovePlay(SIXC, column_ref(0)))

    def test_4_column_top_to_foundation_before_tableau_moves(self):
        g = build(columns=[[(NINEC, False), (QS, True)], [(KH, True)], [(AS, True)]])
        self.assertEqual(self.suggest(g), MovePlay(AS, foundation_ref(0)))   # QS->KH também seria possível

    def test_5_tableau_move_that_reveals_a_card(self):
        g = build(columns=[[(NINEC, False), (QS, True)], [(KH, True)]])
        self.assertEqual(self.suggest(g), MovePlay(QS, column_ref(1)))

    def test_5_tableau_move_that_empties_a_column(self):
        g = build(columns=[[(QS, True)], [(KH, True)]])
        self.assertEqual(self.suggest(g), MovePlay(QS, column_ref(1)))

    def test_5_move_without_gain_is_not_suggested(self):
        # 8S sobre 9H é legal, mas não revela nem esvazia nada.
        eight_s, nine_h, nine_d = C(Rank.EIGHT, Suit.SPADES), C(Rank.NINE, Suit.HEARTS), C(Rank.NINE, Suit.DIAMONDS)
        g = build(columns=[[(C(Rank.TWO, Suit.CLUBS), False), (nine_d, True), (eight_s, True)],
                           [(nine_h, True)]])
        self.assertTrue(g.can_move(eight_s, column_ref(1)))
        self.assertEqual(self.suggest(g), NoPlay())

    def test_rf30_king_already_at_base_is_not_moved(self):
        g = build(columns=[[(KH, True)], []])
        self.assertTrue(g.can_move(KH, column_ref(1)))        # legal pelas regras...
        self.assertEqual(self.suggest(g), NoPlay())            # ...mas inútil: a estratégia evita

    def test_6_draw_when_nothing_else_is_possible(self):
        g = build(stock=[SPARE], waste=[C(Rank.TWO, Suit.CLUBS)])
        self.assertEqual(self.suggest(g), DrawPlay())

    def test_7_no_play(self):
        self.assertEqual(self.suggest(build()), NoPlay())
        self.assertEqual(self.suggest(build(waste=[C(Rank.TWO, Suit.CLUBS)])), NoPlay())


class DecideAndExecuteTests(unittest.TestCase):
    def test_rf31_decide_does_not_change_state(self):
        g = Game(random.Random(3))
        before = snapshot(g)
        for _ in range(20):
            AutoStrategy().suggest(GameView(g))
        self.assertEqual(snapshot(g), before)
        self.assertEqual(g.moves_made, 0)

    def test_rnf04_view_has_only_queries(self):
        view = GameView(Game(random.Random(1)))
        for name in ("execute", "move", "draw", "undo", "new_game", "auto_play",
                     "set_strategy", "add_observer", "_board", "board"):
            self.assertFalse(hasattr(view, name), name)

    def test_rf31_execution_is_validated_by_the_game(self):
        class Rogue(Strategy):
            def suggest(self, view):
                card = view.top_card(column_ref(0))
                return MovePlay(card, foundation_ref(0))       # ilegal (a menos que seja Ás)

        g = Game(random.Random(1), strategy=Rogue())
        events, before = [], snapshot(g)
        g.add_observer(events.append)
        self.assertNotEqual(g.top_card(column_ref(0)).rank, Rank.ACE)
        with self.assertRaises(IllegalPlayError):
            g.auto_play()
        self.assertEqual(snapshot(g), before)
        self.assertEqual((events, g.moves_made), ([], 0))

    def test_rf31_auto_play_is_recorded_and_notified_like_a_player_move(self):
        g = Game(random.Random(2))
        events = []
        g.add_observer(events.append)
        action = g.auto_play()
        self.assertTrue(action.has_effect)
        self.assertEqual(g.moves_made, 1)
        self.assertEqual([e.kind for e in events], [EventKind.ACTION_DONE])
        before_undo = snapshot(g)
        self.assertTrue(g.undo())
        self.assertNotEqual(snapshot(g), before_undo)
        self.assertEqual(events[-1].kind, EventKind.ACTION_UNDONE)


class DisabledStrategyTests(unittest.TestCase):
    def test_rf28_null_strategy_does_nothing_with_no_special_handling(self):
        g = Game(random.Random(2), strategy=NullStrategy())
        events, before = [], snapshot(g)
        g.add_observer(events.append)
        for _ in range(5):
            action = g.auto_play()
            self.assertIsInstance(action, Action)
            self.assertFalse(action.has_effect)
        self.assertEqual((snapshot(g), events, g.moves_made), (before, [], 0))

    def test_rf28_can_be_disabled_at_any_time(self):
        g = Game(random.Random(2))
        for _ in range(5):
            g.auto_play()
        done = g.moves_made
        before = snapshot(g)
        g.set_strategy(NullStrategy())
        g.auto_play()
        self.assertEqual((snapshot(g), g.moves_made), (before, done))
        g.set_strategy(AutoStrategy())
        self.assertTrue(g.auto_play().has_effect)

    def test_rf24_no_play_when_nothing_is_possible(self):
        g = build()
        action = g.auto_play()
        self.assertFalse(action.has_effect)
        self.assertEqual(g.moves_made, 0)


class FullAutoPlayTests(unittest.TestCase):
    def test_rf30_no_loops_each_step_reaches_a_new_state(self):
        for seed in range(40):
            g = Game(random.Random(seed))
            seen = {snapshot(g)}
            steps = 0
            while g.auto_play().has_effect:
                steps += 1
                state = snapshot(g)
                self.assertNotIn(state, seen, f"estado repetido (seed {seed}, passo {steps})")
                seen.add(state)
                self.assertLess(steps, MAX_STEPS)

    def test_rf25_undo_all_then_auto_play_again_gives_same_result(self):
        for seed in range(10):
            g = Game(random.Random(seed))
            initial = snapshot(g)
            play_automatically(g)
            final = snapshot(g)
            while g.undo():
                pass
            self.assertEqual(snapshot(g), initial)
            play_automatically(g)                      # jogo automático continua a funcionar
            self.assertEqual(snapshot(g), final)

    def test_auto_play_after_manual_undo_midway(self):
        g = Game(random.Random(4))
        for _ in range(15):
            g.auto_play()
        for _ in range(7):
            g.undo()
        self.assertTrue(g.auto_play().has_effect)

    def test_rf03_simulation_statistics(self):
        r = simulate(30, seed=0)
        self.assertEqual(r.games, 30)
        self.assertTrue(all(0 <= s <= 52 for s in r.scores))
        self.assertEqual(simulate(30, seed=0).scores, r.scores)        # reprodutível
        self.assertEqual(r.wins, sum(1 for s in r.scores if s == 52))

    def test_victory_is_detected_by_score_in_automatic_games(self):
        for seed in range(200):
            g = Game(random.Random(seed))
            play_automatically(g)
            if g.is_won:
                self.assertEqual(g.score, 52)
                return
        self.fail("Nenhuma vitória automática em 200 partidas: verifique a estratégia.")


if __name__ == "__main__":
    unittest.main()
