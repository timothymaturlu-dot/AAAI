#!/usr/bin/env python3
"""
Institutional AI Fleet Orchestrator - Core Initialization Engine
Validates zero-trust state boundaries before starting production runtime.
"""

import os
import sys
import logging
import redis
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
        if not env_path.exists():
            logger.critical("Bootstrapping Failed: Matrix Configuration File (.env) not found.")
            sys.exit(1)
        load_dotenv(dotenv_path=env_path)

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
        # Skip checking in dev fallback mode if certificates aren't generated yet
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
        try:
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD"),
                db=int(os.getenv("REDIS_DB_INDEX", 0)),
                socket_timeout=3.0
            )
            if r.ping():
                logger.info("Redis Core Layer Mesh Synchronization: ONLINE")
                return True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.critical(f"Data Infrastructure Engine Fault: Cannot establish pipeline to Redis. Context: {str(e)}")
            return False
        return False

    def execute_preflight_checks(self):
        logger.info("Initializing Pre-flight Isolation Audits...")
        if not self.verify_cryptography() or not self.verify_mtls_paths() or not self.verify_redis_connection():
            sys.exit(1)
        logger.info("All Multi-Layer Systems Aligned. System Boot Cleared.")


if __name__ == "__main__":
    checker = SystemSanityChecker()
    checker.execute_preflight_checks()
    logger.info("Spawning FastAPI Orchestrator Application Thread Pools...")
