"""
Main entry point for the Bookvoed parser application.

This module provides the command-line interface for running the parser
with configurable parameters.
"""

import asyncio
import argparse

from core.parser import BookvoedParser
from logging_config import logger


async def main() -> None:
    """Main entry point for the Bookvoed parser.
    
    Parses command-line arguments, initializes the parser, and starts
    the parsing process. Handles graceful shutdown on interrupts.
    
    Command-line arguments:
        --start-page: Starting page number for catalog parsing (default: 1)
        --concurrent: Number of concurrent book parsing tasks (default: 30)
        --delay: Delay between HTTP requests in seconds (default: 0.1)
        
    Example:
        python main.py --start-page 100 --concurrent 50 --delay 0.2
    """
    parser = argparse.ArgumentParser(description='Parser for bookvoed.ru')
    parser.add_argument('--start-page', type=int, default=1,
                       help='Starting page number')
    parser.add_argument('--concurrent', type=int, default=30,
                       help='Number of concurrent tasks')
    parser.add_argument('--delay', type=float, default=0.1,
                       help='Delay between requests')
    
    args = parser.parse_args()
    
    bookvoed_parser = None
    try:
        bookvoed_parser = BookvoedParser(
            max_concurrent_tasks=args.concurrent,
            delay=args.delay
        )
        
        async with bookvoed_parser:
            await bookvoed_parser.parse_bookvoed(start_page=args.start_page)
            
    except KeyboardInterrupt:
        logger.info('Received interrupt signal.')
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
    finally:
        if bookvoed_parser:
            await bookvoed_parser.close()
        logger.info('Parser finished')


if __name__ == '__main__':
    asyncio.run(main())
