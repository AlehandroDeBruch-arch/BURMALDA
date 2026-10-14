import flet as ft
import random
import asyncio
import datetime
import os
from abc import ABC, abstractmethod

BG, PANEL, ACCENT, DANGER, SUCCESS = "#0f0f1e", "#1a1a2e", "#ffd700", "#ff4757", "#2ed573"
FMT = "%d.%m.%Y %H:%M:%S"


class Entity(ABC):
    @abstractmethod
    def describe(self) -> str: ...

    @abstractmethod
    def identifier(self) -> str: ...


class SymbolMap(Entity):
    def __init__(self):
        self._k: list[str] = []
        self._v: list[int] = []

    def put(self, k, v):
        if k in self._k:
            self._v[self._k.index(k)] = v
        else:
            self._k.append(k); self._v.append(v)

    def get(self, k, d=0):
        return self._v[self._k.index(k)] if k in self._k else d

    def __len__(self): return len(self._k)
    def describe(self): return f"SymbolMap({len(self._k)})"
    def identifier(self): return "symbol_map"
    def __repr__(self): return f"SymbolMap({self._k!r}, {self._v!r})"
    def __str__(self): return " ".join(f"{a}:{b}" for a, b in zip(self._k, self._v))
    def __eq__(self, o): return isinstance(o, SymbolMap) and self._k == o._k and self._v == o._v


class SlotSymbol(Entity):
    def __init__(self, icon: str, weight: int, payout: int):
        self._icon, self._weight, self._payout = icon, weight, payout

    @property
    def icon(self): return self._icon
    @icon.setter
    def icon(self, v): self._icon = v
    @property
    def weight(self): return self._weight
    @weight.setter
    def weight(self, v): self._weight = v
    @property
    def payout(self): return self._payout
    @payout.setter
    def payout(self, v): self._payout = v

    def describe(self): return f"{self._icon} w={self._weight} p={self._payout}"
    def identifier(self): return self._icon
    def __repr__(self): return f"SlotSymbol({self._icon!r},{self._weight},{self._payout})"
    def __str__(self): return self._icon
    def __eq__(self, o): return isinstance(o, SlotSymbol) and self._icon == o._icon
    def __hash__(self): return hash(self._icon)
    def __lt__(self, o): return self._weight < o._weight


class Player(Entity):
    def __init__(self, login: str):
        self._login = login
        self._tin: datetime.datetime = datetime.datetime.now()
        self._tout: datetime.datetime | None = None

    @property
    def login(self): return self._login
    @login.setter
    def login(self, v): self._login = v
    @property
    def time_in(self): return self._tin
    @time_in.setter
    def time_in(self, v): self._tin = v
    @property
    def time_out(self): return self._tout
    @time_out.setter
    def time_out(self, v): self._tout = v

    def describe(self): return f"Player {self._login}"
    def identifier(self): return self._login
    def __repr__(self): return f"Player({self._login!r})"
    def __str__(self): return self._login
    def __eq__(self, o): return isinstance(o, Player) and self._login == o._login
    def __hash__(self): return hash(self._login)


class SlotMachine(Entity):
    START, JACKPOT = 1000, 0.002

    def __init__(self):
        self._balance, self._bet, self._spinning = self.START, 10, False
        self._payouts = SymbolMap()
        self._symbols: list[SlotSymbol] = []
        for icon, w, p in [("🍒", 25, 5), ("🍋", 25, 8), ("🍊", 20, 12),
                           ("🔔", 15, 20), ("💎", 8, 50), ("7️⃣", 5, 100), ("⭐", 2, 500)]:
            self._symbols.append(SlotSymbol(icon, w, p))
            self._payouts.put(icon, p)

    @property
    def balance(self): return self._balance
    @balance.setter
    def balance(self, v): self._balance = v
    @property
    def bet(self): return self._bet
    @bet.setter
    def bet(self, v): self._bet = v
    @property
    def spinning(self): return self._spinning
    @spinning.setter
    def spinning(self, v): self._spinning = v
    @property
    def symbols(self): return self._symbols
    @property
    def payouts(self): return self._payouts

    @staticmethod
    def weighted(symbols): return random.choices(symbols, weights=[s.weight for s in symbols], k=1)[0]

    @staticmethod
    def evaluate(reels, bet, payouts):
        a, b, c = reels
        if a == b == c: return bet * payouts.get(a.icon, 1)
        if a == b or b == c or a == c: return bet * 2
        return 0

    def spin(self):
        if self._balance < self._bet: return None
        self._balance -= self._bet
        if random.random() < self.JACKPOT:
            s = next(x for x in self._symbols if x.icon == "⭐")
            return [s, s, s]
        return [self.weighted(self._symbols) for _ in range(3)]

    def apply_win(self, w): self._balance += w

    def adjust_bet(self, d):
        self._bet = max(1, min(self._bet + d, max(1, self._balance)))

    def describe(self): return f"SlotMachine({self._balance})"
    def identifier(self): return "slot_machine"
    def __repr__(self): return f"SlotMachine({self._balance},{self._bet})"
    def __str__(self): return f"🎰 {self._balance}"
    def __eq__(self, o): return isinstance(o, SlotMachine) and self._balance == o._balance


class TitleHeader(ft.Container):
    def __init__(self):
        super().__init__(padding=ft.Padding.only(top=20, bottom=10), alignment=ft.Alignment.CENTER)
        self.content = ft.Column(
            [ft.Text("🎰 СЛОТЫ БУРМАЛОТЫ 🎰", size=26, weight=ft.FontWeight.BOLD, color=ACCENT),
             ft.Text("ИСПЫТАЙ СВОЮ УДАЧУ", size=13, color="#7f8fa6")],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
    def __str__(self): return "TitleHeader"
    def __eq__(self, o): return isinstance(o, TitleHeader)


class BalancePanel(ft.Container):
    def __init__(self, v):
        super().__init__(padding=ft.Padding.symmetric(horizontal=30, vertical=12),
                         bgcolor=PANEL, border_radius=16,
                         border=ft.Border.all(1, "#2a2a45"), alignment=ft.Alignment.CENTER)
        self._t = ft.Text(f"${v}", size=32, weight=ft.FontWeight.BOLD, color=ACCENT)
        self.content = ft.Column([ft.Text("Баланс", size=12, color="#7f8fa6"), self._t],
                                 horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
    def set_value(self, v): self._t.value = f"${v}"
    def __str__(self): return f"Balance({self._t.value})"
    def __eq__(self, o): return isinstance(o, BalancePanel) and self._t.value == o._t.value


class ReelView(ft.Container):
    def __init__(self):
        super().__init__(width=110, height=130, bgcolor=PANEL, border_radius=16,
                         alignment=ft.Alignment.CENTER,
                         border=ft.Border.all(2, "#2a2a45"),
                         shadow=ft.BoxShadow(blur_radius=20, color="#000", offset=ft.Offset(0, 4)),
                         animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT))
        self._t = ft.Text("❓", size=64, color="white")
        self.content = self._t
    def set_symbol(self, s, size=64): self._t.value, self._t.size = s, size
    def highlight(self, on): self.border = ft.Border.all(2, ACCENT if on else "#2a2a45")
    def scale_to(self, s): self.scale = ft.Scale(s)
    def __str__(self): return f"Reel({self._t.value})"
    def __eq__(self, o): return isinstance(o, ReelView) and self._t.value == o._t.value


class ResultPanel(ft.Container):
    def __init__(self, txt):
        super().__init__(padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                         bgcolor=PANEL, border_radius=12, width=360, alignment=ft.Alignment.CENTER)
        self._t = ft.Text(txt, size=20, weight=ft.FontWeight.BOLD,
                          color="#cfd8dc", text_align=ft.TextAlign.CENTER)
        self.content = self._t
    def set_result(self, t, c): self._t.value, self._t.color = t, c
    def __str__(self): return f"Result({self._t.value})"
    def __eq__(self, o): return isinstance(o, ResultPanel) and self._t.value == o._t.value


class SpinButton(ft.Container):
    def __init__(self, handler):
        super().__init__(width=220, height=60, bgcolor=ACCENT, border_radius=30,
                         alignment=ft.Alignment.CENTER, ink=True,
                         shadow=ft.BoxShadow(blur_radius=25, color=ACCENT, spread_radius=1),
                         on_click=handler)
        self.content = ft.Text("КРУТИТЬ", size=22, weight=ft.FontWeight.BOLD, color="#1a1a2e")
    def set_enabled(self, en): self.ink, self.opacity = en, 1.0 if en else 0.5
    def __str__(self): return "SpinButton"
    def __eq__(self, o): return isinstance(o, SpinButton)


class BetButton(ft.Container):
    def __init__(self, label, delta, handler):
        super().__init__(width=70, height=44, bgcolor=PANEL, border_radius=12,
                         alignment=ft.Alignment.CENTER, ink=True,
                         on_click=lambda e: handler(delta))
        self.content = ft.Text(label, size=16, weight=ft.FontWeight.BOLD, color="white")
    def __str__(self): return f"BetButton({self.content.value})"
    def __eq__(self, o): return isinstance(o, BetButton) and self.content.value == o.content.value


class BetLabel(ft.Text):
    def __init__(self, v): super().__init__(value=f"Ставка: ${v}", size=18, color="#cfd8dc")
    def set_bet(self, v): self.value = f"Ставка: ${v}"
    def __str__(self): return self.value
    def __eq__(self, o): return isinstance(o, BetLabel) and self.value == o.value


class PayoutsHint(ft.Text):
    def __init__(self):
        super().__init__(value="Расценки: 🍒x5 🍋x8 🍊x12 🔔x20 💎x50 7️⃣x100 ⭐x500 | Любая пара x2",
                         size=10, color="#7f8fa6", text_align=ft.TextAlign.CENTER)
    def __str__(self): return "PayoutsHint"
    def __eq__(self, o): return isinstance(o, PayoutsHint)


class Spacer(ft.Container):
    def __init__(self, h=10): super().__init__(height=h)
    def __str__(self): return "Spacer"
    def __eq__(self, o): return isinstance(o, Spacer) and self.height == o.height


class ReelRow(ft.Row):
    def __init__(self, reels):
        super().__init__(controls=reels, alignment=ft.MainAxisAlignment.CENTER, spacing=14)
    def __str__(self): return "ReelRow"
    def __eq__(self, o): return isinstance(o, ReelRow)


class SlotApp(Entity):
    def __init__(self, page: ft.Page, player: Player):
        self._page, self._player = page, player
        self._game = SlotMachine()
        self._reels = [ReelView() for _ in range(3)]
        self._init_page()
        self._init_ui()

    @property
    def page(self): return self._page
    @property
    def player(self): return self._player
    @property
    def game(self): return self._game

    def _init_page(self):
        p = self._page
        p.title = "NeNaeb-Inator.bet"
        p.bgcolor = BG
        p.window.width, p.window.height, p.window.resizable = 460, 800, False
        p.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        p.vertical_alignment = ft.MainAxisAlignment.START
        p.scroll = ft.ScrollMode.AUTO

    def _init_ui(self):
        self._bal = BalancePanel(self._game.balance)
        self._res = ResultPanel("Нажми КРУТИТЬ что бы сыграть!")
        self._bet_lbl = BetLabel(self._game.bet)
        self._spin_btn = SpinButton(self._on_spin)
        self._page.add(
            TitleHeader(), self._bal, Spacer(10), ReelRow(self._reels), Spacer(15),
            self._res, Spacer(20),
            ft.Column([
                self._bet_lbl,
                ft.Row([BetButton("− $5", -5, self._on_bet), BetButton("− $1", -1, self._on_bet),
                        BetButton("+ $1", 1, self._on_bet), BetButton("+ $5", 5, self._on_bet)],
                       alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                Spacer(8), self._spin_btn,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            Spacer(10), PayoutsHint())

    def _on_bet(self, d):
        if self._game.spinning: return
        self._game.adjust_bet(d)
        self._bet_lbl.set_bet(self._game.bet)
        self._page.update()

    def _on_spin(self, e):
        if self._game.spinning: return
        if self._game.balance < self._game.bet:
            self._res.set_result("💸 Недостаточно средств :(", DANGER); self._page.update(); return
        self._page.run_task(self._do_spin)

    async def _spin_reel(self, i, dur, final):
        r = self._reels[i]; r.highlight(True); self._page.update()
        delay, total = 0.04, 0.0
        for _ in range(18 + i * 4):
            r.set_symbol(random.choice([s.icon for s in self._game.symbols]),
                         size=64 + random.randint(-4, 4))
            self._page.update(); await asyncio.sleep(delay); total += delay
            if total > dur * 0.4: delay = min(delay * 1.15, 0.18)
        r.set_symbol(final); self._page.update(); await asyncio.sleep(0.1)

    async def _do_spin(self):
        self._game.spinning = True
        self._spin_btn.set_enabled(False)
        self._res.set_result("🎰 Идет прокрутка...", ACCENT)
        self._bal.set_value(self._game.balance - self._game.bet)
        self._page.update()

        result = self._game.spin()
        await asyncio.gather(*[asyncio.create_task(
            self._spin_reel(i, 0.6 + i * 0.35, result[i].icon)) for i in range(3)])
        for r in self._reels: r.highlight(True)

        win = SlotMachine.evaluate(result, self._game.bet, self._game.payouts)
        self._game.apply_win(win); self._bal.set_value(self._game.balance)

        if win > 0:
            if all(s.icon == "⭐" for s in result):
                self._res.set_result(f"🌟 ДЖЕКПОТ! +${win} 🌟", ACCENT)
            elif result[0] == result[1] == result[2]:
                self._res.set_result(f"🎉 УЛЬТРАМЕГАХОРОШ! +${win}", SUCCESS)
            else:
                self._res.set_result(f"✨ Ты выиграл! ${win}!", SUCCESS)
            for _ in range(3):
                for r in self._reels: r.scale_to(1.08)
                self._page.update(); await asyncio.sleep(0.12)
                for r in self._reels: r.scale_to(1.0)
                self._page.update(); await asyncio.sleep(0.12)
        else:
            self._res.set_result("Не повезло. Попробуй еще раз!", "#cfd8dc")

        self._page.update(); await asyncio.sleep(0.6)
        for r in self._reels: r.highlight(False); r.scale_to(1.0)
        self._page.update()

        self._game.spinning = False
        self._spin_btn.set_enabled(True)
        if self._game.balance < 1:
            self._res.set_result("Игра окончена", DANGER); self._page.update()

    def save_report(self):
        self._player.time_out = datetime.datetime.now()
        fmt = FMT
        lines = ["+---", "| login | time_in | time_out |", "|---|", "|---|",
                 f"|{self._player.login} | {self._player.time_in.strftime(fmt)} "
                 f"| {self._player.time_out.strftime(fmt)} |", "+---"]
        path = os.path.join(os.getenv("FLET_APP_STORAGE_DATA", "."), "slot_report.txt")
        try:
            with open(path, "w", encoding="utf-8") as f: f.write("\n".join(lines))
            print(f"Отчёт сохранён: {path}")
        except Exception as ex:
            print(f"Ошибка отчёта: {ex}")

    def describe(self): return f"SlotApp({self._player.login})"
    def identifier(self): return "slot_app"
    def __repr__(self): return f"SlotApp({self._player!r})"
    def __str__(self): return f"🎰 {self._player.login}"
    def __eq__(self, o): return isinstance(o, SlotApp) and self._player == o._player


def main(page: ft.Page):
    app = SlotApp(page, Player("UserName"))
    page.on_disconnect = lambda e: app.save_report()


if __name__ == "__main__":
    ft.run(main)