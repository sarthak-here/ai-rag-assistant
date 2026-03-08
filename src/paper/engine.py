import time
from dataclasses import dataclass

from src.data.feed import get_yfinance_data
from src.risk.manager import RiskManager


@dataclass
class PaperState:
    equity: float
    in_position: bool = False
    side: int = 0  # 1 long, -1 short
    units: float = 0.0
    entry_price: float = 0.0
    stop_price: float = 0.0
    take_profit_price: float = 0.0
    entry_fee: float = 0.0


def run_paper_loop(
    *,
    symbol: str,
    timeframe: str,
    period: str,
    poll_seconds: int,
    max_loops: int,
    strategy,
    risk_manager: RiskManager,
    initial_balance: float,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
) -> None:
    state = PaperState(equity=float(initial_balance))
    commission_rate = max(0.0, float(commission_bps)) / 10_000
    slippage_rate = max(0.0, float(slippage_bps)) / 10_000

    print("=== Paper Trading Started ===")
    print(
        f"symbol={symbol} timeframe={timeframe} poll={poll_seconds}s loops={max_loops} "
        f"commission_bps={commission_bps} slippage_bps={slippage_bps}"
    )

    loop = 0
    while max_loops <= 0 or loop < max_loops:
        loop += 1
        df = get_yfinance_data(symbol=symbol, timeframe=timeframe, period=period)
        price = float(df["close"].iloc[-1])

        signals = strategy.generate_signals(df).fillna(0)
        signal = int(signals.iloc[-2]) if len(signals) > 1 else 0  # avoid acting on the still-forming candle

        action = "HOLD"
        pnl = 0.0

        if state.in_position:
            if state.side == 1:
                if price <= state.stop_price:
                    exit_fill = price * (1 - slippage_rate)
                    pnl = state.units * (exit_fill - state.entry_price)
                    pnl -= abs(state.units * exit_fill) * commission_rate
                    action = "EXIT_LONG_SL"
                elif price >= state.take_profit_price:
                    exit_fill = price * (1 - slippage_rate)
                    pnl = state.units * (exit_fill - state.entry_price)
                    pnl -= abs(state.units * exit_fill) * commission_rate
                    action = "EXIT_LONG_TP"
            elif state.side == -1:
                if price >= state.stop_price:
                    exit_fill = price * (1 + slippage_rate)
                    pnl = state.units * (state.entry_price - exit_fill)
                    pnl -= abs(state.units * exit_fill) * commission_rate
                    action = "EXIT_SHORT_SL"
                elif price <= state.take_profit_price:
                    exit_fill = price * (1 + slippage_rate)
                    pnl = state.units * (state.entry_price - exit_fill)
                    pnl -= abs(state.units * exit_fill) * commission_rate
                    action = "EXIT_SHORT_TP"

            if action.startswith("EXIT"):
                state.equity += pnl
                state.in_position = False
                state.side = 0
                state.units = 0.0
                state.entry_fee = 0.0

        if not state.in_position and signal in (1, -1):
            notional = risk_manager.position_notional(equity=state.equity, entry_price=price)
            if notional > 0:
                entry_fill = price * (1 + slippage_rate) if signal == 1 else price * (1 - slippage_rate)
                state.units = notional / entry_fill
                state.side = signal
                state.entry_price = entry_fill
                state.entry_fee = abs(state.units * entry_fill) * commission_rate
                state.equity -= state.entry_fee
                if state.side == 1:
                    state.stop_price = entry_fill * (1 - risk_manager.stop_loss_pct)
                    state.take_profit_price = entry_fill * (1 + risk_manager.take_profit_pct)
                    action = "ENTER_LONG"
                else:
                    state.stop_price = entry_fill * (1 + risk_manager.stop_loss_pct)
                    state.take_profit_price = entry_fill * (1 - risk_manager.take_profit_pct)
                    action = "ENTER_SHORT"
                state.in_position = True

        mtm_equity = state.equity
        if state.in_position:
            if state.side == 1:
                mtm_equity += state.units * (price - state.entry_price)
            else:
                mtm_equity += state.units * (state.entry_price - price)

        print(
            f"loop={loop} price={price:.2f} signal={signal:+d} action={action} "
            f"equity={state.equity:.2f} mtm={mtm_equity:.2f} in_pos={state.in_position}"
        )

        if max_loops > 0 and loop >= max_loops:
            break

        time.sleep(max(1, poll_seconds))

    print("=== Paper Trading Stopped ===")
    print(f"final_equity={state.equity:.2f}")
