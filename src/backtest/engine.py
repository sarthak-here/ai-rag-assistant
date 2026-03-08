import pandas as pd

from src.risk.manager import RiskManager


def run_backtest(
    df: pd.DataFrame,
    strategy,
    initial_balance: float = 10000,
    risk_manager: RiskManager | None = None,
    return_details: bool = False,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
):
    if risk_manager is None:
        risk_manager = RiskManager()

    commission_rate = max(0.0, float(commission_bps)) / 10_000
    slippage_rate = max(0.0, float(slippage_bps)) / 10_000

    signals = strategy.generate_signals(df).fillna(0)
    prices = df["close"].reset_index(drop=True)

    equity = float(initial_balance)
    peak_equity = equity
    max_drawdown = 0.0

    in_position = False
    side = 0  # 1 long, -1 short
    units = 0.0
    entry_price = 0.0
    stop_price = 0.0
    take_profit_price = 0.0
    entry_index = -1

    trades = 0
    wins = 0
    total_fees = 0.0
    entry_fee = 0.0

    trade_rows = []
    equity_rows = [{"index": 0, "equity": equity}]

    for i in range(1, len(prices)):
        price = float(prices.iloc[i])
        signal = int(signals.iloc[i - 1])  # avoid look-ahead

        # Exit logic for open position
        if in_position:
            exit_now = False
            exit_reason = ""
            gross_pnl = 0.0

            if side == 1:  # long
                if price <= stop_price:
                    gross_pnl = units * (price - entry_price)
                    exit_now = True
                    exit_reason = "stop_loss"
                elif price >= take_profit_price:
                    gross_pnl = units * (price - entry_price)
                    exit_now = True
                    exit_reason = "take_profit"
            else:  # short
                if price >= stop_price:
                    gross_pnl = units * (entry_price - price)
                    exit_now = True
                    exit_reason = "stop_loss"
                elif price <= take_profit_price:
                    gross_pnl = units * (entry_price - price)
                    exit_now = True
                    exit_reason = "take_profit"

            if exit_now:
                exit_fill = price * (1 - slippage_rate) if side == 1 else price * (1 + slippage_rate)
                gross_pnl = units * (exit_fill - entry_price) if side == 1 else units * (entry_price - exit_fill)
                exit_fee = abs(units * exit_fill) * commission_rate
                fees = entry_fee + exit_fee
                pnl = gross_pnl - exit_fee

                equity += pnl
                total_fees += exit_fee
                trades += 1
                if pnl > 0:
                    wins += 1

                trade_rows.append(
                    {
                        "entry_index": entry_index,
                        "exit_index": i,
                        "side": "long" if side == 1 else "short",
                        "entry_price": round(entry_price, 6),
                        "exit_price": round(exit_fill, 6),
                        "units": round(units, 6),
                        "gross_pnl": round(gross_pnl, 6),
                        "fees": round(fees, 6),
                        "pnl": round(pnl, 6),
                        "exit_reason": exit_reason,
                    }
                )

                in_position = False
                side = 0
                units = 0.0
                entry_fee = 0.0

        # Entry logic (only when flat)
        if not in_position and signal in (1, -1):
            notional = risk_manager.position_notional(equity=equity, entry_price=price)
            if notional > 0:
                entry_fill = price * (1 + slippage_rate) if signal == 1 else price * (1 - slippage_rate)
                units = notional / entry_fill
                side = signal
                entry_price = entry_fill
                entry_index = i
                entry_fee = abs(units * entry_fill) * commission_rate
                equity -= entry_fee
                total_fees += entry_fee
                if side == 1:
                    stop_price = entry_price * (1 - risk_manager.stop_loss_pct)
                    take_profit_price = entry_price * (1 + risk_manager.take_profit_pct)
                else:
                    stop_price = entry_price * (1 + risk_manager.stop_loss_pct)
                    take_profit_price = entry_price * (1 - risk_manager.take_profit_pct)
                in_position = True

        # Mark-to-market for drawdown tracking
        mtm_equity = equity
        if in_position:
            if side == 1:
                mtm_equity += units * (price - entry_price)
            else:
                mtm_equity += units * (entry_price - price)

        equity_rows.append({"index": i, "equity": round(float(mtm_equity), 6)})

        peak_equity = max(peak_equity, mtm_equity)
        if peak_equity > 0:
            dd = (peak_equity - mtm_equity) / peak_equity
            max_drawdown = max(max_drawdown, dd)

    # Close open position at final price
    if in_position:
        final_price = float(prices.iloc[-1])
        exit_fill = final_price * (1 - slippage_rate) if side == 1 else final_price * (1 + slippage_rate)
        gross_pnl = units * (exit_fill - entry_price) if side == 1 else units * (entry_price - exit_fill)
        exit_fee = abs(units * exit_fill) * commission_rate
        fees = entry_fee + exit_fee
        pnl = gross_pnl - exit_fee

        equity += pnl
        total_fees += exit_fee
        trades += 1
        if pnl > 0:
            wins += 1

        trade_rows.append(
            {
                "entry_index": entry_index,
                "exit_index": len(prices) - 1,
                "side": "long" if side == 1 else "short",
                "entry_price": round(entry_price, 6),
                "exit_price": round(exit_fill, 6),
                "units": round(units, 6),
                "gross_pnl": round(gross_pnl, 6),
                "fees": round(fees, 6),
                "pnl": round(pnl, 6),
                "exit_reason": "end_of_data",
            }
        )

    total_return = (equity / initial_balance) - 1
    win_rate = (wins / trades * 100) if trades else 0.0

    report = {
        "initial_balance": round(initial_balance, 2),
        "final_balance": round(float(equity), 2),
        "total_return_pct": round(float(total_return * 100), 2),
        "max_drawdown_pct": round(float(max_drawdown * 100), 2),
        "trades": int(trades),
        "win_rate_pct": round(float(win_rate), 2),
        "risk_per_trade_pct": round(risk_manager.risk_per_trade * 100, 2),
        "stop_loss_pct": round(risk_manager.stop_loss_pct * 100, 2),
        "take_profit_pct": round(risk_manager.take_profit_pct * 100, 2),
        "commission_bps": round(float(commission_bps), 4),
        "slippage_bps": round(float(slippage_bps), 4),
        "fees_paid": round(float(total_fees), 2),
    }

    if return_details:
        equity_df = pd.DataFrame(equity_rows)
        trades_df = pd.DataFrame(trade_rows)
        return report, equity_df, trades_df

    return report
