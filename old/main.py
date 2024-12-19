from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Słownik z parametrami telefonów
smartphones = {
    "iPhone 8": {"Q_max": 1.821, "V_nom": 3.82, "I_max": 3.14, "P_max": 12},
    "iPhone X": {"Q_max": 2.716, "V_nom": 3.81, "I_max": 4.7, "P_max": 18},
    "iPhone 11": {"Q_max": 3.110, "V_nom": 3.83, "I_max": 4.7, "P_max": 18},
    "iPhone 12": {"Q_max": 2.815, "V_nom": 3.83, "I_max": 5.2, "P_max": 20},
    "iPhone 13": {"Q_max": 3.240, "V_nom": 3.83, "I_max": 6.0, "P_max": 23},
    "iPhone 14": {"Q_max": 3.279, "V_nom": 3.83, "I_max": 6.5, "P_max": 25},
    "iPhone 15": {"Q_max": 3.349, "V_nom": 3.83, "I_max": 6.5, "P_max": 25},
    "iPhone 16": {"Q_max": 3.561, "V_nom": 3.83, "I_max": 6.5, "P_max": 25},
}


def advanced_voltage_model(q, Q_max, V_nom, V_min=3.0, V_max=4.2):
    """
    Bardziej zaawansowany model napięcia baterii litowo-jonowej

    Parametry:
    q: aktualny ładunek (Ah)
    Q_max: maksymalna pojemność baterii (Ah)
    V_nom: nominalne napięcie baterii (V)
    V_min: minimalne napięcie baterii (V)
    V_max: maksymalne napięcie baterii (V)

    Zwraca: napięcie baterii w danym momencie ładowania
    """
    # Normalizacja ładunku
    soc = q / Q_max

    # Model krzywej ładowania baterii litowo-jonowej
    # Krzywa przypominająca kształt sigmoidy
    if soc < 0.2:
        # Powolny wzrost napięcia na początku ładowania
        voltage = V_min + (V_nom - V_min) * (soc / 0.2) ** 2
    elif soc < 0.8:
        # Prawie liniowy wzrost napięcia
        voltage = V_nom
    else:
        # Spowolnienie wzrostu napięcia pod koniec ładowania
        voltage = V_max - (V_max - V_nom) * np.exp(-(soc - 0.8) / 0.2)

    return voltage


def simulate_charging(phone, charger_power, start_percent, end_percent):
    phone_params = smartphones[phone]
    Q_max = phone_params["Q_max"]  # Pojemność baterii (Ah)
    V_nom = phone_params["V_nom"]  # Napięcie nominalne (V)
    P_max = min(phone_params["P_max"], charger_power)  # Ograniczenie mocy (W)

    time = []  # Czas w minutach
    current = []  # Prąd ładowania (A)
    power = []  # Moc ładowania (W)
    voltage = []  # Napięcie (V)
    charge = []  # Naładowanie (%)

    start_charge = start_percent / 100 * Q_max  # Ładunek początkowy (Ah)
    end_charge = end_percent / 100 * Q_max  # Ładunek końcowy (Ah)

    dt = 1  # Krok czasowy (minuta)
    t = 0
    q = start_charge

    # Próg przejścia do fazy CV
    cv_threshold = 0.8 * Q_max

    # Minimalny próg prądu ładowania
    min_current = 0.25  # 0.1A

    while q < end_charge:
        # Dynamiczne obliczanie napięcia
        V_current = advanced_voltage_model(q, Q_max, V_nom)

        # Faza stałego prądu (CC)
        if q < cv_threshold:
            I = min(P_max / V_current, phone_params["I_max"])
        # Faza stałego napięcia (CV)
        else:
            # Nieliniowa redukcja prądu w fazie CV
            remaining_capacity = end_charge - q
            cv_factor = np.exp(-5 * (q - cv_threshold) / (0.2 * Q_max))
            I = min(
                cv_factor * P_max / V_current,  # Zmniejszanie prądu wykładniczo
                remaining_capacity / (dt / 60),  # Ograniczenie aby nie przekroczyć końcowej pojemności
                phone_params["I_max"]  # Ograniczenie maksymalnego prądu telefonu
            )

        # Ustaw minimalny prąd ładowania
        I = max(I, min_current)

        P = I * V_current  # Moc ładowania

        time.append(t)
        current.append(I)
        power.append(P)
        voltage.append(V_current)
        charge.append(q / Q_max * 100)

        dq = I * (dt / 60)  # Przyrost ładunku (Ah)
        q += dq
        t += dt

    return time, current, power, voltage, charge


# Inicjalizacja aplikacji Dash
app = Dash(__name__)

app.layout = html.Div(
    style={"display": "flex", "flex-direction": "row"},
    children=[
        # Lewa kolumna: Wybór parametrów
        html.Div(
            style={"flex": "25%", "padding": "20px", "border-right": "1px solid #ddd"},
            children=[
                html.H1("Symulacja Ładowania Baterii Smartphone'a", style={"textAlign": "center", "fontFamily": "Comic Sans MS"}),

                html.Label("Wybierz Model Smartphone'a:", style={"fontFamily": "Comic Sans MS"}),
                dcc.Dropdown(
                    id="phone",
                    options=[{"label": model, "value": model} for model in smartphones.keys()],
                    value="iPhone 16",
                    style={"margin-bottom": "20px"},
                    clearable=False
                ),

                html.Label("Wybierz Moc Ładowarki:", style={"fontFamily": "Comic Sans MS"}),
                dcc.Dropdown(
                    id="charger_power",
                    options=[{"label": f"{power}W", "value": power} for power in [5, 12, 20, 30]],
                    value=30,
                    style={"margin-bottom": "20px"},
                    clearable=False
                ),

                html.Label("Początkowy Stan (%) Baterii:", style={"fontFamily": "Comic Sans MS"}),
                html.Div(
                    children=[
                        dcc.Slider(
                            id="start_percent",
                            min=0,
                            max=100,
                            step=1,
                            value=0,
                            marks={i: f"{i}%" for i in range(0, 101, 25)},
                            tooltip={"placement": "bottom", "always_visible": False}
                        ),
                    ],
                    style={"margin-bottom": "20px"}
                ),

                html.Label("Do Ilu % Chcesz Naładować:", style={"fontFamily": "Comic Sans MS"}),
                html.Div(
                    children=[
                        dcc.Slider(
                            id="end_percent",
                            min=80,
                            max=100,
                            step=1,
                            value=80,
                            marks={i: f"{i}%" for i in range(80, 101, 5)},
                            tooltip={"placement": "bottom", "always_visible": False}
                        ),
                    ],
                    style={"margin-bottom": "20px"}
                )
            ]
        ),

        # Prawa kolumna: Wykresy
        html.Div(
            style={"flex": "75%", "padding": "20px"},
            children=[
                dcc.Graph(id="charging_graph")
            ]
        )
    ]
)


@app.callback(
    Output("charging_graph", "figure"),
    Input("phone", "value"),
    Input("charger_power", "value"),
    Input("start_percent", "value"),
    Input("end_percent", "value")
)
def update_graph(phone, charger_power, start_percent, end_percent):
    if start_percent >= end_percent:
        fig = go.Figure()
        fig.update_layout(
            title="Błąd! Stan początkowy baterii nie może być wyższy od stanu końcowego.",
            xaxis_title="Time (minutes)",
            yaxis_title="Value"
        )
        return fig

    time, current, power, voltage, charge = simulate_charging(phone, charger_power, start_percent, end_percent)

    # Układ wykresów w 2x2
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Zmiana Prądu w Czasie", "Zmiana Mocy w Czasie", "Zmiana Napięcia w Czasie", "Poziom Naładowania Baterii:")
    )

    # Dodanie wykresów do odpowiednich miejsc z ustawieniem min na 0
    fig.add_trace(go.Scatter(x=time, y=current, mode='lines', name='Prąd (A)'), row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=power, mode='lines', name='Moc (W)'), row=1, col=2)
    fig.add_trace(go.Scatter(x=time, y=voltage, mode='lines', name='Napięcie (V)'), row=2, col=1)
    fig.add_trace(go.Scatter(x=time, y=charge, mode='lines', name='Poziom Baterii (%)'), row=2, col=2)

    # Aktualizacja osi
    fig.update_xaxes(title_text="Czas (minuty)", row=1, col=1)
    fig.update_xaxes(title_text="Czas (minuty)", row=1, col=2)
    fig.update_xaxes(title_text="Czas (minuty)", row=2, col=1)
    fig.update_xaxes(title_text="Czas (minuty)", row=2, col=2)

    fig.update_yaxes(title_text="Prąd (A)", row=1, col=1, rangemode='tozero')
    fig.update_yaxes(title_text="Moc (W)", row=1, col=2, rangemode='tozero')
    fig.update_yaxes(title_text="Napięcie (V)", row=2, col=1, rangemode='tozero')
    fig.update_yaxes(title_text="Poziom Baterii (%)", row=2, col=2, rangemode='tozero')

    fig.update_layout(
        title=f"Symulacja ładowania baterii dla: {phone}, ładowarką o mocy {charger_power}W",
        height=800
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
