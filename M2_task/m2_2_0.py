import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ----------------------------------------------------
# ПАРАМЕТРЫ, КОТОРЫЕ МОЖНО МЕНЯТЬ ДЛЯ РАЗНЫХ СЦЕНАРИЕВ
# ----------------------------------------------------
N = 200       # Число пространственных узлов (V имеет размер N+1, I имеет размер N)
L0 = 1.0      # Базовая индуктивность (Гн)
C0 = 0.01     # Базовая ёмкость (Ф)
r = 0.0       # Распределённое сопротивление в линии (Ом) - будет меняться для п.3
alpha = 0.0   # Коэффициент частотной зависимости L и C - будет >0 для п.4

# Частота источника
w = 0.2

# СЦЕНАРИЙ: выберите от 1 до 4
# 1 - короткое замыкание на конце => стоячая волна
# 2 - согласованная нагрузка => нет отражения
# 3 - затухание в линии (распределённое сопротивление)
# 4 - дисперсия: частотнозависимые L(w), C(w)
scenario = 1

if scenario == 1:
    # (1) Стоячая волна: короткое замыкание на конце
    # R_end = 0, r=0, alpha=0
    R_end = 0.0
    r = 0.0
    alpha = 0.0

elif scenario == 2:
    # (2) Согласованная нагрузка: R_end = Z = sqrt(L/C), без затухания, без дисперсии
    alpha = 0.0
    # Сначала берём L и C без дисперсии
    L_eff = L0
    C_eff = C0
    Z = np.sqrt(L_eff / C_eff)
    R_end = Z
    r = 0.0

elif scenario == 3:
    # (3) Затухание в линии: добавляем сопротивление r > 0
    #   Сможем выбрать любой тип нагрузки, пусть будет короткое замыкание или что-то ещё.
    #   Для демонстрации возьмём короткое замыкание.
    R_end = 0.0
    alpha = 0.0
    r = 0.05  # Некоторое маленькое сопротивление

elif scenario == 4:
    # (4) Дисперсия: пусть L(ω) = L0*(1 + alpha * ω^2), C(ω) = C0*(1 + alpha * ω^2)
    r = 0.0
    alpha = 0.5  # Коэффициент для усиления частотной зависимости
    # Короткое замыкание на конце (можно менять), чтобы заметнее были изменения
    R_end = 0.0

# ---------------------------------------
# РАСЧЁТ ЭФФЕКТИВНЫХ L и C ПРИ ДИСПЕРСИИ
# ---------------------------------------
# Для упрощения считаем, что у нас одна частота w. Тогда L_eff и C_eff зависят от w.
L_eff = L0 * (1.0 + alpha * w**2)
C_eff = C0 * (1.0 + alpha * w**2)

# Волновое сопротивление с учётом дисперсии (нужно, если хотим согласовать нагрузку)
Z_eff = np.sqrt(L_eff / C_eff)

# Если выбрана сценария 2 (согласованная нагрузка), надо, чтобы R_end = Z_eff
# Но на случай, если alpha != 0 в будущем, можно обновить R_end = Z_eff.
if scenario == 2:
    R_end = Z_eff

# ------------------------------------------
# ВЫБОР ШАГА ВРЕМЕНИ (условие устойчивости)
# ------------------------------------------
# Обычно dt <= k * sqrt( L_eff*C_eff ), где k < 1 (например 0.9).
dt = 0.9 * np.sqrt(L_eff * C_eff)

# ------------------------------------------
# ИНИЦИАЛИЗАЦИЯ МАССИВОВ
# ------------------------------------------
# Напряжения (N+1 узел), токи (N ветвей)
V = np.zeros(N + 1)
I = np.zeros(N)

# ------------------------------------------
# НАСТРОЙКИ ГРАФИКИ
# ------------------------------------------
fig, ax = plt.subplots()
line, = ax.plot(V, label='V')
ax.set_ylim(-1, 1)
ax.set_xlim(0, N)
ax.set_xlabel('Узел')
ax.set_ylabel('Напряжение')
ax.set_title(f"Scenario = {scenario} (см. код)")

# ------------------------------------------
# ФУНКЦИЯ ОБНОВЛЕНИЯ (для анимации)
# ------------------------------------------
def animate(frame):
    global V, I
    # Можно выполнять несколько малых шагов на один кадр, чтобы анимация была плавнее
    sub_steps = 5

    for _ in range(sub_steps):
        # Задаём напряжение источника на левом краю (узел 0).
        # Гармоническое возбуждение.
        V[0] = 0.5 * np.sin(w * frame * dt * sub_steps)

        # Сохраняем старое напряжение (чтобы не перезаписывать раньше времени).
        V_new = V.copy()

        # -------------------------
        # Обновляем напряжения V
        # -------------------------
        # Формула дискретизации:
        # dV_n/dt = (1/C_eff) * (I_{n-1} - I_n)  -> V_n(t+dt) = V_n(t) + ...
        for n in range(1, N):
            V_new[n] = V[n] + dt / C_eff * (I[n-1] - I[n])

        # Граничные условия слева (n=0):
        # V[0] уже задан, но если нужно учесть ток I[0], то можно добавить поправку
        # (если считать, что к узлу 0 тоже подключён конденсатор). Однако
        # в большинстве классических реализаций источник "задаёт" V[0] жёстко.

        # Граничные условия справа (n=N): V_new[N] = R_end * I[N-1]
        V_new[N] = R_end * I[N - 1]

        # -------------------------
        # Обновляем токи I
        # -------------------------
        # dI_n/dt = (1/L_eff)*[ V_n - V_{n+1} - r*I_n ] (если есть сопротивление r)
        for n in range(N):
            dI = dt / L_eff * ((V_new[n] - V_new[n+1]) - r*I[n])
            I[n] += dI

        # Запоминаем новое напряжение
        V = V_new

    # Обновляем линию на графике
    line.set_ydata(V)
    return line,

# ------------------------------------------
# ЗАПУСК АНИМАЦИИ
# ------------------------------------------
ani = FuncAnimation(fig, animate, frames=2000, interval=30, blit=True)
plt.legend()
plt.show()
