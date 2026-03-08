import argparse
from src.config import Settings
from src.data.feed import get_mock_data, get_yfinance_data
from src.strategy.ma_crossover import MovingAverageCrossover
from src.backtest.engine import run_backtest
from src.backtest.reporting import save_backtest_outputs
from src.paper.engine import run_paper_loop
from src.risk.manager import RiskManager


def main() -> None:
    parser = argparse.ArgumentParser(description="Gold trading bot starter")
    parser.add_argument("--mode", choices=["backtest", "paper"], default="backtest")
    parser.add_argument("--source", choices=["auto", "yfinance", "mock"], default="auto")
    parser.add_argument("--save-report", action="store_true", help="Save summary/trades/equity files to reports/")
    args = parser.parse_args()

    settings = Settings.from_env()

    strategy = MovingAverageCrossover(short_window=20, long_window=50)
    risk_manager = RiskManager(
        risk_per_trade=settings.risk_per_trade,
        stop_loss_pct=settings.stop_loss_pct,
        take_profit_pct=settings.take_profit_pct,
        max_position_notional_pct=settings.max_position_notional_pct,
    )

    if args.mode == "backtest":
        source = args.source if args.source != "auto" else settings.data_provider

        if source == "yfinance":
            df = get_yfinance_data(
                symbol=settings.yfinance_symbol,
                timeframe=settings.timeframe,
                period=settings.yfinance_period,
            )
            print(f"Using yfinance data: {settings.yfinance_symbol}, tf={settings.timeframe}, period={settings.yfinance_period}")
        else:
            df = get_mock_data()
            print("Using mock data")

        report, equity_df, trades_df = run_backtest(
            df=df,
            strategy=strategy,
            initial_balance=settings.initial_balance,
            risk_manager=risk_manager,
            return_details=True,
            commission_bps=settings.commission_bps,
            slippage_bps=settings.slippage_bps,
        )

        print("=== Backtest Report ===")
        for k, v in report.items():
            print(f"{k}: {v}")

        if args.save_report:
            out_dir = save_backtest_outputs(report=report, equity_df=equity_df, trades_df=trades_df)
            print(f"Report files saved to: {out_dir}")
    else:
        run_paper_loop(
            symbol=settings.yfinance_symbol,
            timeframe=settings.timeframe,
            period=settings.yfinance_period,
            poll_seconds=settings.paper_poll_seconds,
            max_loops=settings.paper_max_loops,
            strategy=strategy,
            risk_manager=risk_manager,
            initial_balance=settings.initial_balance,
            commission_bps=settings.commission_bps,
            slippage_bps=settings.slippage_bps,
        )


if __name__ == "__main__":
    main()
