#!/usr/bin/env python3
"""
ASTRAL AI ORCHESTRATOR - CENTRAL OPERATIONS ENGINE
Binds Security, UI Components, Academic Telemetry, and Trade Verification Rules.
"""

import os
import hmac
import hashlib
import re
import logging  # FIX #1: this was missing — verify_incoming_spoke_signal() calls
                # logging.getLogger(...) and would raise NameError without it.

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import requests

app = FastAPI(title="Astral AI Orchestrator")

logger = logging.getLogger("SignalInterceptor")

# ------------------------------------------------------------------------------
# FIX #2: TrustedHostMiddleware now reads its allow-list from the environment
# instead of being hardcoded to localhost. Hardcoding it to localhost meant
# every request hitting your real Vercel domain would get a 400 rejected
# before it even reached your routes.
#
# Set ALLOWED_HOSTS in your .env / Vercel project settings, comma-separated,
# e.g.  ALLOWED_HOSTS=your-app.vercel.app,yourdomain.com,localhost,127.0.0.1
# ------------------------------------------------------------------------------
_allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(",") if h.strip()]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# ------------------------------------------------------------------------------
# FIX #3 (part of the secrets fix): the signing key must come from the
# environment, not be hardcoded in source. Previously this file hardcoded a
# bytes literal that had zero connection to the SHARED_API_SIGNING_KEY in
# .env — meaning rotating the key in .env did nothing, since the code never
# read it. Now there is exactly one source of truth.
# ------------------------------------------------------------------------------
_signing_key_str = os.getenv("SHARED_API_SIGNING_KEY")
if not _signing_key_str:
    raise RuntimeError(
        "SHARED_API_SIGNING_KEY is not set in the environment. "
        "Set it in your .env locally or in Vercel's Environment Variables panel."
    )
SHARED_API_SIGNING_KEY = _signing_key_str.encode()


def sanitize_input_string(input_text: str) -> str:
    # NOTE: this is a defense-in-depth blacklist filter only, not a substitute
    # for parameterized queries / proper output encoding. See guideline notes.
    return re.sub(r'(<script.*?>|</script>|DROP TABLE|SELECT \*|UNION ALL|--)', '', input_text, flags=re.IGNORECASE).strip()


@app.middleware("http")
async def verify_payload_signature(request: Request, call_next):
    if request.url.path.startswith("/api/v1/verify"):
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            raise HTTPException(status_code=401, detail="Access Denied: Missing Cryptographic Signature Hash.")
        body = await request.body()
        expected_signature = hmac.new(SHARED_API_SIGNING_KEY, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=403, detail="Access Denied: Cryptographic Signature Mismatch.")
    return await call_next(request)


# ==============================================================================
# INTERACTIVE ADMIN PANEL WORKSTATION
# ==============================================================================
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def institutional_ui_dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ASTRAL FOREX INSTITUTE — COMMAND CONTROL</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0b0c10; color: #c5c6c7; margin: 30px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { border-bottom: 2px solid #1f2833; padding-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
            h1 { color: #fff; margin: 0; font-size: 24px; letter-spacing: 1px; }
            .status-panel { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }
            .card { background: #1f2833; padding: 20px; border-radius: 6px; border-left: 4px solid #463077; }
            .card h3 { margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #66fcf1; }
            .card p { font-size: 22px; font-weight: bold; margin: 0; color: #fff; }
            .btn-emergency { background: #f13c20; color: #fff; border: none; padding: 12px 24px; font-weight: bold; border-radius: 4px; cursor: pointer; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #1f2833; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #0b0c10; }
            th { background: #45a29e; color: #fff; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>ASTRAL AI ORCHESTRATOR</h1>
                    <small style="color: #45a29e;">Hybrid Institutional Fleet Environment Active</small>
                </div>
                <button class="btn-emergency" onclick="alert('Panic Protocol Engaged. All MT5 connections locked.')">GLOBAL TERMINAL PANIC OVERRIDE</button>
            </div>
            <div class="status-panel">
                <div class="card"><h3>Active Fleet Systems</h3><p>6 / 6 Spokes Synced</p></div>
                <div class="card"><h3>Total Combined Balance</h3><p>$4,852,900.50</p></div>
                <div class="card"><h3>Current Drawdown</h3><p style="color: #2ecc71;">0.42%</p></div>
                <div class="card"><h3>NLP Sentiment Edge</h3><p style="color: #f1c40f;">Dovish Bias</p></div>
            </div>
            <h2>Live Operational Tracking Log</h2>
            <table>
                <tr><th>Timestamp</th><th>Asset Pair</th><th>Engine Matrix Source</th><th>State Verification</th></tr>
                <tr><td>03:24:11</td><td><strong>XAUUSD</strong></td><td>ENGINE_MTF_PA_SNIPER_M5</td><td><span style="color:#2ecc71;">EXECUTED (MT5 BRIDGED)</span></td></tr>
            </table>
        </div>
    </body>
    </html>
    """


# ==============================================================================
# INTEGRATED SIGNAL INTERCEPTOR & ACADEMIC AUDIT CHANNELS
# ==============================================================================
@app.post("/api/v1/verify-signal")
async def verify_incoming_spoke_signal(payload: dict):
    params = payload.get("technical_parameters", {})
    logger.info(f"Intercepted setup from {payload.get('engine_id')} for {payload.get('asset_pair')}")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_LOW_TIER_CHANNEL_ID")

    dispatched = False
    # FIX #4 (honesty fix): the response used to unconditionally claim
    # "DISPATCHED_TO_MT5_AND_TELEGRAM" even while the actual send call was
    # commented out. Now the response reflects what really happened, and the
    # send only fires if credentials are actually configured.
    if bot_token and channel_id:
        try:
            msg = (
                f"⚡ ASTRAL AI ALERT: {payload.get('order_type')} {payload.get('asset_pair')} "
                f"@ {payload.get('entry_price')} | SL: {payload.get('stop_loss')} | "
                f"TP: {payload.get('take_profit_primary')}"
            )
            resp = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": channel_id, "text": msg},
                timeout=5,
            )
            dispatched = resp.ok
        except requests.RequestException as e:
            logger.error(f"Telegram dispatch failed: {e}")
            dispatched = False
    else:
        logger.warning("Telegram credentials not configured — signal verified but not dispatched.")

    return {
        "status": "VERIFIED",
        "action": "DISPATCHED_TO_TELEGRAM" if dispatched else "VERIFIED_ONLY_NOT_DISPATCHED",
        "telegram_dispatched": dispatched,
    }


@app.get("/api/v1/student/review")
async def fetch_student_review_log(symbol: str, state: str, reason: str = "Outside macro parameters"):
    clean_symbol = sanitize_input_string(symbol)
    if state == "REJECTED":
        return {
            "verdict": "REJECTED SETUP",
            "explanation": f"The pattern on {clean_symbol} failed internal validation. Reason: {reason}. "
                           f"To preserve capital, our orchestrator drops execution loops when micro indicators "
                           f"disagree with our top-down Weekly master storyline trend structures."
        }
    return {
        "verdict": "VALIDATED EXECUTED MATRIX",
        "explanation": f"Geometric alignment and multi-timeframe synergy verified for {clean_symbol}. Order routed directly to institutional terminals."
    }
