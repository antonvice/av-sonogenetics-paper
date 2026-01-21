from datasets import load_dataset

def main():
    # Load streaming to just get the first example quickly
    ds = load_dataset("gabrielaltay/pmcoa", split="train", streaming=True)
    print("Keys available:", next(iter(ds)).keys())

if __name__ == "__main__":
    main()
