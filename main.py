import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Parametry poczatkowe
Q0_charge = 0.01  # poczatkowy stan ladowania (%)
time_span_charge = [0, 5]  # czas symulacji (h)
smartphones = {
    "iPhone 14 - 3A (5V)": {
        "Q_max": 3.279,  # max pojemnosc baterii (Ah)
        "V_nom": 3.85,  # napiecie nominalne
        "I_charge": 3.0,  # max prad ladowania w A
        "R_int": 0.1,  # rez wewnetrzna
        "eta_ladowanie": 0.9  # sprawnosc ladowania
    },
    "iPhone 14 - 2.22A (9V)": {
        "Q_max": 3.279,
        "V_nom": 3.85,
        "I_charge": 2.22,
        "R_int": 0.1,
        "eta_ladowanie": 0.9
    },
    "Samsung Galaxy S23 - 3A (5V)": {
        "Q_max": 3.9,
        "V_nom": 3.85,
        "I_charge": 3.0,
        "R_int": 0.1,
        "eta_ladowanie": 0.9
    },
    "Samsung Galaxy S23 - 2.77A (9V)": {
        "Q_max": 3.9,
        "V_nom": 3.85,
        "I_charge": 2.77,
        "R_int": 0.1,
        "eta_ladowanie": 0.9
    }
}

def battery_dynamics_nonlinear(t, Q, I, Q_max, eta_ladowanie):
    I_effective = eta_ladowanie * I * (1 - Q / Q_max)
    dQdt = I_effective
    return dQdt

def to_percentage(Q, Q_max):
    return (Q / Q_max) * 100

charge_results = {}
for name, params in smartphones.items():
    sol_ladowanie = solve_ivp(
        battery_dynamics_nonlinear,
        time_span_charge,
        [Q0_charge * params["Q_max"]],
        args=(params["I_charge"], params["Q_max"], params["eta_ladowanie"]),
        t_eval=np.linspace(time_span_charge[0], time_span_charge[1], 100)
    )
    charge_results[name] = sol_ladowanie

plt.figure(figsize=(10, 6))
plt.subplot(1,2,1)
for name, sol in charge_results.items():
    plt.plot(sol.t, to_percentage(sol.y[0], smartphones[name]["Q_max"]), label=name)
plt.xlabel('Czas (h)')
plt.ylabel('Procent Baterii (%)')
plt.title('Porównanie prędkości ładowania')
plt.ylim(0.0, 100.0)
plt.xlim(0.0)
plt.grid(True)
plt.legend()

plt.subplot(1,2,2)
for name, sol in charge_results.items():
    time = sol.t
    charge_capacity = sol.y[0]
    I_charge_values = smartphones[name]["eta_ladowanie"] * smartphones[name]["I_charge"] * (1 - charge_capacity / smartphones[name]["Q_max"])
    plt.plot(time, I_charge_values, label=name)
plt.xlabel('Czas (h)')
plt.ylabel('Prąd ładowania (A)')
plt.title('Zmiany prądu ładowania w czasie')
plt.ylim(0.0, 3.0)
plt.xlim(0.0, 5.0)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
