import plotly.graph_objects as go

def price_chart(df):
    fig = go.Figure([go.Candlestick(
        x=df['date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close']
    )])
    fig.update_layout(height=400, margin=dict(l=0,r=0,t=25,b=0))
    return fig

def rsi_chart(df):
    fig = go.Figure(go.Scatter(x=df['date'], y=df['rsi']))
    fig.add_hline(y=70); fig.add_hline(y=30)
    fig.update_layout(height=250, margin=dict(l=0,r=0,t=25,b=0))
    return fig
