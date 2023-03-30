from django.shortcuts import render
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import yfinance as yf


def get_ticker_histories(tickers, period='5y'):
    histories = {}

    for ticker in tickers:
        history = yf.Ticker(ticker).history(period=period)

        for col in ['Open', 'High', 'Low', 'Close']:
            for window in [5, 10, 20, 50, 100, 150, 200]:
                history[f'{col} {window} Day MA'] = history[col].rolling(window=window).mean()

        histories[ticker] = history

    return histories


def create_plot(ticker_histories):
    n_tickers = len(ticker_histories)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=[None, 'Volume'],
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
            col=1,
        )

        fig.add_trace(
            go.Bar(x=history.index, y=history['Volume'], marker_color='blue', showlegend=False, visible=False),
            row=2,
            col=1,
        )

        for col in ['Open', 'High', 'Low', 'Close']:
            for window in [5, 10, 20, 50, 100, 150, 200]:
                fig.add_trace(
                    go.Scatter(x=history.index, y=history[f'{col} {window} Day MA'], name=f'{col} {window} Day MA',
                               visible=False),
                    row=1,
                    col=1,
                )

    fig.update_layout(
        yaxis_title='Price (USD)',
        height=800,
        updatemenus=[
            dict(
                buttons=[
                            dict(
                                label='Select Ticker',
                                method='update',
                                args=[
                                    {'visible': [False for _ in range(n_tickers * 30)]},
                                    {'title': None},
                                ]
                            )
                        ] + [
                            dict(
                                label=ticker,
                                method='update',
                                args=[
                                    {'visible': [False] * (30 * i) + [True] * 2 + ['legendonly'] * 28 + [False] * (
                                            30 * n_tickers - i)},
                                    {'title': ticker},
                                ]
                            )
                            for i, ticker in enumerate(ticker_histories)
                        ]
            )
        ]
    )
    fig.update(layout_xaxis_rangeslider_visible=False)

    return plot(fig, output_type='div', config=dict({"scrollZoom": True}))


def viz(request):
    tickers = ['MSFT', 'META', 'AAPL', 'GOOG', 'AMZN']
    ticker_histories = get_ticker_histories(tickers)
    plot_div = create_plot(ticker_histories)

    return render(request, "viz/viz.html", context={'plot_div': plot_div})
