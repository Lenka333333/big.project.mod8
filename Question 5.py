import math
import random

stations = [
    ("sec", 1, 1.01 * 2.6931, 1 / 1.01, 8.3),
    ("ane", 3, 1.03 * 18.7736, 1 / 1.03, 8.3),
    ("CPM", 2, 1.02 * 24.7861, 1 / 1.02, 8.3 * 0.3325),
    ("ac", 1, 10.27, 5.617 / 10.27 ** 2, 8.3 * 0.22),
    ("CT", 2, 14.5, (((19 - 10) ** 2 / 12) / 14.5 ** 2), 6.5),
]
total_lq = 0
for name, c, es, cs2, lam in stations:
    mu = 60 / es
    a = lam / mu
    rho = a / c
    numer = (a ** c / math.factorial(c)) * (1 / (1 - rho))
    denom = sum(a ** k / math.factorial(k) for k in range(c)) + numer
    cc = numer / denom
    lqm = cc * rho / (1 - rho)
    lqg = lqm * (1 + cs2) / 2
    rho = lam / (c * mu)
    total_lq += lqg
    print(f"{name} ,c{c}, ρ{rho:.3f}, C2{cs2:.3f}, Lq{lqg:.3f}")


prev_ovfl = 100
for N in range(1, 21):
    total = term = math.exp(-total_lq)
    for j in range(1, N + 1):
        term *= total_lq / j
        total += term
    p_ok= total
    p_ovfl = (1 - p_ok) * 100
    diff = prev_ovfl - p_ovfl

    print(f"{N}, {p_ovfl:.3f}%, {p_ok * 100:.3f}%")
    prev_ovfl = p_ovfl
