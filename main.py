import bisect
import random
import numpy as np

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.config import Config

from kivy_garden.graph import LinePlot

import strategies

# Window.maximize()
Window.fullscreen = 'auto'

Config.set('graphics', 'maxfps', '0')
Config.write()


class MyGridLayout(Widget):

    def __init__(self, **kwargs):

        self.strategy_type = "random"
        self.next_strategy_type = "random"

        self.qinit = 0

        if Window.size[0] < 2000:
            self.smaller_font_size = 20  # 12
            self.larger_font_size = 30  # 20
        else:
            self.smaller_font_size = 24
            self.larger_font_size = 36

        super().__init__()

        self.seconds_per_time_step = 0.1

        self.ids.slider_p.value = 0.9
        self.p = 0.9
        self.ids.slider_lamb.value = 0.5
        self.lamb = 0.5
        self.ids.slider_zeta.value = 5
        self.zeta = 5
        self.ids.slider_e.value = 3
        self.energy_cost = 3

        self.threshold = 2
        self.qvalues = self.qinit*np.ones((100, 100, 2))
        self.epsilon = 0.9

        self.time_step = 0
        self.aoi_sender = 0
        self.aoi_receiver = 1
        self.costs = []
        self.transmission_costs = []
        self.risky_states = []
        self.aoi_costs = []
        self.max_aoi = 10

        self.cost_plot = LinePlot(line_width=2, color=[1, 0, 0, 1])
        self.cost_plot.points = []
        self.energy_plot = LinePlot(line_width=2, color=[0, 1, 0, 1])
        self.energy_plot.points = []
        self.aoi_plot = LinePlot(line_width=2, color=[0, 0, 1, 1])
        self.aoi_plot.points = []
        self.risk_plot = LinePlot(line_width=2, color=[1, 0, 1, 1])
        self.risk_plot.points = []
        self.graph = self.ids.graph

        # needs to be a sorted array and has to contain 0 as the first entry
        self.transition_time_steps = [0]
        for t in self.transition_time_steps:
            plot = LinePlot(line_width=2, color=[0, 0, 0, 0.5])
            plot.points = [(t, self.graph.ymin), (t, 100)]
            self.graph.add_plot(plot)

        legend_cost_plot = LinePlot(line_width=2, color=[1, 0, 0, 1])
        legend_cost_plot.points = [(0, 1), (1, 1)]
        self.ids.legend_costs.add_plot(legend_cost_plot)

        legend_energy_plot = LinePlot(line_width=2, color=[0, 1, 0, 1])
        legend_energy_plot.points = [(0, 1), (1, 1)]
        self.ids.legend_energy.add_plot(legend_energy_plot)

        legend_aoi_plot = LinePlot(line_width=2, color=[0, 0, 1, 1])
        legend_aoi_plot.points = [(0, 1), (1, 1)]
        self.ids.legend_aoi.add_plot(legend_aoi_plot)

        legend_risk_plot = LinePlot(line_width=2, color=[1, 0, 1, 1])
        legend_risk_plot.points = [(0, 1), (1, 1)]
        self.ids.legend_risk.add_plot(legend_risk_plot)

        self.risk_threshold_plot = LinePlot(line_width=2, color=[0.5, 0, 0, 0.8])
        self.risk_threshold_plot.points = [(-1e10, self.zeta), (0, self.zeta)]
        self.graph.add_plot(self.risk_threshold_plot)

        self.update_event = None

        self.x_range = 10000
        self.mean_range = 1000

    def animate_it(self, widget):

        self.adjust(widget)

        animation = Animation(background_color=(1, 1, 1, 0), duration=0.2)
        animation.start(widget)

        self.graph.add_plot(self.cost_plot)
        self.graph.add_plot(self.energy_plot)
        self.graph.add_plot(self.aoi_plot)
        self.graph.add_plot(self.risk_plot)

        self.update_event = Clock.schedule_interval(self.update, self.seconds_per_time_step)

    def adjust(self, widget):
        self.transition_time_steps += [self.time_step]

        plot = LinePlot(line_width=2, color=[0, 0, 0, 0.5])
        plot.points = [(self.time_step, self.graph.ymin), (self.time_step, 100)]
        self.graph.add_plot(plot)

        self.seconds_per_time_step = 10 ** (-2-self.ids.slider_speed.value)
        if self.update_event is not None:
            self.update_event.cancel()
            self.update_event = Clock.schedule_interval(self.update, self.seconds_per_time_step)

        self.p = self.ids.slider_p.value
        self.lamb = self.ids.slider_lamb.value
        self.zeta = self.ids.slider_zeta.value
        self.energy_cost = self.ids.slider_e.value
        self.strategy_type = self.next_strategy_type

        self.risk_threshold_plot.points = [(-1e10, self.zeta), (1e10, self.zeta)]

        if self.strategy_type == "TB":
            self.threshold = strategies.find_threshold(self.lamb, self.p, self.energy_cost)
        if self.strategy_type in ("TQL", "Q+RS"):
            self.qvalues = self.qinit*np.ones((100, 100, 2))

    def adjust_graph(self, widget):
        self.x_range = self.ids.slider_range.value
        if self.x_range > 20000:
            self.ids.graph.x_ticks_major = 10000
        elif self.x_range > 10000:
            self.ids.graph.x_ticks_major = 2000
        else:
            self.ids.graph.x_ticks_major = 1000

        self.graph.ymax = self.ids.slider_yrange.value
        if self.graph.ymax >= 10:
            self.graph.y_ticks_major = int(self.graph.ymax/10)
        else:
            self.graph.y_ticks_major = 1

        if self.ids.avg_box.active:
            self.mean_range = self.ids.slider_meanrange.value
        else:
            self.mean_range = 1

    def random_box(self, widget):
        self.next_strategy_type = "random"
        self.ids.strat_label.text = "random transmission"

    def TQL_box(self, widget):
        self.next_strategy_type = "TQL"
        self.ids.strat_label.text = "risk neutral Q-learning"

    def QRS_box(self, widget):
        self.next_strategy_type = "Q+RS"
        self.ids.strat_label.text = "risk-sensitive Q-learning"

    def TB_box(self, widget):
        self.next_strategy_type = "TB"
        self.ids.strat_label.text = "threshold-based transmission"

    def periodic_box(self, widget):
        self.next_strategy_type = "periodic"
        self.ids.strat_label.text = "periodic transmission"

    def cost_box(self, widget):
        if widget.active:
            self.graph.add_plot(self.cost_plot)
        else:
            self.graph.remove_plot(self.cost_plot)
            self.graph._clear_buffer()

    def energy_box(self, widget):
        if widget.active:
            self.graph.add_plot(self.energy_plot)
        else:
            self.graph.remove_plot(self.energy_plot)
            self.graph._clear_buffer()

    def aoi_box(self, widget):
        if widget.active:
            self.graph.add_plot(self.aoi_plot)
        else:
            self.graph.remove_plot(self.aoi_plot)
            self.graph._clear_buffer()

    def risk_box(self, widget):
        if widget.active:
            self.graph.add_plot(self.risk_plot)
        else:
            self.graph.remove_plot(self.risk_plot)
            self.graph._clear_buffer()

    def avg_box(self, widget):
        pass
        # if widget.active:
        #     self.mean_range = self.ids.slider_meanrange.value
        # else:
        #     self.mean_range = 1

    def update(self, *args):

        old_aoi_sender = self.aoi_sender
        old_aoi_receiver = self.aoi_receiver

        a = self.strategy()
        cost = 0

        transmission_cost = 0
        if a:
            transmission_cost = self.energy_cost
            if random.random() < self.p:
                self.aoi_receiver = self.aoi_sender
                if self.seconds_per_time_step > 0.1:
                    self.send_packet()
                elif self.seconds_per_time_step > 0.01:
                    self.age_sender_paket()
                else:
                    self.ids.green_sender_paket.color = [1, 1, 1, 1 - self.aoi_sender/self.max_aoi]
                    self.ids.red_sender_paket.color = [1, 1, 1, self.aoi_sender/self.max_aoi]
            else:
                if self.seconds_per_time_step > 0.01:
                    if self.seconds_per_time_step > 0.1:
                        self.drop_packet()
                    self.age_receiver_paket()
                else:
                    self.ids.green_receiver_paket.color = [1, 1, 1, 1 - self.aoi_receiver/self.max_aoi]
                    self.ids.red_receiver_paket.color = [1, 1, 1, self.aoi_receiver/self.max_aoi]
        else:
            if self.seconds_per_time_step > 0.01:
                self.age_receiver_paket()
            else:
                self.ids.green_receiver_paket.color = [1, 1, 1, 1 - self.aoi_receiver/self.max_aoi]
                self.ids.red_receiver_paket.color = [1, 1, 1, self.aoi_receiver/self.max_aoi]

        self.aoi_receiver += 1

        cost += self.aoi_receiver + transmission_cost
        self.transmission_costs += [transmission_cost]
        self.aoi_costs += [self.aoi_receiver]
        self.costs += [cost]
        self.risky_states += [int(self.aoi_receiver >= self.zeta)]

        self.aoi_sender += 1
        if random.random() < self.lamb:
            self.aoi_sender = 0
            if self.seconds_per_time_step > 0.1:
                self.new_paket()
            elif self.seconds_per_time_step > 0.01:
                self.age_sender_paket()
            else:
                self.ids.green_sender_paket.color = [1, 1, 1, 1 - self.aoi_sender/self.max_aoi]
                self.ids.red_sender_paket.color = [1, 1, 1, self.aoi_sender/self.max_aoi]
        else:
            if self.seconds_per_time_step > 0.01:
                self.age_sender_paket()
            else:
                self.ids.green_sender_paket.color = [1, 1, 1, 1 - self.aoi_sender/self.max_aoi]
                self.ids.red_sender_paket.color = [1, 1, 1, self.aoi_sender/self.max_aoi]

        if self.strategy_type in ("TQL", "Q+RS"):
            if self.strategy_type == "Q+RS" and self.aoi_receiver >= self.zeta:
                cost = 2 * cost
            self.qvalues, self.epsilon = strategies.update_q_values(self.qvalues, old_aoi_sender, old_aoi_receiver,
                                                                    self.aoi_sender, self.aoi_receiver, a, cost,
                                                                    self.epsilon, self.time_step)

        if self.time_step > 0 and (self.time_step % 10 == 1 or self.seconds_per_time_step > 0.1):
            self.update_graph()

        self.time_step += 1

    def strategy(self):

        if self.strategy_type == "random":
            return random.random() < self.lamb
        elif self.strategy_type in ("TQL", "Q+RS"):
            # random action because of epsilon greedy
            if random.random() < self.epsilon:
                return random.randint(0, 1)
            # random action if Q-values are identical
            elif self.qvalues[self.aoi_sender][self.aoi_receiver][0] == \
                    self.qvalues[self.aoi_sender][self.aoi_receiver][1]:
                return random.randint(0, 1)
            # choose smallest Q-value
            else:
                return np.argmin(self.qvalues[self.aoi_sender][self.aoi_receiver])
        elif self.strategy_type == "TB":
            return self.aoi_receiver - self.aoi_sender >= self.threshold
        elif self.strategy_type == "periodic":
            return self.time_step % (int(1/self.lamb)) == 0

    def update_graph(self):
        trans = self.transition_time_steps[bisect.bisect(self.transition_time_steps, self.time_step) - 1]
        mean_min = lambda x: max(0, x-self.mean_range, trans * int(x > trans))
        self.graph.xmin = self.time_step - self.x_range
        self.graph.xmax = self.time_step

        self.cost_plot.points = self.cost_plot.points + \
                                [(self.time_step,
                                  np.mean(self.costs[mean_min(self.time_step):self.time_step]))]
        self.cost_plot.points = self.cost_plot.points[-3000:]
        self.energy_plot.points = self.energy_plot.points + \
                                  [(self.time_step,
                                    np.mean(self.transmission_costs[mean_min(self.time_step):self.time_step]))]
        self.energy_plot.points = self.energy_plot.points[-3000:]
        self.aoi_plot.points = self.aoi_plot.points + \
                                  [(self.time_step,
                                    np.mean(self.aoi_costs[mean_min(self.time_step):self.time_step]))]
        self.aoi_plot.points = self.aoi_plot.points[-3000:]
        self.risk_plot.points = self.risk_plot.points + \
                               [(self.time_step,
                                 np.mean(self.risky_states[mean_min(self.time_step):self.time_step]))]
        self.risk_plot.points = self.risk_plot.points[-3000:]

    def age_sender_paket(self):

        green_animation_sender = Animation(color=(1, 1, 1, 1 - self.aoi_sender/self.max_aoi),
                                           duration=self.seconds_per_time_step / 4)

        red_animation_sender = Animation(color=(1, 1, 1, self.aoi_sender/self.max_aoi),
                                         duration=self.seconds_per_time_step / 4)

        green_animation_sender.start(self.ids.green_sender_paket)
        red_animation_sender.start(self.ids.red_sender_paket)

    def age_receiver_paket(self):

        green_animation_receiver = Animation(color=(1, 1, 1, 1 - self.aoi_receiver/self.max_aoi),
                                             duration=self.seconds_per_time_step / 4)

        red_animation_receiver = Animation(color=(1, 1, 1, self.aoi_receiver/self.max_aoi),
                                           duration=self.seconds_per_time_step / 4)

        green_animation_receiver.start(self.ids.green_receiver_paket)
        red_animation_receiver.start(self.ids.red_receiver_paket)

    def new_paket(self, *args):
        green_animation = Animation(color=(1, 1, 1, 1),
                                    pos_hint={"x": - 0.667 * self.ids.relative.size[0] / Window.size[0],
                                              "y": self.y},
                                    duration=self.seconds_per_time_step/1000) + \
                          Animation(color=(1, 1, 1, 1),
                                    pos_hint={"x": - 0.224 * self.ids.relative.size[0] / Window.size[0],
                                              "y": self.y},
                                    duration=self.seconds_per_time_step/4)
        red_animation = Animation(color=(1, 1, 1, 0),
                                  pos_hint={"x": - 0.667 * self.ids.relative.size[0] / Window.size[0],
                                            "y": self.y},
                                  duration=self.seconds_per_time_step/1000) + \
                        Animation(color=(1, 1, 1, 0),
                                  pos_hint={"x": - 0.224 * self.ids.relative.size[0] / Window.size[0],
                                            "y": self.y},
                                  duration=self.seconds_per_time_step/4)

        green_animation.start(self.ids.green_sender_paket)
        red_animation.start(self.ids.red_sender_paket)

    def send_packet(self, *args):

        green_animation_sender = Animation(duration=self.seconds_per_time_step / 2) + \
                               Animation(color=(1, 1, 1, 0), duration=3*self.seconds_per_time_step/40) + \
                               Animation(duration=self.seconds_per_time_step / 4) + \
                               Animation(color=(1, 1, 1, 1 - self.aoi_sender/self.max_aoi),
                                         duration=self.seconds_per_time_step / 40)

        red_animation_sender = Animation(duration=self.seconds_per_time_step / 2) + \
                               Animation(color=(1, 1, 1, 0), duration=3*self.seconds_per_time_step/40) + \
                               Animation(duration=self.seconds_per_time_step / 4) + \
                               Animation(color=(1, 1, 1, self.aoi_sender/self.max_aoi),
                                         duration=self.seconds_per_time_step / 40)

        green_animation_receiver = Animation(duration=self.seconds_per_time_step/2) + \
                                   Animation(color=(1, 1, 1, 0), duration=self.seconds_per_time_step/40) + \
                                   Animation(pos_hint={"x": - 0.224 * self.ids.relative.size[0] / Window.size[0],
                                                       "y": self.y},
                                             duration=self.seconds_per_time_step/40) + \
                                   Animation(color=(1, 1, 1, 1 - self.aoi_sender/self.max_aoi),
                                             duration=self.seconds_per_time_step/40) + \
                                   Animation(color=(1, 1, 1, 1 - self.aoi_receiver/self.max_aoi),
                                             pos_hint={"x": self.ids.green_sender_paket.pos_hint["x"]
                                                            + self.ids.relative.size[0] / (1.13 * Window.size[0]),
                                                       "y": self.y},
                                             duration=self.seconds_per_time_step/4)
        red_animation_receiver = Animation(duration=self.seconds_per_time_step/2) + \
                                 Animation(color=(1, 1, 1, 0), duration=self.seconds_per_time_step/40) + \
                                 Animation(pos_hint={"x": - 0.224 * self.ids.relative.size[0] / Window.size[0],
                                                       "y": self.y},
                                           duration=self.seconds_per_time_step/40) + \
                                 Animation(color=(1, 1, 1, self.aoi_sender/self.max_aoi),
                                           duration=self.seconds_per_time_step/40) + \
                                 Animation(color=(1, 1, 1, self.aoi_receiver/self.max_aoi),
                                           pos_hint={"x": self.ids.red_sender_paket.pos_hint["x"]
                                                       + self.ids.relative.size[0] / (1.13 * Window.size[0]),
                                                       "y": self.y},
                                           duration=self.seconds_per_time_step/4)

        green_animation_sender.start(self.ids.green_sender_paket)
        red_animation_sender.start(self.ids.red_sender_paket)

        green_animation_receiver.start(self.ids.green_receiver_paket)
        red_animation_receiver.start(self.ids.red_receiver_paket)

    def drop_packet(self):

        green_animation_sender = Animation(duration=self.seconds_per_time_step / 2) + \
                               Animation(color=(1, 1, 1, 0), duration=3*self.seconds_per_time_step/40) + \
                               Animation(duration=self.seconds_per_time_step / 4) + \
                               Animation(color=(1, 1, 1, 1 - self.aoi_sender/self.max_aoi),
                                         duration=self.seconds_per_time_step / 40)

        red_animation_sender = Animation(duration=self.seconds_per_time_step / 2) + \
                               Animation(color=(1, 1, 1, 0), duration=3*self.seconds_per_time_step/40) + \
                               Animation(duration=self.seconds_per_time_step / 4) + \
                               Animation(color=(1, 1, 1, self.aoi_sender/self.max_aoi),
                                         duration=self.seconds_per_time_step / 40)

        green_animation_receiver = Animation(duration=self.seconds_per_time_step/2) + \
                                   Animation(color=(1, 1, 1, 0), duration=self.seconds_per_time_step/40) + \
                                   Animation(pos_hint={"x": - 0.224 * self.ids.relative.size[0] / Window.size[0],
                                                       "y": self.y},
                                             duration=self.seconds_per_time_step/40) + \
                                   Animation(color=(1, 1, 1, 1 - self.aoi_sender / 10),
                                             duration=self.seconds_per_time_step/40) + \
                                   Animation(color=(1, 1, 1, 0),
                                             pos_hint={"x": self.ids.green_sender_paket.pos_hint["x"]
                                                            + self.ids.relative.size[0] / (1.13 * Window.size[0]),
                                                       "y": self.y},
                                             duration=self.seconds_per_time_step/4) + \
                                   Animation(color=(1, 1, 1, 1 - self.aoi_receiver / 10),
                                             duration=self.seconds_per_time_step/40)
        red_animation_receiver = Animation(duration=self.seconds_per_time_step/2) + \
                                 Animation(color=(1, 1, 1, 0), duration=self.seconds_per_time_step/40) + \
                                 Animation(pos_hint={"x": - 0.224 * self.ids.relative.size[0] / Window.size[0],
                                                       "y": self.y},
                                           duration=self.seconds_per_time_step/40) + \
                                 Animation(color=(1, 1, 1, self.aoi_sender/self.max_aoi),
                                           duration=self.seconds_per_time_step/40) + \
                                 Animation(color=(1, 1, 1, 0),
                                           pos_hint={"x": self.ids.red_sender_paket.pos_hint["x"]
                                                       + self.ids.relative.size[0] / (1.13 * Window.size[0]),
                                                       "y": self.y},
                                           duration=self.seconds_per_time_step/4) + \
                                 Animation(color=(1, 1, 1, self.aoi_receiver / 10),
                                           duration=self.seconds_per_time_step/40)

        green_animation_sender.start(self.ids.green_sender_paket)
        red_animation_sender.start(self.ids.red_sender_paket)

        green_animation_receiver.start(self.ids.green_receiver_paket)
        red_animation_receiver.start(self.ids.red_receiver_paket)


class MyApp(App):

    def build(self):

        grid = MyGridLayout()

        return grid


if __name__ == '__main__':
    MyApp().run()
