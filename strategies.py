import math
import numpy as np


def p_k(k, l, p):
    return (1-l)**(k-1)*(1-p)**(k-1) - (1-l)**k*(1-p)**k


def find_threshold(l, p, e):
    last_cost = math.inf
    new_cost = math.inf
    n = 0
    a1 = -1/l + -1/p + 1/l**2 + 1/(l*p) + 1/p**2
    while new_cost <= last_cost:
        last_cost = new_cost

        a = (n-2)/l + (n-2)/p + (n-2)*(n-1)/2 + 1/l**2 + 1/(l*p) + 1/p**2

        s1 = 0
        for k in range(1, n+1):
            s1 += p_k(k, l, p) * (a - k * (k-1) / 2)

        s2 = 0
        for k in range(n+1, 100):
            s2 += p_k(k, l, p)*(k + a1)

        s3 = 0
        for k in range(1, n):
            s3 += p_k(k, l, p) * (n - k)

        new_cost = (s1 + s2 + e/p) / ((1-p)/p + 1 + (1-l)/l + s3)

        n += 1

    return n-2


def update_q_values(qvalues, old_aoi_sender, old_aoi_receiver,
                    new_aoi_sender, new_aoi_receiver, action, cost, epsilon, time_step):

    old_aoi_sender = min(old_aoi_sender, 99)
    old_aoi_receiver = min(old_aoi_receiver, 99)
    new_aoi_sender = min(new_aoi_sender, 99)
    new_aoi_receiver = min(new_aoi_receiver, 99)

    delta = 0.999
    learning_rate = (1/(time_step+1)) ** 0.2  # 0.1
    gamma = 0.7

    epsilon = delta * epsilon

    V = np.min(qvalues[new_aoi_sender][new_aoi_receiver])
    old_q_value = qvalues[old_aoi_sender][old_aoi_receiver][action]

    qvalues[old_aoi_sender][old_aoi_receiver][action] = \
        (1 - learning_rate) * old_q_value + learning_rate * (cost + gamma * V)

    return qvalues, epsilon
