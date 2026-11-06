import pathlib
import random
import unittest
from unittest import mock

from solitaire.board import Board
from solitaire.card import Card, Rank, Suit
from solitaire.game import Game
from solitaire.location import STOCK_REF, WASTE_REF, column_ref, foundation_ref
from solitaire.serialization import serialize_cards
from solitaire.ui.drag import DragController
from solitaire.ui.layout import CANVAS_H, CANVAS_W, CARD_H, CARD_W, Layout


def C(rank, suit):
    return Card.of(rank, suit)


def snapshot(game):
    return tuple(
        tuple((c.id, game.is_face_up(c)) for c in game.cards_at(ref))
        for ref in game.locations()
    )


def build(stock=(), waste=(), foundations=(), columns=()):
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


def setup(game):
    layout = Layout(game.view)
    return layout, DragController(game, layout)


def center(layout, card):
    placed = next(p for p in layout.placed_cards() if p.card is card)
    return placed.x + CARD_W // 2, placed.y + 10     # parte visível da carta


KH, QS, JD = C(Rank.KING, Suit.HEARTS), C(Rank.QUEEN, Suit.SPADES), C(Rank.JACK, Suit.DIAMONDS)
TENC, NINEC, SPARE = C(Rank.TEN, Suit.CLUBS), C(Rank.NINE, Suit.CLUBS), C(Rank.FIVE, Suit.DIAMONDS)
AH, TWOH = C(Rank.ACE, Suit.HEARTS), C(Rank.TWO, Suit.HEARTS)


class LayoutTests(unittest.TestCase):
    def test_all_52_cards_placed_inside_canvas(self):
        g = Game(random.Random(1))
        placed = Layout(g.view).placed_cards()
        self.assertEqual(len(placed), 52)
        for p in placed:
            self.assertTrue(0 <= p.x and p.x + CARD_W <= CANVAS_W)
            self.assertTrue(0 <= p.y and p.y + CARD_H <= CANVAS_H)

    def test_worst_case_column_fits_in_canvas(self):
        cols = [[(C(r, Suit.CLUBS), False) for r in list(Rank)[:6]] + [(C(r, Suit.HEARTS), True) for r in reversed(list(Rank))]]
        g = build(columns=cols)
        self.assertLessEqual(max(p.y + CARD_H for p in Layout(g.view).placed_cards()), CANVAS_H)

    def test_column_cards_cascade_downwards_in_order(self):
        g = Game(random.Random(2))
        layout = Layout(g.view)
        ys = [p.y for p in layout.placed_cards() if p.ref == column_ref(6)]
        self.assertEqual(ys, sorted(ys))
        self.assertEqual(len(set(ys)), 7)

    def test_card_at_returns_topmost_visible_card(self):
        g = build(columns=[[(KH, True), (QS, True), (JD, True)]])
        layout = Layout(g.view)
        kx, ky = center(layout, KH)
        self.assertIs(layout.card_at(kx, ky).card, KH)             # parte visível do Rei
        qx, qy = center(layout, QS)
        self.assertIs(layout.card_at(qx, qy).card, QS)
        jx, jy = center(layout, JD)
        self.assertIs(layout.card_at(jx, jy + 60).card, JD)        # corpo da última carta
        self.assertIsNone(layout.card_at(5, CANVAS_H - 5))

    def test_location_at(self):
        g = Game(random.Random(3))
        layout = Layout(g.view)
        for ref in g.locations():
            x, y, w, h = layout.slot_rect(ref)
            self.assertEqual(layout.location_at(x + w // 2, y + h // 2), ref)
        x, y, w, h = layout.slot_rect(column_ref(3))
        self.assertEqual(layout.location_at(x + 5, CANVAS_H - 2), column_ref(3))   # coluna se estende
        self.assertIsNone(layout.location_at(layout.slot_rect(foundation_ref(0))[0] - 70, 40))

    def test_slot_rects_do_not_overlap(self):
        g = Game(random.Random(3))
        layout = Layout(g.view)
        rects = [layout.slot_rect(r) for r in g.locations()]
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                self.assertFalse(a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3])


class DragTests(unittest.TestCase):
    def test_hidden_card_and_empty_area_do_not_start_drag(self):
        g = build(columns=[[(NINEC, False), (QS, True)]])
        layout, drag = setup(g)
        self.assertFalse(drag.press(*center(layout, NINEC)))
        self.assertFalse(drag.press(5, CANVAS_H - 5))
        self.assertIsNone(drag.state)

    def test_non_top_waste_card_cannot_be_dragged(self):
        g = build(waste=[TWOH, SPARE])
        layout, drag = setup(g)
        x, y, w, h = layout.slot_rect(WASTE_REF)
        self.assertTrue(drag.press(x + 10, y + 10))
        self.assertEqual(drag.state.cards, (SPARE,))

    def test_rf32_sequence_drag_takes_all_cards_above(self):
        g = build(columns=[[(KH, True), (QS, True), (JD, True)]])
        layout, drag = setup(g)
        self.assertTrue(drag.press(*center(layout, QS)))
        self.assertEqual(drag.state.cards, (QS, JD))
        self.assertEqual(drag.state.payload, serialize_cards((QS, JD)))
        self.assertTrue(all(a is b for a, b in zip(drag.state.cards, (QS, JD))))   # RNF05

    def test_rf32_target_indication_comes_from_game_rules(self):
        g = build(columns=[[(QS, True)], [(KH, True)], [(JD, True)], []])
        layout, drag = setup(g)
        drag.press(*center(layout, QS))
        with mock.patch.object(g, "can_move", wraps=g.can_move) as spy:
            tx, ty = center(layout, KH)
            drag.motion(tx, ty)                                   # QS sobre KH: legal
            self.assertTrue(drag.state.valid)
            spy.assert_called_with(QS, column_ref(1))
            jx, jy = center(layout, JD)
            drag.motion(jx, jy)                                   # QS sobre JD: ilegal
            self.assertFalse(drag.state.valid)
            spy.assert_called_with(QS, column_ref(2))
            drag.motion(5, 5)                                         # fora de qualquer local
            self.assertIsNone(drag.state.target)
            self.assertFalse(drag.state.valid)
        self.assertEqual(g.moves_made, 0)                         # arrastar não altera o jogo

    def test_release_on_valid_target_moves_sequence_through_game(self):
        g = build(columns=[[(NINEC, False), (QS, True), (JD, True)], [(KH, True)]])
        layout, drag = setup(g)
        drag.press(*center(layout, QS))
        self.assertTrue(drag.release(*center(layout, KH)))
        self.assertEqual(g.cards_at(column_ref(1)), (KH, QS, JD))
        self.assertTrue(g.is_face_up(NINEC))                      # revelação automática (RF19)
        self.assertEqual(g.moves_made, 1)
        self.assertIsNone(drag.state)
        g.undo()
        self.assertEqual(g.cards_at(column_ref(0)), (NINEC, QS, JD))

    def test_release_on_invalid_target_or_outside_changes_nothing(self):
        g = build(columns=[[(QS, True)], [(JD, True)]])
        layout, drag = setup(g)
        before = snapshot(g)
        drag.press(*center(layout, QS))
        self.assertFalse(drag.release(*center(layout, JD)))
        drag.press(*center(layout, QS))
        self.assertFalse(drag.release(5, 5))
        drag.press(*center(layout, QS))
        self.assertFalse(drag.release(*layout.slot_rect(WASTE_REF)[:2]))   # descarte nunca é destino
        self.assertEqual(snapshot(g), before)
        self.assertEqual(g.moves_made, 0)

    def test_drag_to_foundation_one_card_only(self):
        g = build(columns=[[(AH, True)], [(TWOH, True), (JD, True)]])
        layout, drag = setup(g)
        fx, fy, fw, fh = layout.slot_rect(foundation_ref(0))
        drag.press(*center(layout, AH))
        self.assertTrue(drag.release(fx + 5, fy + 5))
        self.assertEqual(g.cards_at(foundation_ref(0)), (AH,))
        drag.press(*center(layout, TWOH))                          # 2H leva o valete: 2 cartas
        self.assertFalse(drag.release(fx + 5, fy + 5))

    def test_stock_click_draws_and_empty_stock_starts_new_game(self):
        g = build(stock=[SPARE, AH])
        layout, drag = setup(g)
        sx, sy, w, h = layout.slot_rect(STOCK_REF)
        self.assertFalse(drag.press(sx + 5, sy + 5))
        self.assertEqual(g.top_card(WASTE_REF), AH)
        drag.press(sx + 5, sy + 5)
        self.assertTrue(g.can_start_new_game())
        drag.press(sx + 5, sy + 5)                                 # monte vazio: nova partida (RF01)
        self.assertEqual(len(g.cards_at(STOCK_REF)), 24)
        self.assertEqual(g.moves_made, 0)

    def test_cancel(self):
        g = build(columns=[[(QS, True)]])
        layout, drag = setup(g)
        drag.press(*center(layout, QS))
        drag.cancel()
        self.assertIsNone(drag.state)
        self.assertFalse(drag.release(10, 10))


class UiHasNoRulesTests(unittest.TestCase):
    """RNF03: a interface não repete regras de legalidade nem acessa o tabuleiro."""

    FORBIDDEN = ("is_immediately", "has_same_color", "has_same_suit", "can_accept",
                 "Rank.KING", "Rank.ACE", "Rank.", "from ..board", "from ..location import Column",
                 "Foundation", "Board(")

    def test_no_rule_tokens_in_ui_sources(self):
        root = pathlib.Path(__file__).resolve().parent.parent / "solitaire" / "ui"
        sources = list(root.glob("*.py"))
        self.assertGreaterEqual(len(sources), 3)
        for path in sources:
            text = path.read_text(encoding="utf-8")
            for token in self.FORBIDDEN:
                self.assertNotIn(token, text, f"{path.name} contém {token!r}")


if __name__ == "__main__":
    unittest.main()
