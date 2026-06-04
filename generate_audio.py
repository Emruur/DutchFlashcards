#!/usr/bin/env python3
"""
Generate Dutch pronunciation audio files for a vocabulary JSON.

Usage:
    python3 generate_audio.py vocab/lesson1.json
    python3 generate_audio.py vocab/lesson2.json --voice Xander
    python3 generate_audio.py vocab/lesson1.json --field dutch --voice Ellen
    python3 generate_audio.py vocab/lesson1.json --overwrite

Structure:
    vocab/lesson1.json  →  audio/lesson1/001.m4a …
    vocab/lesson2.json  →  audio/lesson2/201.m4a …

Expected JSON format:
    {
      "sections": [
        {
          "words": [
            { "id": 1, "dutch": "de hond", "english": "the dog" },
            ...
          ]
        }
      ]
    }

Output:
    - Audio files saved to audio/<lesson>/ relative to project root
    - JSON updated in-place with "audio" field on each word
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def generate(json_path: Path, field: str, voice: str, overwrite: bool):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    # lesson name derived from filename: vocab/lesson1.json -> lesson1
    lesson = json_path.stem
    # project root is parent of vocab/
    project_root = json_path.parent.parent
    audio_dir = project_root / 'audio' / lesson
    audio_dir.mkdir(parents=True, exist_ok=True)

    words = [w for s in data.get('sections', []) for w in s.get('words', [])]

    if not words:
        print('No words found. Make sure your JSON has sections[].words[].')
        sys.exit(1)

    generated = skipped = 0

    for word in words:
        wid  = word.get('id')
        text = word.get(field)

        if wid is None or not text:
            print(f'  skip (missing id or field "{field}"): {word}')
            continue

        aiff = audio_dir / f'{wid:03d}.aiff'
        out  = audio_dir / f'{wid:03d}.m4a'

        if out.exists() and not overwrite:
            word['audio'] = f'audio/{lesson}/{out.name}'
            skipped += 1
            continue

        subprocess.run(['say', '-v', voice, '-o', str(aiff), text], check=True)
        subprocess.run(['afconvert', str(aiff), str(out), '-f', 'm4af', '-d', 'aac'], check=True)
        aiff.unlink()
        word['audio'] = f'audio/{lesson}/{out.name}'
        print(f'  [{wid:03d}] {text}')
        generated += 1

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'\n{generated} generated, {skipped} already existed.')
    print(f'Audio saved to: {audio_dir}')
    print(f'JSON updated:   {json_path}')


def main():
    parser = argparse.ArgumentParser(
        description='Generate TTS audio for a Dutch vocabulary JSON file.'
    )
    parser.add_argument('json_file', help='Path to vocab JSON (e.g. vocab/lesson1.json)')
    parser.add_argument(
        '--voice', default='Xander',
        help='macOS voice to use (default: Xander, nl_NL). Use Ellen for Belgian Dutch.'
    )
    parser.add_argument(
        '--field', default='dutch',
        help='JSON field to read text from (default: dutch)'
    )
    parser.add_argument(
        '--overwrite', action='store_true',
        help='Re-generate audio even if the file already exists'
    )
    parser.add_argument(
        '--list-voices', action='store_true',
        help='Print available voices and exit'
    )
    args = parser.parse_args()

    if args.list_voices:
        result = subprocess.run('say -v "?" 2>&1', shell=True, capture_output=True, text=True)
        print(result.stdout or result.stderr)
        return

    json_path = Path(args.json_file).resolve()
    if not json_path.exists():
        print(f'Error: {json_path} not found')
        sys.exit(1)

    print(f'Voice:  {args.voice}')
    print(f'Field:  {args.field}')
    print(f'Source: {json_path}\n')

    generate(json_path, field=args.field, voice=args.voice, overwrite=args.overwrite)


if __name__ == '__main__':
    main()
