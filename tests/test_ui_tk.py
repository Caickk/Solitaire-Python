"""Teste de fumaça da janela Tkinter. Pulado se não houver Tkinter ou display."""

import random
import unittest

try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    tk = None

from solitaire.game import Game
from solitaire.location import STOCK_REF, WASTE_REF


class Event:
    def __init__(self, x, y):
        self.x, self.y = x, y


@unittest.skipIf(tk is None, "tkinter indisponível")
class TkSmokeTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("sem display")
        from solitaire.ui.app import SolitaireApp
        self.game = Game(random.Random(1))
        self.app = SolitaireApp(self.root, self.game)

    def tearDown(self):
        if hasattr(self, "root"):
            self.root.destroy()

    def items(self):
        return len(self.app.canvas.find_all())

    def test_initial_draw_has_cards_and_slots(self):
        self.assertGreater(self.items(), 52)            # 13 locais + 52 cartas (várias peças cada)
        self.assertEqual(str(self.app.undo_button["state"]), "disabled")

    def test_observer_redraws_on_game_changes(self):
        before = self.items()
        self.game.draw()
        self.assertEqual(str(self.app.undo_button["state"]), "normal")
        self.assertNotEqual(self.items(), before)
        self.game.undo()
        self.assertEqual(str(self.app.undo_button["state"]), "disabled")
        self.assertEqual(self.items(), before)

    def test_mouse_events_draw_stock(self):
        x, y, w, h = self.app.layout.slot_rect(STOCK_REF)
        self.app._on_press(Event(x + 5, y + 5))
        self.app._on_release(Event(x + 5, y + 5))
        self.assertEqual(len(self.game.cards_at(WASTE_REF)), 1)

    def test_drag_overlay_follows_cursor_without_changing_game(self):
        g = self.game
        self.app.game.draw()
        top = g.top_card(WASTE_REF)
        x, y, w, h = self.app.layout.slot_rect(WASTE_REF)
        self.app._on_press(Event(x + 10, y + 10))
        self.assertIsNotNone(self.app.drag.state)
        self.app._on_motion(Event(300, 300))
        self.assertEqual(g.top_card(WASTE_REF), top)
        self.app._on_release(Event(5, 5))
        self.assertIsNone(self.app.drag.state)

    def test_auto_checkbox_swaps_strategy_without_special_cases(self):
        self.app.auto_enabled.set(False)
        self.app._toggle_auto()
        self.app.auto_play()
        self.assertEqual(self.game.moves_made, 0)
        self.app.auto_enabled.set(True)
        self.app._toggle_auto()
        self.app.auto_play()
        self.assertEqual(self.game.moves_made, 1)

    def test_undo_command(self):
        self.game.draw()
        self.app.undo()
        self.assertEqual(self.game.moves_made, 0)

    def test_victory_message_hides_score(self):
        self.assertEqual(self.app.status["text"], "")


if __name__ == "__main__":
    unittest.main()
