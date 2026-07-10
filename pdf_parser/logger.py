import logging
import os
import sys

def setup_logging():
    """Initializes logging with separate logs for INFO messages and ERROR messages."""
    # Determine base directory depending on execution context (source or bundled .exe)
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    info_log_path = os.path.join(base_dir, "pdf_parser.log")
    error_log_path = os.path.join(base_dir, "pdf_parser_error.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if setup is run multiple times
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

        # Info (all details) handler
        try:
            info_handler = logging.FileHandler(info_log_path, mode='a', encoding='utf-8')
            info_handler.setLevel(logging.INFO)
            info_handler.setFormatter(formatter)
            logger.addHandler(info_handler)
        except Exception as e:
            print(f"Warning: Could not create info log file: {e}", file=sys.stderr)

        # Error only handler
        try:
            error_handler = logging.FileHandler(error_log_path, mode='a', encoding='utf-8')
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
        except Exception as e:
            print(f"Warning: Could not create error log file: {e}", file=sys.stderr)

        # Configure stdout and stderr for UTF-8 support to prevent encoding errors on terminals
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
            except Exception:
                pass
        if hasattr(sys.stderr, 'reconfigure'):
            try:
                sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
            except Exception:
                pass

        # Console output handler (useful for CLI mode)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

