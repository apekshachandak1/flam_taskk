from datasets import load_dataset
import json
import os

os.makedirs("data/raw", exist_ok=True)

# -------- Hindi --------
print("Downloading Hindi...")
hi = load_dataset(
    "allenai/c4",
    "hi",
    split="train",
    streaming=True
)

with open("data/raw/hindi.jsonl","w",encoding="utf-8") as f:
    for i,row in enumerate(hi):
        if i>=9000:
            break
        json.dump(
            {
                "text":row["text"],
                "source":"mc4_hi"
            },
            f,
            ensure_ascii=False
        )
        f.write("\n")

print("Hindi Done")

# -------- Hinglish --------

print("Downloading Hinglish...")

hinglish = load_dataset(
    "allenai/c4",
    "hi-Latn",
    split="train",
    streaming=True
)

with open("data/raw/hinglish.jsonl","w",encoding="utf-8") as f:
    for i,row in enumerate(hinglish):
        if i>=1000:
            break
        json.dump(
            {
                "text":row["text"],
                "source":"mc4_hi_latn"
            },
            f,
            ensure_ascii=False
        )
        f.write("\n")

print("Hinglish Done")
print("Completed!")