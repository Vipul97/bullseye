from .model import Model
from django.http import Http404
from django.shortcuts import render
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime
import yfinance as yf

MODEL_FILENAME = 'viz/model.pkl'
SCALER_FILENAME = 'viz/scaler.pkl'


def get_ticker_history(ticker, period='5y'):
    ticker_history = yf.Ticker(ticker).history(period=period)

    for col in ['Open', 'High', 'Low', 'Close']:
        for window in [5, 10, 20, 50, 100, 150, 200]:
            col_window = f'{col} {window} Day MA'
            ticker_history[col_window] = ticker_history[col].rolling(window=window).mean()

    return ticker_history


def create_plot(ticker_history):
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_width=[0.2, 0.8]
    )

    fig.add_trace(
        go.Candlestick(
            x=ticker_history.index,
            open=ticker_history['Open'],
            high=ticker_history['High'],
            low=ticker_history['Low'],
            close=ticker_history['Close'],
            name='Candlestick',
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Bar(x=ticker_history.index, y=ticker_history['Volume'], marker=dict(color='blue'), showlegend=False),
        row=2,
        col=1
    )

    for col in ['Open', 'High', 'Low', 'Close']:
        fig.add_trace(
            go.Scatter(x=ticker_history.index, y=ticker_history[col], name=col, visible='legendonly'),
            row=1,
            col=1
        )

    for col in ['Open', 'High', 'Low', 'Close']:
        for window in [5, 10, 20, 50, 100, 150, 200]:
            col_window = f'{col} {window} Day MA'
            fig.add_trace(
                go.Scatter(x=ticker_history.index, y=ticker_history[col_window], name=col_window, visible='legendonly'),
                row=1,
                col=1
            )

    today = datetime.date.today()
    last_month = today.replace(month=today.month - 1)
    fig.update_layout(
        height=800,
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label='1D', step='day', stepmode='backward'),
                    dict(count=5, label='5D', step='day', stepmode='backward'),
                    dict(count=1, label='1M', step='month', stepmode='backward'),
                    dict(count=6, label='6M', step='month', stepmode='backward'),
                    dict(count=1, label='YTD', step='year', stepmode='todate'),
                    dict(count=1, label='1Y', step='year', stepmode='backward'),
                    dict(count=5, label='5Y', step='year', stepmode='backward'),
                    # dict(label='MAX', step='all')
                ]
            ),
            range=[last_month, today]
        ),
        legend=dict(orientation='h'),
    )
    fig.update(layout_xaxis_rangeslider_visible=False)

    return plot(fig, output_type='div', config=dict({'scrollZoom': True, 'doubleClick': 'autosize'}))


def viz(request):
    ticker = request.GET.get('ticker')
    ticker_history = get_ticker_history(ticker)

    if ticker_history.empty:
        raise Http404("Invalid Ticker!")

    model = Model(MODEL_FILENAME, SCALER_FILENAME)
    ticker_info = yf.Ticker(ticker).info

    long_name = ticker_info["longName"]
    price = ticker_info["currentPrice"]
    prev_close = ticker_info["previousClose"]
    change = price - prev_close
    change_percent = change / price * 100
    color = "green" if change > 0 else "red"
    plus = "+" if change > 0 else ""
    prediction = model.predict(ticker_history)
    prediction_color = "green" if prediction > price else "red"
    plot_div = create_plot(ticker_history)

    context = {
        'long_name': long_name,
        'price': f'{price:.2f}',
        'color': color,
        'plus': plus,
        'change': f'{change:.2f}',
        'change_percent': f'{change_percent:.2f}',
        'prediction_color': prediction_color,
        'prediction': f'{prediction:.2f}',
        'year': datetime.datetime.now().year,
        'plot_div': plot_div
    }

    return render(request, 'viz/base.html', context=context)
