from kivy.uix.button import Button
from kivy.app import App
from functools import partial


class KivyButton(App):
    def disable(self, instance, *args):
        instance.disabled = True

    def change_color1(self, instance:Button, *args):
        instance.background_color = (255,0,0)

    def change_color2(self, instance:Button, *args):
        instance.background_color = (0,255,0)
        print('!!!!')

    def update(self, instance, *args):
        instance.text = "I am Disabled!"

    def build(self):
        mybtn = Button(text="Click me to disable", pos=(300,350), size_hint = (.25, .18))
        mybtn.bind(on_press=partial(self.change_color2, mybtn))
        mybtn.bind(on_press=partial(self.change_color1, mybtn))
        mybtn.bind(on_press=partial(self.update, mybtn))
        mybtn.bind(on_press=partial(self.disable, mybtn))

        return mybtn


KivyButton().run()
