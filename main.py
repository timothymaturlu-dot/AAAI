#!/usr/bin/env python3
"""
Institutional AI Fleet Orchestrator - Entry Point
Runs zero-trust preflight checks, then exposes the FastAPI `app` object
that Vercel's @vercel/python builder (and uvicorn locally) actually needs.

FIX #3: previously the preflight-check script and the FastAPI app lived in
two separate files, and the checker script never imported or exposed `app`.
vercel.json pointed @vercel/python at this file expecting an ASGI `app`
object — it would have found none. This file now does both jobs.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CORE_INIT] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("OrchestratorInit")


class SystemSanityChecker:
    def __init__(self):
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            # On Vercel there is no .env file on disk — env vars come from
            # the project's Environment Variables settings instead, so this
            # is expected there and should not be fatal.
            logger.info("No local .env file found — assuming environment variables are injected by the platform (e.g. Vercel).")

    def verify_cryptography(self) -> bool:
        signing_key = os.getenv("SHARED_API_SIGNING_KEY")
        enc_key = os.getenv("DATABASE_ENCRYPTION_KEY")

        if not signing_key or len(signing_key) < 64:
            logger.critical("Security Breach: SHARED_API_SIGNING_KEY is missing or mathematically weak.")
            return False

        if not enc_key:
            logger.critical("Security Breach: DATABASE_ENCRYPTION_KEY is unassigned.")
            return False

        logger.info("Cryptographic Verification Matrix: SECURE")
        return True

    def verify_mtls_paths(self) -> bool:
        if os.getenv("ENVIRONMENT") != "production":
            logger.warning("Running in non-production development fallback mode. Skipping cert checks.")
            return True

        required_paths = [
            "MTLS_CA_CERT_PATH",
            "MTLS_SERVER_CERT_PATH",
            "MTLS_SERVER_KEY_PATH"
        ]

        for path_env in required_paths:
            resolved_path = os.getenv(path_env)
            if not resolved_path or not Path(resolved_path).exists():
                logger.critical(f"Infrastructure Fault: Path variable '{path_env}' mapped to '{resolved_path}' cannot be verified.")
                return False

        logger.info("mTLS Topology Paths: VERIFIED")
        return True

    def verify_redis_connection(self) -> bool:
        redis_host = os.getenv("REDIS_HOST")
        if not redis_host:
            logger.warning("REDIS_HOST not set — skipping Redis check (feature not in use).")
            return True
        try:
            import redis
            r = redis.Redis(
                host=redis_host,
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD"),
                db=int(os.getenv("REDIS_DB_INDEX", 0)),
                socket_timeout=3.0
            )
            if r.ping():
                logger.info("Redis Core Layer Mesh Synchronization: ONLINE")
                return True
        except Exception as e:
            logger.critical(f"Data Infrastructure Engine Fault: Cannot establish pipeline to Redis. Context: {str(e)}")
            return False
        return False

    def execute_preflight_checks(self, hard_fail: bool = True):
        logger.info("Initializing Pre-flight Isolation Audits...")
        checks_passed = (
            self.verify_cryptography()
            and self.verify_mtls_paths()
            and self.verify_redis_connection()
        )
        if not checks_passed:
            msg = "Pre-flight checks failed."
            if hard_fail:
                logger.critical(msg + " Aborting startup.")
                sys.exit(1)
            else:
                logger.critical(msg + " Continuing in degraded mode (serverless environment).")
        else:
            logger.info("All Multi-Layer Systems Aligned. System Boot Cleared.")


# ------------------------------------------------------------------------------
# Run preflight checks at import time. On Vercel, this module is imported
# fresh on cold start; a hard sys.exit(1) here would kill the function
# instead of returning a normal HTTP error, so we run checks non-fatally
# when not running as a local `python main.py` script.
# ------------------------------------------------------------------------------
_checker = SystemSanityChecker()
_is_direct_run = __name__ == "__main__"
_checker.execute_preflight_checks(hard_fail=_is_direct_run)

# Import the actual FastAPI application AFTER checks, and expose it at
# module level — this `app` object is what @vercel/python and uvicorn need.
from orchestrator import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    logger.info("Spawning FastAPI Orchestrator locally via uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
