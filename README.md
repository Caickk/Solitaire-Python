# Solitaire (Klondike) em Python

Implementação do Anexo I (Solitaire) do trabalho *Investigando o efeito das LLMs sobre o projeto de software* (EXA871, UEFS).
Testado em Python 3.12; apenas biblioteca padrão (Tkinter para a interface).

## Como executar

```
python -m solitaire                 # abre o jogo
python -m unittest discover         # roda os testes (testes da janela são pulados sem display)
python -m solitaire.simulate -n 1000 --seed 0   # simulação automática (estatísticas de pontuação)
```

Uso: clique no monte para comprar (com o monte vazio, o mesmo clique inicia nova partida); arraste cartas com o mouse
(arrastar uma carta do tableau leva as cartas sobre ela); `Ctrl+Z` desfaz; `A` faz uma jogada automática; a caixa
"Jogo automático ativado" liga/desliga o recurso.

## Estrutura

```
solitaire/
  card.py, deck.py          Cartas (únicas), naipes, ranks, baralho
  stack.py                  Pilha de cartas com visibilidade por posição
  location.py, board.py     Locais (monte, descarte, fundações, colunas), regras de empilhamento, tabuleiro
  action.py, moves.py       Ações reversíveis: compra, movimento, revelação, composta, nula
  play.py                   Jogadas (pedidos): DrawPlay, MovePlay, NoPlay
  game.py                   Núcleo: legalidade, execução, histórico, desfazer, observadores, jogo automático
  view.py                   Visão somente leitura do jogo
  strategy.py               Estratégias: AutoStrategy (RF29) e NullStrategy (desativada)
  serialization.py          Serialização de cartas/sequências (RNF05)
  simulate.py               Simulações automáticas (RF03)
  ui/                       layout.py (geometria), drag.py (arraste), app.py (janela Tkinter)
tests/                      Testes unitários, de integração e de fumaça da janela
```

## Padrões e técnicas usados no código

- **Command + Composite + Null Object** nas ações (`action.py`, `moves.py`); **Template Method** no ciclo de vida de `Action`.
- **Flyweight** em `Card` (uma instância por carta).
- **Observer** para notificar a interface (`Game.add_observer`).
- **Strategy** para o jogo automático (`strategy.py`), com `NullStrategy` como Null Object.
- Polimorfismo nos locais (`can_accept`, `is_accessible`) em vez de condicionais por tipo.
- `Play` (pedido de jogada) separado de `Action` (execução reversível), para jogador e estratégia usarem o mesmo caminho de validação.

## Decisões de interpretação do anexo

- **RF01:** com o monte vazio, a ação de comprar inicia nova partida (não há reciclagem do descarte) e o histórico é zerado.
- **RF10:** "carta acessível" = no tableau, qualquer carta visível; nos demais locais, apenas o topo, se visível.
- **RF14:** as fundações não têm naipe pré-definido; o naipe vem da primeira carta (Ás) colocada.
- **RF21:** mover o topo de uma fundação de volta ao tableau é permitido (o anexo não proíbe). Mover um Rei já na base para outra coluna vazia é legal, mas a estratégia automática não o faz (RF30).
- **RF29:** desempate dentro de uma mesma prioridade por ordem determinística (fundações e colunas por índice; cartas da base ao topo).
- **RF28:** a interface oferece botão/atalho e uma caixa para desativar o jogo automático.

## Rastreabilidade: requisito → módulo → testes

| Req. | Descrição | Módulos | Testes (`tests/`) |
|---|---|---|---|
| RF01 | Nova partida | `game.py` | `test_game.py::test_rf01_rf16_initial_layout`<br>`test_game.py::test_rf01_draw_with_empty_stock_starts_new_game` |
| RF02 | Vitória | `game.py` | `test_game.py::test_rf02_victory_only_with_52` |
| RF03 | Pontuação | `game.py, simulate.py` | `test_game.py::test_rf03_score_counts_foundation_cards`<br>`test_strategy.py::test_rf03_simulation_statistics` |
| RF04 | Composição e unicidade | `card.py` | `test_card_deck.py::test_rf04_52_unique_cards`<br>`test_card_deck.py::test_rf04_single_entity` |
| RF05 | Ordem dos ranks | `card.py` | `test_card_deck.py::test_rf05_rank_order`<br>`test_card_deck.py::test_rf05_immediately_above_below` |
| RF06 | Cor dos naipes | `card.py` | `test_card_deck.py::test_rf06_colors` |
| RF07 | Embaralhamento | `deck.py` | `test_card_deck.py::test_rf07_shuffle_is_permutation`<br>`test_card_deck.py::test_rf07_shuffle_varies_and_is_reproducible` |
| RF08 | Pilha | `stack.py` | `test_stack.py::test_rf08_preserves_order_base_to_top` |
| RF09 | Consultas à pilha | `stack.py` | `test_stack.py::test_rf09_empty_and_peek_do_not_alter` |
| RF10 | Locais | `location.py, board.py` | `test_locations_board.py::test_rf10_*` |
| RF11 | Compra | `moves.py, play.py` | `test_game.py::test_rf11_*` |
| RF12 | Desfazer compra | `moves.py` | `test_game.py::test_rf11_rf12_draw_and_undo`<br>`test_actions.py::test_rf12_undo_returns_same_card_to_stock` |
| RF13 | Restrição do descarte | `location.py` | `test_game.py::test_rf13_waste_is_not_a_destination` |
| RF14 | Estrutura das fundações | `board.py, location.py` | `test_locations_board.py::test_rf10_structure`<br>`test_game.py::test_rf15_foundation_same_suit_next_rank` |
| RF15 | Empilhamento nas fundações | `location.py` | `test_game.py::test_rf15_*` |
| RF16 | Organização inicial do tableau | `game.py` | `test_game.py::test_rf01_rf16_initial_layout` |
| RF17 | Empilhamento no tableau | `location.py` | `test_game.py::test_rf17_*` |
| RF18 | Movimentação de sequências | `moves.py, stack.py` | `test_game.py::test_rf18_sequence_moves_together`<br>`test_ui_logic.py::test_rf32_sequence_drag_takes_all_cards_above` |
| RF19 | Revelação automática | `play.py, moves.py` | `test_game.py::test_rf19_*` |
| RF20 | Consultas ao tableau | `location.py, game.py` | `test_locations_board.py::test_rf20_*`<br>`test_game.py::test_rf20_queries` |
| RF21 | Legalidade | `board.py, location.py, game.py` | `test_game.py::test_rf21_*` |
| RF22 | Ações reversíveis | `action.py, moves.py` | `test_actions.py::test_rf22_*` |
| RF23 | Ação composta | `action.py` | `test_actions.py::test_rf23_*` |
| RF24 | Ação nula | `action.py` | `test_actions.py::test_rf24_null_action` |
| RF25 | Histórico e desfazer | `game.py` | `test_game.py::test_rf25_*`<br>`test_strategy.py::test_rf25_*` |
| RF26 | Notificação | `game.py` | `test_game.py::test_rf26_events_for_do_undo_and_null` |
| RF27 | Consulta somente leitura | `game.py, view.py` | `test_game.py::test_rf27_*` |
| RF28 | Jogada automática | `strategy.py, game.py` | `test_strategy.py::test_rf28_*` |
| RF29 | Ordem de prioridade | `strategy.py` | `test_strategy.py::test_1_*`<br>`test_strategy.py::test_2_*`<br>`test_strategy.py::test_3_*`<br>`test_strategy.py::test_4_*`<br>`test_strategy.py::test_5_*`<br>`test_strategy.py::test_6_*`<br>`test_strategy.py::test_7_*` |
| RF30 | Sem ciclos | `strategy.py` | `test_strategy.py::test_rf30_*` |
| RF31 | Decidir × executar | `strategy.py, view.py, game.py` | `test_strategy.py::test_rf31_*` |
| RF32 | Movimentação direta | `ui/drag.py, ui/layout.py, ui/app.py` | `test_ui_logic.py::test_rf32_*`<br>`test_ui_tk.py::test_drag_overlay_follows_cursor_without_changing_game` |
| RNF01 | Consistência de visibilidade | `stack.py` | `test_stack.py::test_rnf01_*`<br>`test_game.py::test_rf25_undo_all_restores_initial_state_and_is_ready_to_continue` |
| RNF02 | Tratamento uniforme de ações | `action.py, play.py, game.py` | `test_actions.py::test_rnf02_uniform_treatment`<br>`test_strategy.py::test_rf28_null_strategy_does_nothing_with_no_special_handling` |
| RNF03 | Apresentação × regras | `ui/` | `test_ui_logic.py::test_no_rule_tokens_in_ui_sources`<br>`test_ui_logic.py::test_rf32_target_indication_comes_from_game_rules` |
| RNF04 | Estratégia × regras | `view.py, strategy.py` | `test_strategy.py::test_rnf04_view_has_only_queries` |
| RNF05 | Fidelidade na serialização | `card.py, serialization.py` | `test_serialization.py::*`<br>`test_card_deck.py::test_rnf05_*` |

`*` ao final do nome indica todos os testes com aquele prefixo.

## Estado da verificação

- 126 testes passando (inclui testes da janela, executados em display virtual Xvfb).
- Cobertura de linhas medida com `coverage`: 95% do pacote `solitaire`.
- Simulação de referência (1000 partidas, `--seed 0`): 22 vitórias (2,2%), pontuação média 8,06, média de 49,2 jogadas por partida, sem ciclos.
- **Não verificado:** execução com mouse físico em Windows e a aparência dos símbolos dos naipes com a fonte `Segoe UI Symbol` (a verificação visual foi feita em Linux).
