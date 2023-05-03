import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle


class MyBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MyBoxLayout, self).__init__(**kwargs)
        # Erstes Bild hinzufügen
        self.add_widget(Image(source='sender.png'))
        # Zweites Bild hinzufügen
        self.add_widget(Image(source='receiver.png'))

        # Hintergrundfarbe auf Weiß setzen
        with self.canvas.before:
            Color(1, 1, 1, 1)  # weiß
            self.rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class MyKivyApp(App):
    def build(self):
        # Erstellen Sie das Layout
        layout = MyBoxLayout(orientation='horizontal')
        return layout


if __name__ == '__main__':
    MyKivyApp().run()
