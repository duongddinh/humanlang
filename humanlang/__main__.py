# humanlang/__main__.py
import asyncio
import sys
from .core.interpreter import HumanLang

async def _main_async():
    if len(sys.argv) < 2:
        print("Usage: humanlang <yourfile.human>")
        sys.exit(1)

    filepath = sys.argv[1]
    interpreter = HumanLang()
    await interpreter.run_from_file(filepath)

def main():              
    try:
        asyncio.run(_main_async())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
