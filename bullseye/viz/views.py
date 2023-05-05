from .model import Model
from django.shortcuts import render
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime
import yfinance as yf


def get_ticker_histories(tickers, period='5y'):
    histories = {}

    for ticker in tickers:
        history = yf.Ticker(ticker).history(period=period)

        for col in ['Open', 'High', 'Low', 'Close']:
            for window in [5, 10, 20, 50, 100, 150, 200]:
                col_window = f'{col} {window} Day MA'
                history[col_window] = history[col].rolling(window=window).mean()

        histories[ticker] = history

    return histories


def create_plot(ticker_histories, model):
    def get_title(ticker, history, model):
        ticker_info = yf.Ticker(ticker).info
        long_name = ticker_info["longName"]
        price = ticker_info["currentPrice"]
        prev_close = ticker_info["previousClose"]
        change = price - prev_close
        change_percent = change / price * 100
        color = "green" if change > 0 else "red"
        plus = "+" if change > 0 else ""
        prediction = model.predict(history)
        prediction_color = "green" if prediction > price else "red"

        return f'<b>{long_name}</b><br><b style="font-size: 20px;">{price:.2f}</b> ' \
               f'<span style="color: {color};">{plus}{change:.2f} ({plus}{change_percent:.2f}%)</span><br>' \
               f'Close Price prediction for next working day: <b style="font-size: 20px; color: {prediction_color};">{prediction:.2f}</b>'

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_width=[0.2, 0.8]
    )

    for ticker, history in ticker_histories.items():
        fig.add_trace(
            go.Candlestick(
                x=history.index,
                open=history['Open'],
                high=history['High'],
                low=history['Low'],
                close=history['Close'],
                name='Candlestick',
                visible=False
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Bar(x=history.index, y=history['Volume'], marker=dict(color='blue'), showlegend=False, visible=False),
            row=2,
            col=1
        )

        for col in ['Open', 'High', 'Low', 'Close']:
            fig.add_trace(
                go.Scatter(x=history.index, y=history[col], name=col, visible=False),
                row=1,
                col=1
            )

        for col in ['Open', 'High', 'Low', 'Close']:
            for window in [5, 10, 20, 50, 100, 150, 200]:
                col_window = f'{col} {window} Day MA'
                fig.add_trace(
                    go.Scatter(x=history.index, y=history[col_window], name=col_window, visible=False),
                    row=1,
                    col=1
                )

    today = datetime.date.today()
    last_month = today.replace(month=today.month - 1)
    n_tickers = len(ticker_histories)
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
        updatemenus=[
            dict(
                buttons=[
                            dict(
                                label='Select Ticker',
                                method='update',
                                args=[
                                    {'visible': [False for _ in range(n_tickers * 34)]},
                                    {'title': None}
                                ]
                            )
                        ] + [
                            dict(
                                label=ticker,
                                method='update',
                                args=[
                                    {'visible': [False] * (34 * i) + [True] * 2 + ['legendonly'] * 32 + [False] * (
                                            34 * n_tickers - i)},
                                    {
                                        'title': get_title(ticker, ticker_histories[ticker], model)
                                    }
                                ]
                            )
                            for i, ticker in enumerate(ticker_histories)
                        ],
                direction='right',
                xanchor='left',
                x=0,
                y=1.3
            )
        ],
        legend=dict(orientation='h')
    )
    fig.update(layout_xaxis_rangeslider_visible=False)

    return plot(fig, output_type='div', config=dict({'scrollZoom': True, 'doubleClick': 'autosize'}))


def viz(request):
    tickers = ['MSFT', 'META', 'AAPL', 'GOOG', 'AMZN']
    ticker_histories = get_ticker_histories(tickers)
    model = Model('viz/model.pkl', 'viz/scaler.pkl')
    plot_div = create_plot(ticker_histories, model)

    return render(request, 'viz/base.html', context={'plot_div': plot_div})
