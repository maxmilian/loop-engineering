"""
folder_watcher.py — watches an inbox folder and auto-files documents.
Every 30s: find new files, ask the LLM what each is, move it to the right folder.
Runs as a long-lived daemon on the file server.
"""
import os
import time
import shutil
from llm import ask_model

INBOX = "/srv/inbox"
SORTED = "/srv/sorted"
INTERVAL = 30


def classify_and_file(path):
    with open(path) as f:
        content = f.read()
    category = ask_model(
        f"What category does this document belong to? Reply with one word.\n\n{content}"
    ).strip()
    dest = os.path.join(SORTED, category)
    os.makedirs(dest, exist_ok=True)
    shutil.move(path, os.path.join(dest, os.path.basename(path)))


def main():
    while True:
        for name in os.listdir(INBOX):
            path = os.path.join(INBOX, name)
            if os.path.isfile(path):
                classify_and_file(path)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
