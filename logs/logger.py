"""Sistema de logging centralizado."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from config.configuration import (
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE,
    LOG_FILE_PARSER,
    LOG_FILE_AGENT,
    LOG_MAX_SIZE_MB,
    LOG_BACKUP_COUNT
)


def setup_logger(
    name: str,
    log_file: Path | None = None,
    level: str = LOG_LEVEL,
    console: bool = True,
) -> logging.Logger:
    """
    Configura e retorna um logger.
    
    Args:
        name: Nome do logger
        log_file: Arquivo de log (opcional)
        level: Nível de log
        console: Se deve exibir no console
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()
    
    formatter = logging.Formatter(LOG_FORMAT)
    
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOG_MAX_SIZE_MB * 1024 * 1024,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

app_logger = setup_logger("nf_processor", LOG_FILE)
parser_logger = setup_logger("parser", LOG_FILE_PARSER)
agent_logger = setup_logger("agent", LOG_FILE_AGENT)