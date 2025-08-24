import click
import MetaTrader5 as mt5
import pandas as pd
from mtcli.conecta import conectar, shutdown
from mtcli.logger import setup_logger


logger = setup_logger("macd")


@click.command()
@click.version_option(package_name="mtcli-macd")
@click.option(
    "--symbol", "-s", default="WIN$N", help="Símbolo do ativo (default WIN$N)."
)
@click.option(
    "--dias", type=int, default=5, help="Número de dias de histórico (default 5)."
)
@click.option(
    "--period", "-p", type=int, default=5, help="Timeframe em minutos (default 5)."
)
@click.option("--salvar", is_flag=True, help="Salvar resultado em CSV.")
def macd(symbol, dias, period, salvar):
    """Calcula o MACD do ativo symbol."""
    conectar()

    # Dicionário de timeframes
    timeframes = {
        1: mt5.TIMEFRAME_M1,
        2: mt5.TIMEFRAME_M2,
        3: mt5.TIMEFRAME_M3,
        4: mt5.TIMEFRAME_M4,
        5: mt5.TIMEFRAME_M5,
        6: mt5.TIMEFRAME_M6,
        10: mt5.TIMEFRAME_M10,
        12: mt5.TIMEFRAME_M12,
        15: mt5.TIMEFRAME_M15,
        20: mt5.TIMEFRAME_M20,
        30: mt5.TIMEFRAME_M30,
        60: mt5.TIMEFRAME_H1,
    }

    if period not in timeframes:
        click.echo(f"Timeframe {period}  inválido. Use 1, 5, 15, 30 ou 60.")
        logger.error(f"Timeframe {period} inválido.")
        shutdown()
        return

    tf = timeframes[period]
    total_barras = dias * (1440 // period)
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, total_barras)

    if rates is None or len(rates) == 0:
        click.echo(f"Sem dados recebidos para o ativo {symbol}.")
        logger.info(f"Nenhum dado recebido do ativo {symbol}.")
        shutdown()
        return

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)

    # MACD
    fast_ema = df["close"].ewm(span=12, adjust=False).mean()
    slow_ema = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = fast_ema - slow_ema
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["histograma"] = df["macd"] - df["signal"]

    click.echo(df[["close", "macd", "signal", "histograma"]].tail(10))

    if salvar:
        df.to_csv(f"{symbol}macd{period}min.csv")
        click.echo("MACD salvo em CSV.")
        logger.info("MACD salvo em csv.")

    shutdown()


if __name__ == "__main__":
    macd()
