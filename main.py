import numpy as np
from scipy.integrate import solve_ivp
import tkinter as tk
from tkinter import ttk
import plotly.graph_objects as go
import plotly.offline as pyo
from plotly.subplots import make_subplots

# Parametry poczatkowe
V_nom = 3.85  # nominalne napięcie baterii (V)
R_int = 0.1  # rez wewnętrzna (ohm)
eta_ladowanie = 0.9  # sprawnosc ladowania
time_span_charge = [0, 5]  # czas symulacji (h)

# Słownik popularnych smartfonów z nowymi modelami
smartphones = {
    "iPhone 14 - 3A (5V)": {
        "Q_max": 3.279, # max pojemnosc baterii (Ah)
        "I_charge": 3.0 # max prad ladowania w A
    },
    "iPhone 14 - 2.22A (9V)": {
        "Q_max": 3.279,
        "I_charge": 2.22
    },
    "Samsung Galaxy S23 - 3A (5V)": {
        "Q_max": 3.9,
        "I_charge": 3.0
    },
    "Samsung Galaxy S23 - 2.77A (9V)": {
        "Q_max": 3.9,
        "I_charge": 2.77
    },
    "Google Pixel 7 - 2.5A (5V)": {
        "Q_max": 4.0,
        "I_charge": 2.5
    },
    "Google Pixel 7 - 2.0A (9V)": {
        "Q_max": 4.0,
        "I_charge": 2.0
    },
    "OnePlus 11 - 3.0A (5V)": {
        "Q_max": 4.5,
        "I_charge": 3.0
    },
    "OnePlus 11 - 2.5A (9V)": {
        "Q_max": 4.5,
        "I_charge": 2.5
    }
}

def battery_dynamics_nonlinear(t, Q, I, Q_max, eta_ladowanie):
    I_effective = eta_ladowanie * I * (1 - Q / Q_max)
    dQdt = I_effective
    return dQdt

def to_percentage(Q, Q_max):
    return (Q / Q_max) * 100

def plot_charging_process():
    smartphone_name = smartphone_var.get()
    Q0_charge = q0_charge_var.get()
    Q_max = smartphones[smartphone_name]["Q_max"]
    I_charge = smartphones[smartphone_name]["I_charge"]
    Q0 = Q0_charge / 100 * Q_max
    sol_ladowanie = solve_ivp(
        battery_dynamics_nonlinear,
        time_span_charge,
        [Q0],
        args=(I_charge, Q_max, eta_ladowanie),
        t_eval=np.linspace(time_span_charge[0], time_span_charge[1], 100)
    )
    fig = make_subplots(rows=1, cols=2, subplot_titles=('Szybkość ładowania', 'Zmiany prądu ładowania'))
    fig.add_trace(go.Scatter(x=sol_ladowanie.t,
                             y=to_percentage(sol_ladowanie.y[0], Q_max),
                             mode='lines', name='Stan naładowania'),
                  row=1, col=1)
    charge_capacity = sol_ladowanie.y[0]
    I_charge_values = eta_ladowanie * I_charge * (1 - charge_capacity / Q_max)
    fig.add_trace(go.Scatter(x=sol_ladowanie.t,
                             y=I_charge_values,
                             mode='lines', name='Prąd ładowania'),
                  row=1, col=2)
    fig.update_layout(title='Symulacja procesu ładowania baterii',
                      xaxis_title='Czas (h)',
                      yaxis_title='Procent Baterii (%)',
                      yaxis2_title='Prąd ładowania (A)',
                      showlegend=True)
    pyo.iplot(fig)

def increase_q0_charge():
    if q0_charge_var.get() < 100:
        q0_charge_var.set(q0_charge_var.get() + 1)
def decrease_q0_charge():
    if q0_charge_var.get() > 0:
        q0_charge_var.set(q0_charge_var.get() - 1)
def increase_q0_charge_10():
    if q0_charge_var.get() <= 90:
        q0_charge_var.set(q0_charge_var.get() + 10)
def decrease_q0_charge_10():
    if q0_charge_var.get() >= 10:
        q0_charge_var.set(q0_charge_var.get() - 10)

#obsluga tkinter
root = tk.Tk()
root.title("Symulacja procesu ładowania baterii")
root.geometry("350x100")
root.minsize(350, 100)

smartphone_label = tk.Label(root, text="Wybierz smartfon:",font=("TkDefaultFont", 8, "bold"))
smartphone_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')
smartphone_var = tk.StringVar(value=list(smartphones.keys())[0])
smartphone_dropdown = ttk.Combobox(root, textvariable=smartphone_var, values=list(smartphones.keys()))
smartphone_dropdown.grid(row=0, column=1, columnspan=5, padx=5, pady=5, sticky='ew')

q0_charge_label = tk.Label(root, text="Aktualny % baterii:", font=("TkDefaultFont", 8, "bold"))
q0_charge_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')
q0_charge_var = tk.IntVar(value=10)
q0_charge_display = tk.Label(root, textvariable=q0_charge_var, fg="green", font=("TkDefaultFont", 8, "bold"))
q0_charge_display.grid(row=1, column=1, padx=10, pady=5, sticky='w')

decrease_button_10 = tk.Button(root, text="-10", command=decrease_q0_charge_10)
decrease_button_10.grid(row=1, column=2, padx=5)
decrease_button = tk.Button(root, text="-", command=decrease_q0_charge)
decrease_button.grid(row=1, column=3, padx=5)
increase_button = tk.Button(root, text="+", command=increase_q0_charge)
increase_button.grid(row=1, column=4, padx=5)
increase_button_10 = tk.Button(root, text="+10", command=increase_q0_charge_10)
increase_button_10.grid(row=1, column=5, padx=5)

plot_button = tk.Button(root, text="Generuj wykresy", command=plot_charging_process)
plot_button.grid(row=2, column=0, columnspan=6, padx=5, pady=5, sticky='ew')

root.grid_columnconfigure(1, weight=1)

root.mainloop()
