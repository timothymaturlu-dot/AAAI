"""
Core Engine Spokes Fleet Array (Modules 1 - 6)
Houses structural math tracking analytics matrices.
"""

import numpy as np

# ==============================================================================
# SPOKE 1: SMC / ICT STRUCTURAL SCANNER
# ==============================================================================
class SMCIctSpokeEngine:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.engine_id = "ENGINE_SMC_ICT_M15"

    def scan_for_liquidity_and_fvg(self, high_prices, low_prices, close_prices) -> dict:
        if len(close_prices) < 3: return {"status": "NO_SETUP"}
        c1_high, c1_low = high_prices[-3], low_prices[-3]
        c2_high, c2_low = high_prices[-2], low_prices[-2]
        c3_high, c3_low = high_prices[-1], low_prices[-1]

        if c3_low > c1_high:
            fvg_size = c3_low - c1_high
            proposed_entry = c1_high + (fvg_size * 0.5)
            return {
                "status": "SETUP_FOUND",
                "payload": {
                    "engine_id": self.engine_id,
                    "asset_pair": self.symbol,
                    "order_type": "BUY_LIMIT",
                    "entry_price": round(proposed_entry, 5),
                    "stop_loss": round(c2_low - (fvg_size * 0.2), 5),
                    "take_profit_primary": round(proposed_entry + (fvg_size * 4), 5),
                    "technical_parameters": {
                        "market_structure": "BULLISH_DISPLACEMENT",
                        "key_liquidity_sweep": "HTF_LIQUIDITY_POOL_SWEPT",
                        "fvg_mitigation_zone": f"M15_IMBALANCE_{round(fvg_size, 5)}",
                        "fibonacci_retracement_level": 0.618
                    }
                }
            }
        return {"status": "NO_SETUP"}


# ==============================================================================
# SPOKE 2: MALAYSIAN SNR FLIP ENGINE
# ==============================================================================
class MalaysianSnRSpokeEngine:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.engine_id = "ENGINE_MALAYSIAN_SNR_M5"

    def evaluate_clean_support_flip(self, historical_peaks, current_bid_price) -> dict:
        for support_level in historical_peaks:
            if abs(current_bid_price - support_level) <= 0.00020:
                return {
                    "status": "SETUP_FOUND",
                    "payload": {
                        "engine_id": self.engine_id,
                        "asset_pair": self.symbol,
                        "order_type": "SELL_LIMIT",
                        "entry_price": round(support_level, 5),
                        "stop_loss": round(support_level + 0.00150, 5),
                        "take_profit_primary": round(support_level - 0.00450, 5),
                        "technical_parameters": {
                            "market_structure": "SUPPORT_BECOMES_RESISTANCE",
                            "key_liquidity_sweep": "RETEST_OF_SIGNIFICANT_LEFT_SHOULDER",
                            "fvg_mitigation_zone": "NONE_HORIZONTAL_FLIP",
                            "fibonacci_retracement_level": 0.0
                        }
                    }
                }
        return {"status": "NO_SETUP"}


# ==============================================================================
# SPOKE 3: HIGH-SPEED MOMENTUM MICRO-SCALPER
# ==============================================================================
class HFTScalperSpokeEngine:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.engine_id = "ENGINE_HFT_SCALPER_TICK"

    def analyze_orderflow_velocity(self, bid_stream, ask_stream) -> dict:
        if len(bid_stream) < 10: return {"status": "NO_SETUP"}
        velocity_delta = np.diff(bid_stream[-10:]).sum()

        if velocity_delta > 0.00050:
            return {
                "status": "SETUP_FOUND",
                "payload": {
                    "engine_id": self.engine_id,
                    "asset_pair": self.symbol,
                    "order_type": "BUY",
                    "entry_price": round(ask_stream[-1], 5),
                    "stop_loss": round(bid_stream[-1] - 0.00080, 5),
                    "take_profit_primary": round(ask_stream[-1] + 0.00120, 5),
                    "technical_parameters": {
                        "market_structure": "MOMENTUM_VELOCITY_SPIKE",
                        "key_liquidity_sweep": "ORDER_BOOK_IMBALANCE",
                        "fvg_mitigation_zone": "MICRO_TICK_GAP",
                        "fibonacci_retracement_level": 0.0
                    }
                }
            }
        return {"status": "NO_SETUP"}


# ==============================================================================
# SPOKE 4: MTF RSI MOMENTUM DIVERGENCE ENGINE
# ==============================================================================
class MTFRSIDivergenceEngine:
    def __init__(self, symbol: str, rsi_period: int = 14):
        self.symbol = symbol
        self.engine_id = "ENGINE_MTF_RSI_DIVERGENCE"
        self.rsi_period = rsi_period

    def calculate_rsi(self, close_prices, period: int = 14) -> np.ndarray:
        deltas = np.diff(close_prices)
        seed = deltas[:period]  # FIX: was deltas[:period+1], which pulled in one
                                 # extra delta than the seed window should contain.
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period

        # FIX (RSI edge case): previously `rs = up / down if down != 0 else 0`
        # forced RSI to 0 whenever there were zero losing candles in the
        # window. Zero losses is a maximally BULLISH/overbought condition,
        # so RSI should resolve near 100 in that case, not 0 — the old code
        # had this exactly backwards, which would make
        # verify_mtf_momentum_alignment() silently fail to flag strong
        # uptrends as overbought.
        if down == 0:
            rsi_seed_value = 100.0 if up > 0 else 50.0
        else:
            rs = up / down
            rsi_seed_value = 100. - 100. / (1. + rs)

        rsi = np.zeros_like(close_prices, dtype=float)
        rsi[:period + 1] = rsi_seed_value

        for i in range(period + 1, len(close_prices)):
            delta = deltas[i - 1]
            up_val = delta if delta > 0 else 0.
            down_val = -delta if delta < 0 else 0.
            up = (up * (period - 1) + up_val) / period
            down = (down * (period - 1) + down_val) / period
            if down == 0:
                rsi[i] = 100.0 if up > 0 else 50.0
            else:
                rs = up / down
                rsi[i] = 100. - 100. / (1. + rs)
        return rsi

    def verify_mtf_momentum_alignment(self, w1_bias: str, m5_rsi_value: float) -> dict:
        if w1_bias == "NEUTRAL":
            return {"status": "REJECTED", "reason": "No clear Weekly master storyline defined."}
        if w1_bias == "BULLISH" and m5_rsi_value <= 32.0:
            return {"status": "ALIGNED", "bias": "BULLISH"}
        if w1_bias == "BEARISH" and m5_rsi_value >= 68.0:
            return {"status": "ALIGNED", "bias": "BEARISH"}
        return {"status": "WAITING_FOR_CONFLUENCE"}


# ==============================================================================
# SPOKE 5: HARMONIC GEOMETRY PATTERN PATTERNS
# ==============================================================================
class HarmonicPatternSpokeEngine:
    def __init__(self, symbol: str, tolerance: float = 0.015):
        self.symbol = symbol
        self.engine_id = "ENGINE_HARMONIC_GEOMETRY_H1"
        self.tolerance = tolerance

    def _is_within_tolerance(self, target, calculated) -> bool:
        return abs(target - calculated) <= self.tolerance

    def validate_harmonic_nodes(self, x: float, a: float, b: float, c: float, d: float) -> dict:
        xa, ab, bc = abs(a - x), abs(b - a), abs(c - b)
        if xa == 0 or ab == 0 or bc == 0: return {"status": "NO_SETUP"}

        b_to_xa, c_to_ab, d_to_xa = ab / xa, bc / ab, abs(d - x) / xa
        direction = "BUY" if d < c else "SELL"

        if self._is_within_tolerance(0.618, b_to_xa) and (0.382 <= c_to_ab <= 0.886) and self._is_within_tolerance(0.786, d_to_xa):
            return self._build_payload("GARTLEY", direction, d, abs(d - x) * 0.1, abs(d - c))
        if (0.382 <= b_to_xa <= 0.500) and (0.382 <= c_to_ab <= 0.886) and self._is_within_tolerance(0.886, d_to_xa):
            return self._build_payload("BAT", direction, d, abs(d - x) * 0.1, abs(d - c))
        return {
            "status": "REJECTED",
            "student_telemetry": {"calculated_B_leg_ratio": round(b_to_xa, 3), "calculated_D_leg_ratio": round(d_to_xa, 3)}
        }

    def _build_payload(self, name, order_type, d_price, risk, reward) -> dict:
        sl = d_price - risk if order_type == "BUY" else d_price + risk
        tp = d_price + (reward * 2) if order_type == "BUY" else d_price - (reward * 2)
        return {
            "status": "SETUP_FOUND",
            "payload": {
                "engine_id": self.engine_id, "asset_pair": self.symbol, "order_type": order_type,
                "entry_price": round(d_price, 5), "stop_loss": round(sl, 5), "take_profit_primary": round(tp, 5),
                "technical_parameters": {
                    "market_structure": f"HARMONIC_{name}_PATTERN", "key_liquidity_sweep": "POTENTIAL_REVERSAL_ZONE",
                    "fvg_mitigation_zone": "GEOMETRIC_ALIGNMENT", "fibonacci_retracement_level": round(d_price, 3)
                }
            }
        }


# ==============================================================================
# SPOKE 6: MTF TRENDLINE + PRICE ACTION SNIPER
# ==============================================================================
class MTFPriceActionSniperSpoke:
    def __init__(self, symbol: str, price_tolerance: float = 0.00015):
        self.symbol = symbol
        self.engine_id = "ENGINE_MTF_PA_SNIPER_M5"
        self.tolerance = price_tolerance

    def _verify_confluence(self, current_price, trendline_y, malaysian_snr) -> bool:
        return abs(current_price - trendline_y) <= self.tolerance and abs(current_price - malaysian_snr) <= self.tolerance

    def audit_and_trigger_sniper_entry(self, w1_bias: str, htf_zone: dict, m30_structure: dict, m5_candles: list, rsi_aligned: bool) -> dict:
        if not rsi_aligned or len(m5_candles) < 2:
            return {"status": "REJECTED", "reason": "Sniper conditions unaligned."}

        c3 = m5_candles[-1]
        current_m5_price = c3["close"]
        if not (htf_zone["zone_bottom"] <= current_m5_price <= htf_zone["zone_top"]):
            return {"status": "TRACKING", "reason": "Price outside HTF mitigation boundaries."}

        m5_range = c3["high"] - c3["low"]
        if m5_range == 0: return {"status": "NO_SETUP"}
        m5_body = abs(c3["close"] - c3["open"])
        m5_lower_wick = min(c3["open"], c3["close"]) - c3["low"]
        m5_upper_wick = c3["high"] - max(c3["open"], c3["close"])

        if w1_bias == "BULLISH":
            if (m5_lower_wick / m5_range) >= 0.65 and (m5_body / m5_range) <= 0.35: # Pin bar
                return self._compile_payload("BUY", current_m5_price, m30_structure["structural_low"], m30_structure["target_high"])
        elif w1_bias == "BEARISH":
            if (m5_upper_wick / m5_range) >= 0.65 and (m5_body / m5_range) <= 0.35: # Shooting star
                return self._compile_payload("SELL", current_m5_price, m30_structure["structural_high"], m30_structure["target_low"])

        return {"status": "WAITING_FOR_CANDLE_CLOSE"}

    def _compile_payload(self, order_type, entry, sl, tp) -> dict:
        return {
            "status": "SETUP_FOUND",
            "payload": {
                "engine_id": self.engine_id, "asset_pair": self.symbol, "order_type": order_type,
                "entry_price": round(entry, 5), "stop_loss": round(sl, 5), "take_profit_primary": round(tp, 5),
                "technical_parameters": {
                    "market_structure": "MTF_SNIPER_CONFLUENCE", "key_liquidity_sweep": "WEEKLY_ALIGNED",
                    "fvg_mitigation_zone": "HTF_ZONE_MITIGATED", "fibonacci_retracement_level": "M5_CANDLE_TRIGGER"
                }
            }
        }
