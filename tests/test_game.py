import random
import unittest

from solitaire.board import Board
from solitaire.card import Card, Rank, Suit
from solitaire.game import EventKind, Game, IllegalPlayError, TOTAL_CARDS
from solitaire.location import STOCK_REF, WASTE_REF, column_ref, foundation_ref
from solitaire.play import DrawPlay, MovePlay, NoPlay


def C(rank, suit):
    return Card.of(rank, suit)


def snapshot(game):
    return tuple(
        tuple((c.id, game.is_face_up(c)) for c in game.cards_at(ref))
        for ref in game.locations()
    )


def legal_plays(game):
    """Gera jogadas legais usando apenas consultas públicas do jogo."""
    plays = set()
    if game.can_draw():
        plays.add(DrawPlay())
    for ref in game.locations():
        for card in game.cards_at(ref):
            if game.location_of(card) is None:
                continue
            for dest in game.locations():
                play = MovePlay(card, dest)
                if game.is_legal(play):
                    plays.add(play)
    return plays


def check_invariants(test, game):
    cards = [c for ref in game.locations() for c in game.cards_at(ref)]
    test.assertEqual(len(cards), TOTAL_CARDS)
    test.assertEqual(len(set(cards)), TOTAL_CARDS)
    for i in range(7):
        col = game.cards_at(column_ref(i))
        if col:
            flags = [game.is_face_up(c) for c in col]
            test.assertTrue(flags[-1], "topo da coluna deve estar visível (RF19)")
            # ocultas sempre abaixo das visíveis
            test.assertEqual(flags, sorted(flags))
    test.assertTrue(all(game.is_face_up(c) for c in game.cards_at(WASTE_REF)))
    test.assertTrue(not any(game.is_face_up(c) for c in game.cards_at(STOCK_REF)))


class NewGameTests(unittest.TestCase):
    def test_rf01_rf16_initial_layout(self):
        g = Game(random.Random(3))
        self.assertEqual(sum(len(g.cards_at(column_ref(i))) for i in range(7)), 28)
        self.assertEqual(len(g.cards_at(STOCK_REF)), 24)
        self.assertTrue(g.is_empty(WASTE_REF))
        for i in range(4):
            self.assertTrue(g.is_empty(foundation_ref(i)))
        for i in range(7):
            col = g.cards_at(column_ref(i))
            self.assertEqual(len(col), i + 1)
            self.assertEqual([g.is_face_up(c) for c in col], [False] * i + [True])
        self.assertFalse(any(g.is_face_up(c) for c in g.cards_at(STOCK_REF)))
        check_invariants(self, g)

    def test_rf04_all_52_distinct_cards_in_play(self):
        check_invariants(self, Game())

    def test_games_differ_and_seed_is_reproducible(self):
        a, b, c = Game(random.Random(1)), Game(random.Random(1)), Game(random.Random(2))
        self.assertEqual(snapshot(a), snapshot(b))
        self.assertNotEqual(snapshot(a), snapshot(c))

    def test_rf01_draw_with_empty_stock_starts_new_game(self):
        board = Board()
        board.waste.push(C(Rank.ACE, Suit.SPADES))
        g = Game(rng=random.Random(5), board=board)
        events = []
        g.add_observer(events.append)
        self.assertTrue(g.can_start_new_game())
        g.draw()
        self.assertEqual(len(g.cards_at(STOCK_REF)), 24)
        self.assertTrue(g.is_empty(WASTE_REF))
        self.assertEqual(g.moves_made, 0)
        self.assertEqual([e.kind for e in events], [EventKind.NEW_GAME])
        check_invariants(self, g)

    def test_new_game_clears_history(self):
        g = Game(random.Random(1))
        g.draw()
        g.new_game()
        self.assertEqual(g.moves_made, 0)
        self.assertFalse(g.can_undo())


class ScoreAndVictoryTests(unittest.TestCase):
    def make(self, count):
        board = Board()
        placed = 0
        for i, suit in enumerate(Suit):
            for rank in Rank:
                if placed < count:
                    board.foundations[i].push(C(rank, suit))
                    placed += 1
        return Game(board=board)

    def test_rf03_score_counts_foundation_cards(self):
        self.assertEqual(Game(random.Random(0)).score, 0)
        self.assertEqual(self.make(17).score, 17)

    def test_rf02_victory_only_with_52(self):
        self.assertFalse(self.make(51).is_won)
        self.assertTrue(self.make(52).is_won)


class DrawTests(unittest.TestCase):
    def test_rf11_rf12_draw_and_undo(self):
        g = Game(random.Random(7))
        top = g.top_card(STOCK_REF)
        before = snapshot(g)
        g.draw()
        self.assertIs(g.top_card(WASTE_REF), top)
        self.assertTrue(g.is_face_up(top))
        self.assertEqual(len(g.cards_at(STOCK_REF)), 23)
        self.assertTrue(g.undo())
        self.assertIs(g.top_card(STOCK_REF), top)
        self.assertFalse(g.is_face_up(top))
        self.assertTrue(g.is_empty(WASTE_REF))
        self.assertEqual(snapshot(g), before)

    def test_rf11_all_24_cards_can_be_drawn(self):
        g = Game(random.Random(7))
        for _ in range(24):
            g.draw()
        self.assertTrue(g.is_empty(STOCK_REF))
        self.assertEqual(len(g.cards_at(WASTE_REF)), 24)

    def test_rf13_waste_is_not_a_destination(self):
        board = Board()
        board.columns[0].push(C(Rank.FIVE, Suit.CLUBS))
        g = Game(board=board)
        self.assertFalse(g.can_move(C(Rank.FIVE, Suit.CLUBS), WASTE_REF))
        self.assertFalse(g.can_move(C(Rank.FIVE, Suit.CLUBS), STOCK_REF))
        with self.assertRaises(IllegalPlayError):
            g.move(C(Rank.FIVE, Suit.CLUBS), WASTE_REF)


class LegalityTests(unittest.TestCase):
    def game_with(self, **spots):
        board = Board()
        for name, cards in spots.items():
            kind, idx = name.rstrip("0123456789"), int(name[len(name.rstrip("0123456789")):] or 0)
            loc = {"col": board.columns, "fnd": board.foundations}.get(kind)
            target = loc[idx] if loc else getattr(board, kind)
            for card, up in cards:
                target.push(card, up)
        return Game(board=board)

    def test_rf15_empty_foundation_accepts_only_ace(self):
        g = self.game_with(col0=[(C(Rank.TWO, Suit.HEARTS), True)],
                           col1=[(C(Rank.ACE, Suit.HEARTS), True)])
        self.assertFalse(g.can_move(C(Rank.TWO, Suit.HEARTS), foundation_ref(0)))
        self.assertTrue(g.can_move(C(Rank.ACE, Suit.HEARTS), foundation_ref(0)))

    def test_rf15_foundation_same_suit_next_rank(self):
        g = self.game_with(fnd0=[(C(Rank.ACE, Suit.HEARTS), True)],
                           col0=[(C(Rank.TWO, Suit.HEARTS), True)],
                           col1=[(C(Rank.TWO, Suit.CLUBS), True)],
                           col2=[(C(Rank.THREE, Suit.HEARTS), True)])
        self.assertTrue(g.can_move(C(Rank.TWO, Suit.HEARTS), foundation_ref(0)))
        self.assertFalse(g.can_move(C(Rank.TWO, Suit.CLUBS), foundation_ref(0)))
        self.assertFalse(g.can_move(C(Rank.THREE, Suit.HEARTS), foundation_ref(0)))

    def test_rf15_only_one_card_at_a_time_to_foundation(self):
        g = self.game_with(fnd0=[(C(Rank.ACE, Suit.HEARTS), True)],
                           col0=[(C(Rank.TWO, Suit.HEARTS), True), (C(Rank.ACE, Suit.CLUBS), True)])
        # 2H seria aceita sozinha, mas move junto com o AC que está sobre ela (2 cartas): ilegal
        self.assertFalse(g.can_move(C(Rank.TWO, Suit.HEARTS), foundation_ref(0)))

    def test_rf17_empty_column_accepts_only_king(self):
        g = self.game_with(col0=[(C(Rank.QUEEN, Suit.CLUBS), True)],
                           col1=[(C(Rank.KING, Suit.HEARTS), True)])
        self.assertFalse(g.can_move(C(Rank.QUEEN, Suit.CLUBS), column_ref(2)))
        self.assertTrue(g.can_move(C(Rank.KING, Suit.HEARTS), column_ref(2)))

    def test_rf17_column_rank_below_and_alternate_color(self):
        g = self.game_with(col0=[(C(Rank.SEVEN, Suit.HEARTS), True)],
                           col1=[(C(Rank.SIX, Suit.CLUBS), True)],
                           col2=[(C(Rank.SIX, Suit.DIAMONDS), True)],
                           col3=[(C(Rank.FIVE, Suit.SPADES), True)])
        self.assertTrue(g.can_move(C(Rank.SIX, Suit.CLUBS), column_ref(0)))
        self.assertFalse(g.can_move(C(Rank.SIX, Suit.DIAMONDS), column_ref(0)))   # mesma cor
        self.assertFalse(g.can_move(C(Rank.FIVE, Suit.SPADES), column_ref(0)))    # rank errado

    def test_rf18_sequence_moves_together(self):
        g = self.game_with(col0=[(C(Rank.NINE, Suit.CLUBS), False), (C(Rank.EIGHT, Suit.HEARTS), True),
                                 (C(Rank.SEVEN, Suit.SPADES), True), (C(Rank.SIX, Suit.DIAMONDS), True)],
                           col1=[(C(Rank.NINE, Suit.DIAMONDS), True)])
        eight = C(Rank.EIGHT, Suit.HEARTS)
        self.assertEqual(g.sequence_from(eight), (eight, C(Rank.SEVEN, Suit.SPADES), C(Rank.SIX, Suit.DIAMONDS)))
        self.assertFalse(g.can_move(eight, column_ref(1)))  # 8 vermelho sobre 9 vermelho: ilegal
        g2 = self.game_with(col0=[(C(Rank.EIGHT, Suit.HEARTS), True), (C(Rank.SEVEN, Suit.SPADES), True),
                                  (C(Rank.SIX, Suit.DIAMONDS), True)],
                            col1=[(C(Rank.NINE, Suit.CLUBS), True)])
        g2.move(eight, column_ref(1))
        self.assertEqual([c.id for c in g2.cards_at(column_ref(1))], ["9C", "8H", "7S", "6D"])
        self.assertTrue(g2.is_empty(column_ref(0)))

    def test_rf21_hidden_and_non_top_cards_are_not_movable(self):
        g = self.game_with(col0=[(C(Rank.KING, Suit.HEARTS), False), (C(Rank.QUEEN, Suit.CLUBS), True)],
                           waste=[(C(Rank.ACE, Suit.CLUBS), True), (C(Rank.TWO, Suit.CLUBS), True)])
        self.assertFalse(g.can_move(C(Rank.KING, Suit.HEARTS), column_ref(1)))     # oculta
        self.assertFalse(g.can_move(C(Rank.ACE, Suit.CLUBS), foundation_ref(0)))   # não é topo do descarte
        self.assertFalse(g.can_move(C(Rank.QUEEN, Suit.CLUBS), column_ref(0)))     # mesmo local

    def test_rf21_illegal_play_changes_nothing_and_does_not_notify(self):
        g = self.game_with(col0=[(C(Rank.TWO, Suit.CLUBS), True)])
        events, before = [], snapshot(g)
        g.add_observer(events.append)
        with self.assertRaises(IllegalPlayError):
            g.move(C(Rank.TWO, Suit.CLUBS), foundation_ref(0))
        self.assertEqual(snapshot(g), before)
        self.assertEqual((events, g.moves_made), ([], 0))

    def test_rf10_location_of_accessible_card(self):
        g = self.game_with(col0=[(C(Rank.KING, Suit.HEARTS), False), (C(Rank.QUEEN, Suit.CLUBS), True)])
        self.assertEqual(g.location_of(C(Rank.QUEEN, Suit.CLUBS)), column_ref(0))
        self.assertIsNone(g.location_of(C(Rank.KING, Suit.HEARTS)))

    def test_rf20_queries(self):
        g = self.game_with(col0=[(C(Rank.KING, Suit.HEARTS), True), (C(Rank.QUEEN, Suit.CLUBS), True)],
                           col1=[(C(Rank.TWO, Suit.HEARTS), False), (C(Rank.KING, Suit.CLUBS), True)])
        self.assertTrue(g.is_king_already_at_base(C(Rank.KING, Suit.HEARTS)))
        self.assertFalse(g.is_king_already_at_base(C(Rank.KING, Suit.CLUBS)))
        self.assertTrue(g.is_bottom_most_face_up(C(Rank.KING, Suit.CLUBS)))
        self.assertFalse(g.is_bottom_most_face_up(C(Rank.QUEEN, Suit.CLUBS)))
        self.assertEqual(g.cards_at(column_ref(0)), (C(Rank.KING, Suit.HEARTS), C(Rank.QUEEN, Suit.CLUBS)))


class RevealTests(unittest.TestCase):
    def setUp(self):
        board = Board()
        board.columns[0].push(C(Rank.NINE, Suit.CLUBS), False)
        board.columns[0].push(C(Rank.QUEEN, Suit.SPADES), True)
        board.columns[1].push(C(Rank.KING, Suit.HEARTS), True)
        self.g = Game(board=board)
        self.events = []
        self.g.add_observer(self.events.append)

    def test_rf19_move_reveals_hidden_card_in_same_play(self):
        nine = C(Rank.NINE, Suit.CLUBS)
        self.g.move(C(Rank.QUEEN, Suit.SPADES), column_ref(1))
        self.assertTrue(self.g.is_face_up(nine))
        self.assertEqual(self.g.moves_made, 1)             # uma única jogada
        self.assertEqual(len(self.events), 1)               # uma única notificação (RF26)

    def test_rf19_undo_hides_card_again(self):
        nine = C(Rank.NINE, Suit.CLUBS)
        before = snapshot(self.g)
        self.g.move(C(Rank.QUEEN, Suit.SPADES), column_ref(1))
        self.g.undo()
        self.assertFalse(self.g.is_face_up(nine))
        self.assertEqual(snapshot(self.g), before)


class NotificationTests(unittest.TestCase):
    def test_rf26_events_for_do_undo_and_null(self):
        g = Game(random.Random(2))
        events = []
        g.add_observer(events.append)
        g.draw()
        g.execute(NoPlay())                  # sem efeito: sem histórico, sem notificação
        g.undo()
        g.undo()                             # nada a desfazer: sem notificação
        self.assertEqual([e.kind for e in events], [EventKind.ACTION_DONE, EventKind.ACTION_UNDONE])
        self.assertEqual(g.moves_made, 0)

    def test_remove_observer(self):
        g = Game(random.Random(2))
        events = []
        g.add_observer(events.append)
        g.remove_observer(events.append)
        g.draw()
        self.assertEqual(events, [])


class ReadOnlyQueriesTests(unittest.TestCase):
    def test_rf27_queries_never_change_state_or_notify(self):
        g = Game(random.Random(4))
        for _ in range(5):
            g.draw()
        events, before = [], snapshot(g)
        g.add_observer(events.append)
        for ref in g.locations():
            g.is_empty(ref)
            g.top_card(ref)
            cards = g.cards_at(ref)
            self.assertIsInstance(cards, tuple)
            for card in cards:
                g.is_face_up(card)
                g.sequence_from(card)
                g.location_of(card)
                g.is_bottom_most_face_up(card)
                g.is_king_already_at_base(card)
                for dest in g.locations():
                    g.can_move(card, dest)
        g.can_draw(); g.can_undo(); g.can_start_new_game(); g.score; g.is_won
        legal_plays(g)
        self.assertEqual(snapshot(g), before)
        self.assertEqual(events, [])

    def test_returned_cards_cannot_mutate_the_game(self):
        g = Game(random.Random(4))
        cards = g.cards_at(column_ref(6))
        with self.assertRaises(TypeError):
            cards[0] = cards[1]
        self.assertEqual(g.cards_at(column_ref(6)), cards)


class HistoryTests(unittest.TestCase):
    def test_rf25_undo_all_restores_initial_state_and_is_ready_to_continue(self):
        for seed in range(6):
            rng = random.Random(seed)
            g = Game(random.Random(seed))
            initial, initial_plays = snapshot(g), legal_plays(g)
            moves = 0
            for _ in range(400):
                plays = sorted(legal_plays(g), key=repr)
                if not plays:
                    break
                g.execute(rng.choice(plays))
                moves += 1
                check_invariants(self, g)
            self.assertGreater(g.moves_made, 40)
            while g.can_undo():
                self.assertTrue(g.undo())
                check_invariants(self, g)
            self.assertEqual(snapshot(g), initial)
            self.assertEqual(legal_plays(g), initial_plays)       # pronto para continuar
            self.assertFalse(g.undo())
            g.execute(rng.choice(sorted(legal_plays(g), key=repr)))  # e continua funcionando
            check_invariants(self, g)

    def test_history_keeps_real_order(self):
        g = Game(random.Random(1))
        top1 = g.top_card(STOCK_REF)
        g.draw()
        top2 = g.top_card(STOCK_REF)
        g.draw()
        g.undo()
        self.assertIs(g.top_card(WASTE_REF), top1)
        g.undo()
        self.assertTrue(g.is_empty(WASTE_REF))
        self.assertIs(g.top_card(STOCK_REF), top1)
        self.assertNotEqual(top1, top2)


if __name__ == "__main__":
    unittest.main()
