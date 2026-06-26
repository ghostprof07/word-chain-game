import random
import string
import threading
import urllib.request
import urllib.error
import json

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.properties import (
    NumericProperty, StringProperty, ColorProperty, BooleanProperty
)
from kivy.core.window import Window
from kivy.metrics import dp

Window.clearcolor = (0.05, 0.05, 0.05, 1)

LETTER_SCORES = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 2, 'h': 4,
    'i': 1, 'j': 8, 'k': 5, 'l': 1, 'm': 3, 'n': 1, 'o': 1, 'p': 3,
    'q': 10, 'r': 1, 's': 1, 't': 1, 'u': 1, 'v': 4, 'w': 4, 'x': 8,
    'y': 4, 'z': 10,
}

_word_cache = {}


def calculate_score(word):
    return sum(LETTER_SCORES.get(ch, 0) for ch in word.lower())


def validate_word_online(word, callback):
    """Runs in a background thread; calls callback(True/False) on main thread."""
    key = word.lower()
    if key in _word_cache:
        Clock.schedule_once(lambda dt: callback(_word_cache[key]), 0)
        return

    def _run():
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{key}"
            req = urllib.request.Request(url, headers={"User-Agent": "WordChainGame/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                valid = resp.status == 200
        except urllib.error.HTTPError as e:
            valid = False
        except Exception:
            valid = True   # network error — give benefit of the doubt
        _word_cache[key] = valid
        Clock.schedule_once(lambda dt: callback(valid), 0)

    threading.Thread(target=_run, daemon=True).start()


Builder.load_string(r"""
#:import dp kivy.metrics.dp

<RoundButton@Button>:
    background_normal: ''
    background_color: 0, 0, 0, 0
    canvas.before:
        Color:
            rgba: self.bg_color if not self.disabled else (0.3, 0.3, 0.3, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
    bg_color: (0, 0.78, 0.32, 1)
    color: (0, 0, 0, 1)
    bold: True
    font_size: dp(18)

<RuleRow@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(64)
    spacing: dp(12)
    padding: dp(14)
    icon_text: '?'
    icon_color: (1,1,1,1)
    title_text: ''
    desc_text: ''
    canvas.before:
        Color:
            rgba: (0.1, 0.1, 0.1, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
    Label:
        size_hint_x: None
        width: dp(36)
        text: root.icon_text
        font_size: dp(22)
        color: root.icon_color
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(2)
        Label:
            text: root.title_text
            bold: True
            font_size: dp(13)
            halign: 'left'
            text_size: self.size
            valign: 'bottom'
        Label:
            text: root.desc_text
            font_size: dp(11)
            color: (0.6, 0.6, 0.6, 1)
            halign: 'left'
            text_size: self.size
            valign: 'top'

<HomeScreen>:
    name: 'home'
    canvas.before:
        Color:
            rgba: (0.05, 0.05, 0.05, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(28)
        spacing: dp(14)
        Label:
            size_hint_y: None
            height: dp(20)
        Label:
            text: 'WORD\nCHAIN'
            font_size: dp(56)
            bold: True
            halign: 'center'
            color: (0, 0.78, 0.32, 1)
            size_hint_y: None
            height: dp(130)
        Label:
            text: 'Chain words — each word must start\nwith the last letter of the previous one.'
            font_size: dp(13)
            halign: 'center'
            color: (0.6, 0.6, 0.6, 1)
            size_hint_y: None
            height: dp(48)
        Widget:
            size_hint_y: None
            height: dp(10)
        RuleRow:
            icon_text: '\U0001f517'
            icon_color: (0, 0.78, 0.32, 1)
            title_text: 'Chain Rule'
            desc_text: 'Next word must begin with the last letter of the previous word.'
        RuleRow:
            icon_text: '⏱'
            icon_color: (1, 0.43, 0, 1)
            title_text: '20s Per Turn'
            desc_text: 'You have 20 seconds per turn and 5 minutes total.'
        RuleRow:
            icon_text: '★'
            icon_color: (1, 0.84, 0, 1)
            title_text: 'Scrabble Scoring'
            desc_text: 'Rare letters (Q, Z, X, J) score higher.'
        Widget:
        RoundButton:
            text: 'START GAME'
            size_hint_y: None
            height: dp(58)
            on_press: root.start_game()
        Widget:
            size_hint_y: None
            height: dp(10)

<PlayerCard@BoxLayout>:
    orientation: 'vertical'
    spacing: dp(4)
    padding: dp(10)
    label_text: 'PLAYER ?'
    score_text: '0'
    active: False
    card_color: (0, 0.78, 0.32, 1)
    canvas.before:
        Color:
            rgba: (self.card_color[0], self.card_color[1], self.card_color[2], 0.15) if self.active else (0.1, 0.1, 0.1, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
        Color:
            rgba: self.card_color if self.active else (1,1,1,0.08)
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(12))
            width: 2 if self.active else 1
    Label:
        text: root.label_text
        font_size: dp(10)
        bold: True
        color: root.card_color if root.active else (0.5, 0.5, 0.5, 1)
        halign: 'center'
    Label:
        text: root.score_text
        font_size: dp(36)
        bold: True
        color: (1,1,1,1) if root.active else (0.5,0.5,0.5,1)
        halign: 'center'

<GameScreen>:
    name: 'game'
    canvas.before:
        Color:
            rgba: (0.05, 0.05, 0.05, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: [dp(20), dp(12), dp(20), dp(12)]
        spacing: dp(10)

        # --- Top bar ---
        BoxLayout:
            size_hint_y: None
            height: dp(36)
            Label:
                id: total_timer_label
                text: '05:00'
                font_size: dp(20)
                bold: True
                color: (0.5, 0.5, 0.5, 1)
                halign: 'left'
                text_size: self.size
                valign: 'middle'
            Label:
                id: words_label
                text: '0 words'
                font_size: dp(13)
                color: (0.4, 0.4, 0.4, 1)
                halign: 'center'
                text_size: self.size
                valign: 'middle'
            Button:
                text: 'QUIT'
                font_size: dp(12)
                color: (0.4, 0.4, 0.4, 1)
                background_normal: ''
                background_color: 0, 0, 0, 0
                size_hint_x: None
                width: dp(50)
                on_press: root.confirm_quit()

        # --- Player cards ---
        BoxLayout:
            size_hint_y: None
            height: dp(90)
            spacing: dp(12)
            PlayerCard:
                id: p1_card
                label_text: 'PLAYER 1'
                score_text: '0'
                active: True
                card_color: (0, 0.78, 0.32, 1)
            PlayerCard:
                id: p2_card
                label_text: 'PLAYER 2'
                score_text: '0'
                active: False
                card_color: (0, 0.9, 1, 1)

        # --- Required letter circle ---
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: dp(200)
            spacing: dp(6)
            Label:
                id: turn_hint
                text: 'PLAYER 1 — starts with'
                font_size: dp(12)
                color: (0.5, 0.5, 0.5, 1)
                halign: 'center'
            Widget:
                id: letter_circle_widget
                size_hint_y: None
                height: dp(120)
                canvas:
                    Color:
                        rgba: (0.1, 0.1, 0.1, 1)
                    Ellipse:
                        pos: (self.center_x - dp(55), self.center_y - dp(55))
                        size: (dp(110), dp(110))
                    Color:
                        rgba: (0, 0.78, 0.32, 1)
                    Line:
                        ellipse: (self.center_x - dp(55), self.center_y - dp(55), dp(110), dp(110))
                        width: dp(2.5)
                Label:
                    id: letter_label
                    text: 'A'
                    font_size: dp(68)
                    bold: True
                    color: (1, 1, 1, 1)
                    center: letter_circle_widget.center
                    size: letter_circle_widget.size
                    pos: letter_circle_widget.pos
                    halign: 'center'
                    valign: 'middle'
                    text_size: self.size

            # Turn timer bar
            BoxLayout:
                size_hint_y: None
                height: dp(30)
                orientation: 'vertical'
                spacing: dp(2)
                Widget:
                    size_hint_y: None
                    height: dp(6)
                    canvas:
                        Color:
                            rgba: (1,1,1,0.08)
                        RoundedRectangle:
                            pos: (self.center_x - dp(100), self.y)
                            size: (dp(200), dp(6))
                            radius: [dp(3)]
                        Color:
                            rgba: app.root.get_screen('game').timer_bar_color
                        RoundedRectangle:
                            pos: (self.center_x - dp(100), self.y)
                            size: (dp(200) * app.root.get_screen('game').timer_fraction, dp(6))
                            radius: [dp(3)]
                Label:
                    id: turn_timer_label
                    text: '20'
                    font_size: dp(16)
                    bold: True
                    halign: 'center'

        # --- Last word hint ---
        Label:
            id: last_word_label
            text: ''
            font_size: dp(13)
            color: (0.4, 0.4, 0.4, 1)
            size_hint_y: None
            height: dp(20)
            halign: 'center'

        Widget:

        # --- Status ---
        Label:
            id: status_label
            text: 'Game started!'
            font_size: dp(15)
            bold: True
            halign: 'center'
            size_hint_y: None
            height: dp(28)

        # --- Input ---
        TextInput:
            id: word_input
            multiline: False
            font_size: dp(28)
            size_hint_y: None
            height: dp(58)
            halign: 'center'
            hint_text: 'Type a word…'
            hint_text_color: (0.3, 0.3, 0.3, 1)
            background_color: (0.1, 0.1, 0.1, 1)
            foreground_color: (1, 1, 1, 1)
            cursor_color: (0, 0.78, 0.32, 1)
            padding: [dp(16), dp(14)]
            on_text_validate: root.submit_word()

        # --- Submit button ---
        RoundButton:
            id: submit_btn
            text: 'SUBMIT'
            size_hint_y: None
            height: dp(58)
            on_press: root.submit_word()

        Widget:
            size_hint_y: None
            height: dp(6)

<ResultScreen>:
    name: 'result'
    canvas.before:
        Color:
            rgba: (0.05, 0.05, 0.05, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(24)
        spacing: dp(14)
        Widget:
            size_hint_y: None
            height: dp(20)
        Label:
            text: 'FINAL SCORE'
            font_size: dp(13)
            color: (0.5, 0.5, 0.5, 1)
            bold: True
            halign: 'center'
            size_hint_y: None
            height: dp(20)
        Label:
            id: winner_label
            text: 'PLAYER 1 WINS!'
            font_size: dp(36)
            bold: True
            halign: 'center'
            size_hint_y: None
            height: dp(54)
        BoxLayout:
            size_hint_y: None
            height: dp(110)
            spacing: dp(14)
            BoxLayout:
                id: p1_result_box
                orientation: 'vertical'
                spacing: dp(4)
                padding: dp(14)
                canvas.before:
                    Color:
                        rgba: (0.1, 0.1, 0.1, 1)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(14)]
                Label:
                    id: p1_result_label
                    text: 'PLAYER 1'
                    font_size: dp(11)
                    bold: True
                    color: (0, 0.78, 0.32, 1)
                    halign: 'center'
                Label:
                    id: p1_score_label
                    text: '0'
                    font_size: dp(48)
                    bold: True
                    halign: 'center'
                Label:
                    text: 'pts'
                    font_size: dp(12)
                    color: (0.5,0.5,0.5,1)
                    halign: 'center'
            BoxLayout:
                id: p2_result_box
                orientation: 'vertical'
                spacing: dp(4)
                padding: dp(14)
                canvas.before:
                    Color:
                        rgba: (0.1, 0.1, 0.1, 1)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(14)]
                Label:
                    id: p2_result_label
                    text: 'PLAYER 2'
                    font_size: dp(11)
                    bold: True
                    color: (0, 0.9, 1, 1)
                    halign: 'center'
                Label:
                    id: p2_score_label
                    text: '0'
                    font_size: dp(48)
                    bold: True
                    halign: 'center'
                Label:
                    text: 'pts'
                    font_size: dp(12)
                    color: (0.5,0.5,0.5,1)
                    halign: 'center'
        # Stats row
        BoxLayout:
            size_hint_y: None
            height: dp(70)
            spacing: dp(10)
            canvas.before:
                Color:
                    rgba: (0.1, 0.1, 0.1, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(12)]
            Label:
                id: stat_words
                text: '0\n[size=10][color=666666]Words[/color][/size]'
                markup: True
                font_size: dp(24)
                bold: True
                halign: 'center'
            Label:
                id: stat_total
                text: '0\n[size=10][color=666666]Total pts[/color][/size]'
                markup: True
                font_size: dp(24)
                bold: True
                halign: 'center'
            Label:
                id: stat_avg
                text: '0\n[size=10][color=666666]Avg/word[/color][/size]'
                markup: True
                font_size: dp(24)
                bold: True
                halign: 'center'
        # Words used
        Label:
            text: 'Words Used'
            font_size: dp(12)
            color: (0.5,0.5,0.5,1)
            size_hint_y: None
            height: dp(20)
            halign: 'left'
            text_size: self.size
            valign: 'middle'
        ScrollView:
            Label:
                id: words_used_label
                text: ''
                font_size: dp(13)
                color: (0.7, 0.7, 0.7, 1)
                halign: 'left'
                valign: 'top'
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
        Widget:
        RoundButton:
            text: 'PLAY AGAIN'
            size_hint_y: None
            height: dp(58)
            on_press: root.play_again()
        Widget:
            size_hint_y: None
            height: dp(10)
""")


class HomeScreen(Screen):
    def start_game(self):
        game = self.manager.get_screen('game')
        game.reset()
        self.manager.current = 'game'


class GameScreen(Screen):
    timer_fraction = NumericProperty(1.0)
    timer_bar_color = ColorProperty([0, 0.78, 0.32, 1])

    TOTAL_TIME = 300
    TURN_TIME = 20

    def reset(self):
        self._total_time = self.TOTAL_TIME
        self._turn_time = self.TURN_TIME
        self._current_player = 1
        self._scores = {1: 0, 2: 0}
        self._used_words = set()
        self._last_word = ''
        self._validating = False

        self._required_letter = random.choice(string.ascii_lowercase)

        self.ids.letter_label.text = self._required_letter.upper()
        self.ids.turn_hint.text = 'PLAYER 1 — starts with'
        self.ids.p1_card.active = True
        self.ids.p2_card.active = False
        self.ids.p1_card.score_text = '0'
        self.ids.p2_card.score_text = '0'
        self.ids.last_word_label.text = ''
        self.ids.status_label.text = 'Game started!'
        self.ids.status_label.color = (1, 1, 0, 1)
        self.ids.word_input.text = ''
        self.ids.submit_btn.disabled = False
        self.timer_fraction = 1.0
        self.timer_bar_color = [0, 0.78, 0.32, 1]

        self._update_top_bar()
        if hasattr(self, '_timer_event') and self._timer_event:
            self._timer_event.cancel()
        self._timer_event = Clock.schedule_interval(self._tick, 1)

    def _tick(self, dt):
        self._total_time -= 1
        self._turn_time -= 1

        self._update_top_bar()
        self._update_turn_timer()

        if self._total_time <= 0 or self._turn_time <= 0:
            self._timer_event.cancel()
            self._end_game()

    def _update_top_bar(self):
        m = self._total_time // 60
        s = self._total_time % 60
        self.ids.total_timer_label.text = f"{m:02d}:{s:02d}"
        self.ids.words_label.text = f"{len(self._used_words)} words"

    def _update_turn_timer(self):
        t = self._turn_time
        self.ids.turn_timer_label.text = str(t)
        self.timer_fraction = max(0.0, t / self.TURN_TIME)

        if t > 10:
            color = [0, 0.78, 0.32, 1]
            text_color = (0, 0.78, 0.32, 1)
        elif t > 5:
            color = [1, 0.84, 0, 1]
            text_color = (1, 0.84, 0, 1)
        else:
            color = [1, 0.32, 0.32, 1]
            text_color = (1, 0.32, 0.32, 1)

        self.timer_bar_color = color
        self.ids.turn_timer_label.color = text_color

    def submit_word(self):
        if self._validating:
            return
        word = self.ids.word_input.text.strip().lower()
        self.ids.word_input.text = ''

        if not word or not word.isalpha():
            return

        if word in self._used_words:
            self._show_error('Already used!')
            return

        if word[0] != self._required_letter:
            self._show_error(f'Must start with "{self._required_letter.upper()}"')
            return

        self._validating = True
        self.ids.submit_btn.disabled = True
        self.ids.status_label.text = 'Checking…'
        self.ids.status_label.color = (0.6, 0.6, 0.6, 1)

        validate_word_online(word, lambda valid: self._on_validated(word, valid))

    def _on_validated(self, word, valid):
        self._validating = False
        self.ids.submit_btn.disabled = False

        if not valid:
            self._show_error('Not a valid English word!')
            return

        score = calculate_score(word)
        self._scores[self._current_player] += score
        self._used_words.add(word)
        self._last_word = word
        self._required_letter = word[-1]

        # Update UI
        self.ids.letter_label.text = self._required_letter.upper()
        self.ids.last_word_label.text = f'Last: {word}'

        # Pulse animation on letter
        anim = (Animation(font_size=dp(80), duration=0.1) +
                Animation(font_size=dp(68), duration=0.15))
        anim.start(self.ids.letter_label)

        self.ids.status_label.text = f'+{score} points!'
        self.ids.status_label.color = (0, 0.78, 0.32, 1)

        # Switch player
        self._current_player = 2 if self._current_player == 1 else 1
        self._turn_time = self.TURN_TIME
        self._update_turn_timer()

        p1_active = self._current_player == 1
        self.ids.p1_card.active = p1_active
        self.ids.p2_card.active = not p1_active
        self.ids.p1_card.score_text = str(self._scores[1])
        self.ids.p2_card.score_text = str(self._scores[2])
        self.ids.turn_hint.text = f'PLAYER {self._current_player} — starts with'

    def _show_error(self, msg):
        self.ids.status_label.text = msg
        self.ids.status_label.color = (1, 0.32, 0.32, 1)
        # Shake animation
        lbl = self.ids.status_label
        orig_x = lbl.x
        anim = (Animation(x=orig_x + dp(10), duration=0.05) +
                Animation(x=orig_x - dp(10), duration=0.05) +
                Animation(x=orig_x + dp(6), duration=0.05) +
                Animation(x=orig_x, duration=0.05))
        anim.start(lbl)

    def confirm_quit(self):
        from kivy.uix.popup import Popup
        from kivy.uix.gridlayout import GridLayout

        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        content.add_widget(Label(text='Quit game?', font_size=dp(18), bold=True))

        btns = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))
        cancel_btn = Button(text='Cancel', background_normal='',
                            background_color=(0.2, 0.2, 0.2, 1))
        quit_btn = Button(text='Quit', background_normal='',
                          background_color=(0.8, 0.2, 0.2, 1), bold=True)
        btns.add_widget(cancel_btn)
        btns.add_widget(quit_btn)
        content.add_widget(btns)

        popup = Popup(title='', content=content, size_hint=(0.8, None), height=dp(180),
                      separator_height=0, background_color=(0.12, 0.12, 0.12, 1))

        cancel_btn.bind(on_press=popup.dismiss)

        def do_quit(_):
            popup.dismiss()
            if hasattr(self, '_timer_event') and self._timer_event:
                self._timer_event.cancel()
            self.manager.current = 'home'

        quit_btn.bind(on_press=do_quit)
        popup.open()

    def _end_game(self):
        result = self.manager.get_screen('result')
        result.show_results(self._scores, self._used_words)
        self.manager.current = 'result'


class ResultScreen(Screen):
    def show_results(self, scores, used_words):
        p1, p2 = scores[1], scores[2]

        if p1 > p2:
            self.ids.winner_label.text = 'PLAYER 1 WINS!'
            self.ids.winner_label.color = (0, 0.78, 0.32, 1)
        elif p2 > p1:
            self.ids.winner_label.text = 'PLAYER 2 WINS!'
            self.ids.winner_label.color = (0, 0.9, 1, 1)
        else:
            self.ids.winner_label.text = "IT'S A DRAW!"
            self.ids.winner_label.color = (1, 0.84, 0, 1)

        self.ids.p1_score_label.text = str(p1)
        self.ids.p2_score_label.text = str(p2)

        total = p1 + p2
        count = len(used_words)
        avg = f"{total/count:.1f}" if count else '0'

        self.ids.stat_words.text = f'{count}\n[size=10][color=666666]Words[/color][/size]'
        self.ids.stat_total.text = f'{total}\n[size=10][color=666666]Total pts[/color][/size]'
        self.ids.stat_avg.text = f'{avg}\n[size=10][color=666666]Avg/word[/color][/size]'

        self.ids.words_used_label.text = '  '.join(sorted(used_words)) if used_words else '—'

    def play_again(self):
        game = self.manager.get_screen('game')
        game.reset()
        self.manager.current = 'game'


class WordChainApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(ResultScreen(name='result'))
        return sm


if __name__ == '__main__':
    WordChainApp().run()
