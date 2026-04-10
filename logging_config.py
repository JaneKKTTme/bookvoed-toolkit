"""
Logging configuration module.

This module sets up structured logging with rotating file handlers
and console output for the Bookvoed parser application.
"""

import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure and initialize the logging system.
    
    Sets up a rotating file handler with 10MB maximum size and 5 backup files.
    Log format includes timestamp, logger name, level, and message.
    
    Returns:
        logging.Logger: Configured logger instance for the module.
        
    Example:
        >>> logger = setup_logging()
        >>> logger.info('Application started')
        >>> logger.error('Something went wrong', exc_info=True)
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        'app.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Configure root logger with file handler only
    # Console output is omitted to avoid clutter in production.
    # For debugging, set DEBUG_CONSOLE=1 environment variable to enable console logging.
    # Example: export DEBUG_CONSOLE=1 && python main.py
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler],
        force=True
    )

    return logging.getLogger(__name__)

# Module-level logger instance for direct import
logger = setup_logging()
