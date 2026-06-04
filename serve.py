#!/usr/bin/env python3
"""
Start a local server and open the flashcard app in the browser.

Usage:
    python3 serve.py                          # opens vocabulary.json
    python3 serve.py lesson2/vocabulary.json  # opens a different vocab file
    python3 serve.py --port 9000              # custom port
"""

import argparse
import http.server
import os
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.resolve()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass  # suppress request logs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('vocab', nargs='?', default='vocabulary.json',
                        help='Vocab JSON file relative to this directory')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()

    vocab_path = Path(args.vocab)
    if not (ROOT / vocab_path).exists():
        print(f"Error: {ROOT / vocab_path} not found")
        return

    server = http.server.HTTPServer(('', args.port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f'http://localhost:{args.port}/flashcards.html?vocab={vocab_path}'
    print(f'Serving:  http://localhost:{args.port}')
    print(f'Vocab:    {vocab_path}')
    print(f'Opening:  {url}')
    print('Press Ctrl+C to stop.\n')
    webbrowser.open(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Stopped.')
        server.shutdown()


if __name__ == '__main__':
    main()
