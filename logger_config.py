# logger_config.py
import logging

logger = logging.getLogger("LangGraph POC")
logger.setLevel(logging.DEBUG)  # Set to DEBUG for development

# Avoid adding handlers multiple times if this file is imported repeatedly
if not logger.handlers:
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(filename)s | %(funcName)s | Line: %(lineno)d | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
