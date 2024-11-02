import numpy as np
from scipy.integrate import solve_ivp
import tkinter as tk
from tkinter import ttk
import plotly.graph_objects as go
import plotly.offline as pyo

# Parametry poczatkowe
V_nom = 3.85  # nominalne napięcie baterii (V)
R_int = 0.1  # rez wewnętrzna (ohm)
eta_ladowanie = 0.9  # sprawnosc ladowania
time_span_charge = [0, 3]  # czas symulacji (h)

smartphones = {
    "iPhone 14 - 3A (5V)": {"Q_max": 3.279, "I_charge": 3.0},
    "iPhone 14 - 2.22A (9V)": {"Q_max": 3.279, "I_charge": 2.22},
    "Samsung Galaxy S23 - 3A (5V)": {"Q_max": 3.9, "I_charge": 3.0},
    "Samsung Galaxy S23 - 2.77A (9V)": {"Q_max": 3.9, "I_charge": 2.77},
    "Google Pixel 7 - 2.5A (5V)": {"Q_max": 4.0, "I_charge": 2.5},
    "Google Pixel 7 - 2.0A (9V)": {"Q_max": 4.0, "I_charge": 2.0},
    "OnePlus 11 - 3.0A (5V)": {"Q_max": 4.5, "I_charge": 3.0},
    "OnePlus 11 - 2.5A (9V)": {"Q_max": 4.5, "I_charge": 2.5},
}

class PID:
    def __init__(self, kp, ti, td, setpoint=100):
        self.kp = kp
        self.ti = ti
        self.td = td
        self.setpoint = setpoint
        self.integral = 0
        self.previous_error = 0

    def compute(self, measured_value, dt):
        error = self.setpoint - measured_value
        p = self.kp * error
        if self.ti != 0:
            self.integral += error * dt / self.ti
        i = self.kp * self.integral
        d = self.kp * self.td * (error - self.previous_error) / dt if dt > 0 else 0
        self.previous_error = error
        output = p + i + d
        return output  # Nie wprowadzono limitu

def battery_dynamics_nonlinear(t, Q, I, Q_max, eta_ladowanie, pid_controller, dt):
    battery_percentage = to_percentage(Q, Q_max)
    I_adjusted = pid_controller.compute(battery_percentage, dt)
    I_effective = eta_ladowanie * I_adjusted * (1 - Q / Q_max)
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
    pid_controller = PID(kp=0.1, ti=4.0, td=0.1) #parametry regulatora
    time_eval = np.linspace(time_span_charge[0], time_span_charge[1], 100)
    dt = time_eval[1] - time_eval[0]
    sol_ladowanie = solve_ivp(
        lambda t, Q: battery_dynamics_nonlinear(t, Q, I_charge, Q_max, eta_ladowanie, pid_controller, dt),
        time_span_charge,
        [Q0],
        t_eval=time_eval
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sol_ladowanie.t,
                             y=to_percentage(sol_ladowanie.y[0], Q_max),
                             mode='lines', name='Stan naładowania'))
    fig.update_layout(title='Stan naładowania baterii',
                      xaxis_title='Czas (h)',
                      yaxis_title='Procent Baterii (%)',
                      showlegend=True)
    pyo.iplot(fig)

# GUI
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

# Ustawienia GUI
root = tk.Tk()
root.title("Symulacja procesu ładowania baterii")
root.geometry("350x100")
root.minsize(350, 100)

smartphone_label = tk.Label(root, text="Wybierz smartfon:", font=("TkDefaultFont", 8, "bold"))
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
