import click
import MetaTrader5 as mt5
import pandas as pd

@click.command()
@click.option('--ativo', default='WINQ25', help='Símbolo do ativo.')
@click.option('--dias', default=5, help='Número de dias de histórico.')
@click.option('--periodo', default=5, help='Período em minutos (1, 5, 15, 60 etc).')
@click.option('--salvar', is_flag=True, help='Salvar resultado em CSV.')
def macd(ativo, dias, periodo, salvar):
    if not mt5.initialize():
        click.echo("Erro ao conectar ao MetaTrader 5.")
        return

    # Dicionário de timeframes
    timeframes = {
        1: mt5.TIMEFRAME_M1,
        5: mt5.TIMEFRAME_M5,
        15: mt5.TIMEFRAME_M15,
        30: mt5.TIMEFRAME_M30,
        60: mt5.TIMEFRAME_H1
    }

    if periodo not in timeframes:
        click.echo("Período inválido. Use 1, 5, 15, 30 ou 60.")
        mt5.shutdown()
        return

    tf = timeframes[periodo]
    total_barras = dias * (1440 // periodo)
    rates = mt5.copy_rates_from_pos(ativo, tf, 0, total_barras)

    if rates is None or len(rates) == 0:
        click.echo("Sem dados recebidos.")
        mt5.shutdown()
        return

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    # MACD
    fast_ema = df['close'].ewm(span=12, adjust=False).mean()
    slow_ema = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = fast_ema - slow_ema
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['histograma'] = df['macd'] - df['signal']

    click.echo(df[['close', 'macd', 'signal', 'histograma']].tail(10))

    if salvar:
        df.to_csv(f'{ativo}macd{periodo}min.csv')
        click.echo("MACD salvo em CSV.")

    mt5.shutdown()

if __name__ == '__main__':
    macd()
