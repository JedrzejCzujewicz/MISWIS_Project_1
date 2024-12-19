import numpy as np
from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.integrate import odeint
from scipy.optimize import minimize
import control
import time


class Drone:
    def __init__(self, name, mass, max_thrust):
        self.name = name
        self.mass = mass  # kg
        self.max_thrust = max_thrust  # N


# Definicja popularnych dronów
DRONES = {
    f"DJI Mini 2 (masa: 0.249 kg, max ciąg: 10 N)": Drone("DJI Mini 2", 0.249, 10),
    f"DJI Mavic 3 (masa: 0.895 kg, max ciąg: 30 N)": Drone("DJI Mavic 3", 0.895, 30),
    f"DJI Matrice 300 RTK (masa: 3.6 kg, max ciąg: 100 N)": Drone("DJI Matrice 300 RTK", 3.6, 100)
}


def create_system_equations(drone):
    def system(state, t, u):
        h, v = state
        dv = (u - drone.mass * 9.81) / drone.mass
        dh = v
        return [dh, dv]

    return system


def simulate_drone_with_params(drone, target_height, initial_height, Kp, Ti, Td, duration=60, dt=0.01):
    """Symulacja z podanymi parametrami PID"""
    t = np.arange(0, duration, dt)
    h = np.zeros_like(t)
    v = np.zeros_like(t)
    u = np.zeros_like(t)

    h[0] = initial_height
    v[0] = 0

    error_integral = 0
    prev_error = 0

    system = create_system_equations(drone)

    for i in range(1, len(t)):
        error = target_height - h[i - 1]
        error_integral += error * dt
        error_derivative = (error - prev_error) / dt

        u[i - 1] = (Kp * (error +
                          error_integral / Ti +
                          Td * error_derivative))

        u[i - 1] = np.clip(u[i - 1], 0, drone.max_thrust)

        state = odeint(system, [h[i - 1], v[i - 1]], [0, dt], args=(u[i - 1],))
        h[i] = state[-1, 0]
        v[i] = state[-1, 1]

        prev_error = error

    u[-1] = u[-2]
    return t, h, u


# Definicja kolorów dla ciemnego motywu
DARK_THEME = {
    'background': '#1f2630',
    'panel': '#2d3443',
    'text': '#ffffff',
    'button': '#3d4554',
    'button_hover': '#4d5565'
}

# Tworzenie aplikacji Dash
app = Dash(__name__)

# Layout aplikacji
app.layout = html.Div([
    # Tytuł strony
    html.Div([
        html.H1("Regulator wysokości dronów",
                style={'textAlign': 'center', 'marginBottom': '30px'})
    ]),

    # Kontener dla dwóch kolumn
    html.Div([
        # Lewa kolumna - kontrolki
        html.Div([
            # Wybór drona
            html.Div([
                html.Label("Wybór drona:",
                           style={'fontSize': '18px', 'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='drone-select',
                    options=[{'label': key, 'value': key}
                             for key in DRONES.keys()],
                    value=list(DRONES.keys())[0],
                    style={'marginTop': '5px', 'marginBottom': '20px'},
                    clearable=False
                ),
            ]),

            # Wysokość początkowa
            html.Div([
                html.Div([
                    html.Label("Wysokość początkowa [m]: ",
                               style={'fontSize': '18px', 'fontWeight': 'bold'}),
                    html.Span(id='initial-height-display',
                              style={'fontSize': '18px', 'fontWeight': 'bold'})
                ]),
                html.Div([
                    html.Button('-10', id='initial-minus10', n_clicks=0,
                                style={'margin': '5px'}),
                    html.Button('-1', id='initial-minus1', n_clicks=0,
                                style={'margin': '5px'}),
                    html.Button('+1', id='initial-plus1', n_clicks=0,
                                style={'margin': '5px'}),
                    html.Button('+10', id='initial-plus10', n_clicks=0,
                                style={'margin': '5px'}),
                ], style={'marginTop': '10px', 'marginBottom': '20px'})
            ]),

            # Wysokość zadana
            html.Div([
                html.Div([
                    html.Label("Wysokość zadana [m]: ",
                               style={'fontSize': '18px', 'fontWeight': 'bold'}),
                    html.Span(id='target-height-display',
                              style={'fontSize': '18px', 'fontWeight': 'bold'})
                ]),
                html.Div([
                    html.Button('-10', id='target-minus10', n_clicks=0,
                                style={'margin': '5px'}),
                    html.Button('-1', id='target-minus1', n_clicks=0,
                                style={'margin': '5px'}),
                    html.Button('+1', id='target-plus1', n_clicks=0,
                                style={'margin': '5px'}),
                    html.Button('+10', id='target-plus10', n_clicks=0,
                                style={'margin': '5px'}),
                ], style={'marginTop': '10px', 'marginBottom': '20px'})
            ]),

            # Sekcja parametrów PID
            html.Div([
                html.H3("Parametry regulatora PID",
                        style={'marginTop': '20px'}),
                html.Div([
                    html.Label("Kp: "),
                    html.Span(id='kp-display'),
                    dcc.Slider(
                        id='kp-slider',
                        min=0,
                        max=100,
                        step=0.1,
                        value=20,
                        marks={i: str(i) for i in range(0, 101, 20)},
                        className='mb-4'
                    )
                ]),
                html.Div([
                    html.Label("Ti: "),
                    html.Span(id='ti-display'),
                    dcc.Slider(
                        id='ti-slider',
                        min=0.1,
                        max=10,
                        step=0.1,
                        value=4.0,
                        marks={i: str(i) for i in range(0, 11, 2)},
                        className='mb-4'
                    )
                ]),
                html.Div([
                    html.Label("Td: "),
                    html.Span(id='td-display'),  # Poprawione z td='td-display' na id='td-display'
                    dcc.Slider(
                        id='td-slider',
                        min=0.1,
                        max=5,
                        step=0.1,
                        value=1.5,
                        marks={i: str(i) for i in range(0, 6)},
                        className='mb-4'
                    )
                ])
            ], style={'marginTop': '20px'})

        ], style={'width': '30%',
                  'display': 'inline-block',
                  'verticalAlign': 'top',
                  'padding': '20px',
                  'backgroundColor': '#f8f9fa',
                  'borderRadius': '10px'}),

        # Prawa kolumna - wykresy
        html.Div([
            dcc.Graph(id='simulation-graphs')
        ], style={'width': '65%',
                  'display': 'inline-block',
                  'verticalAlign': 'top',
                  'marginLeft': '20px'}),

    ], style={'width': '100%', 'display': 'flex', 'justifyContent': 'space-between'}),

    # Ukryte komponenty do przechowywania stanu
    dcc.Store(id='initial-height', data=0),
    dcc.Store(id='target-height', data=10),

], style={'padding': '20px', 'fontFamily': 'Arial'})


@app.callback(
    [Output('initial-height', 'data'),
     Output('initial-height-display', 'children')],
    [Input('initial-minus10', 'n_clicks'),
     Input('initial-minus1', 'n_clicks'),
     Input('initial-plus1', 'n_clicks'),
     Input('initial-plus10', 'n_clicks')],
    [State('initial-height', 'data')]
)
def update_initial_height(minus10, minus1, plus1, plus10, current_height):
    ctx = callback_context
    if not ctx.triggered:
        return current_height, f"{current_height} m"

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'initial-minus10':
        current_height = max(0, current_height - 10)
    elif button_id == 'initial-minus1':
        current_height = max(0, current_height - 1)
    elif button_id == 'initial-plus1':
        current_height = min(120, current_height + 1)  # Ograniczenie do 120m
    elif button_id == 'initial-plus10':
        current_height = min(120, current_height + 10)  # Ograniczenie do 120m

    return current_height, f"{current_height} m"


@app.callback(
    [Output('target-height', 'data'),
     Output('target-height-display', 'children')],
    [Input('target-minus10', 'n_clicks'),
     Input('target-minus1', 'n_clicks'),
     Input('target-plus1', 'n_clicks'),
     Input('target-plus10', 'n_clicks')],
    [State('target-height', 'data')]
)
def update_target_height(minus10, minus1, plus1, plus10, current_height):
    ctx = callback_context
    if not ctx.triggered:
        return current_height, f"{current_height} m"

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'target-minus10':
        current_height = max(0, current_height - 10)
    elif button_id == 'target-minus1':
        current_height = max(0, current_height - 1)
    elif button_id == 'target-plus1':
        current_height = min(120, current_height + 1)  # Ograniczenie do 120m
    elif button_id == 'target-plus10':
        current_height = min(120, current_height + 10)  # Ograniczenie do 120m

    return current_height, f"{current_height} m"


@app.callback(
    [Output('kp-display', 'children'),
     Output('ti-display', 'children'),
     Output('td-display', 'children')],
    [Input('kp-slider', 'value'),
     Input('ti-slider', 'value'),
     Input('td-slider', 'value')]
)
def update_pid_params(kp, ti, td):
    return f"{kp:.2f}", f"{ti:.2f}", f"{td:.2f}"


@app.callback(
    Output('simulation-graphs', 'figure'),
    [Input('drone-select', 'value'),
     Input('initial-height', 'data'),
     Input('target-height', 'data'),
     Input('kp-slider', 'value'),
     Input('ti-slider', 'value'),
     Input('td-slider', 'value')]
)
def update_graphs(drone_name, initial_height, target_height, kp, ti, td):
    drone = DRONES[drone_name]
    t, h, u = simulate_drone_with_params(drone, target_height, initial_height, kp, ti, td)

    # Obliczanie granic tunelu ±2%
    upper_bound = target_height * 1.02
    lower_bound = target_height * 0.98

    # Znajdowanie maksymalnego przeregulowania
    max_overshoot_value = max(h)
    max_overshoot_idx = np.argmax(h)
    max_overshoot_time = t[max_overshoot_idx]
    overshoot_percent = ((max_overshoot_value - target_height) / target_height) * 100

    # Znajdowanie momentu wejścia do tunelu
    in_tunnel = False
    settling_time = None
    for i in range(len(t)):
        if lower_bound <= h[i] <= upper_bound and not in_tunnel:
            in_tunnel = True
            settling_time = t[i]
            # Sprawdzamy czy system pozostaje w tunelu
            for j in range(i, len(t)):
                if not (lower_bound <= h[j] <= upper_bound):
                    in_tunnel = False
                    settling_time = None
                    break
            if in_tunnel:
                break

    fig = make_subplots(rows=2, cols=1,
                        subplot_titles=('Wysokość', 'Sygnał sterujący'))

    # Podstawowe wykresy
    fig.add_trace(
        go.Scatter(x=t, y=h, name='Aktualna wysokość',
                   line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=t, y=[target_height] * len(t), name='Wysokość zadana',
                   line=dict(color='red', dash='dash')),
        row=1, col=1
    )

    # Dodanie tunelu akceptowalnego uchybu
    fig.add_trace(
        go.Scatter(x=t, y=[upper_bound] * len(t),
                   name='Górna granica (2%)',
                   line=dict(color='rgba(255,0,0,0.2)', dash='dot')),
        row=1, col=1
    )

    # Wypełnienie tunelu
    upper_line = [upper_bound] * len(t)
    lower_line = [lower_bound] * len(t)
    x_tunnel = list(t) + list(t)[::-1]
    y_tunnel = upper_line + lower_line[::-1]

    fig.add_trace(
        go.Scatter(x=x_tunnel,
                   y=y_tunnel,
                   fill='toself',
                   fillcolor='rgba(255,0,0,0.1)',
                   line=dict(color='rgba(255,0,0,0)'),
                   name='Tunel ±2%'),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=t, y=[lower_bound] * len(t),
                   name='Dolna granica (2%)',
                   line=dict(color='rgba(255,0,0,0.2)', dash='dot')),
        row=1, col=1
    )

    # Dodanie znacznika czasu ustalania
    if settling_time is not None:
        fig.add_trace(
            go.Scatter(x=[settling_time], y=[h[int(settling_time / t[1])]],
                       mode='markers+text',
                       name=f'Czas ustalania: {settling_time:.2f}s',
                       text=[f't={settling_time:.2f}s'],
                       textposition='top center',
                       marker=dict(size=10, symbol='triangle-down'),
                       textfont=dict(size=12)),
            row=1, col=1
        )

    # Dodanie znacznika maksymalnego przeregulowania
    if overshoot_percent > 0:
        fig.add_trace(
            go.Scatter(x=[max_overshoot_time], y=[max_overshoot_value],
                       mode='markers+text',
                       name=f'Przeregulowanie: {overshoot_percent:.1f}%',
                       text=[f'MP={overshoot_percent:.1f}%'],
                       textposition='top center',
                       marker=dict(size=10, symbol='circle'),
                       textfont=dict(size=12)),
            row=1, col=1
        )

    fig.add_trace(
        go.Scatter(x=t, y=u, name='Siła ciągu',
                   line=dict(color='green')),
        row=2, col=1
    )

    fig.update_layout(height=800, showlegend=True)
    fig.update_xaxes(title_text="Czas [s]", row=2, col=1)
    fig.update_yaxes(title_text="Wysokość [m]", row=1, col=1)
    fig.update_yaxes(title_text="Siła ciągu [N]", row=2, col=1)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
