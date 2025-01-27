import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from functools import wraps
import time
import traceback
import asyncio
import functools

class AgentLogger:
    _instances = {}

    def __new__(cls, agent_name: str):
        if agent_name not in cls._instances:
            cls._instances[agent_name] = super(AgentLogger, cls).__new__(cls)
        return cls._instances[agent_name]

    def __init__(self, agent_name: str):
        if not hasattr(self, 'logger'):
            self.agent_name = agent_name
            self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file and console handlers"""
        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # Create logger
        logger = logging.getLogger(self.agent_name)
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            # File handler - separate file for each agent
            file_handler = logging.FileHandler(
                log_dir / f'{self.agent_name}_{datetime.now().strftime("%Y%m%d")}.log'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        return logger

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

def log_execution_time(func: Callable):
    """Decorator to log function execution time"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = AgentLogger(func.__name__)
        start_time = time.time()
        try:
            logger.debug(f"Starting execution of {func.__name__}")
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"Completed {func.__name__} in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {execution_time:.2f} seconds: {str(e)}")
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = AgentLogger(func.__name__)
        start_time = time.time()
        try:
            logger.debug(f"Starting execution of {func.__name__}")
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"Completed {func.__name__} in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {execution_time:.2f} seconds: {str(e)}")
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
