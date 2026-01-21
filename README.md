# Sonogenetics Paper Dataset & Labeling

This project aims to build a high-quality labeled dataset for **Sonogenetics** and **Acoustic Genetic Reporters (ARG)**. We utilize the Gemini API as a "Teacher" model to extract structured experimental protocols from scientific literature found in the PMC Open Access dataset.

## 🧬 Project Overview

Sonogenetics is an emerging field that uses ultrasound to non-invasively control cellular activity, typically through ultrasound-sensitive ion channels (e.g., Piezo1, MscL, TRP channels) or acoustic reporter genes (ARGs) that allow for ultrasound imaging of cellular processes deep within living tissue.

## 🛠️ Key Components

- **`scripts/filter_candidates.py`**: A parallelized scanner that filters the PMCOA dataset for papers containing relevant keywords.
- **`scripts/teacher_label.py`**: An asynchronous script that uses Gemini 1.5 Flash to label papers according to a strict JSON schema.
- **`schema/protocol_extractor_v1.schema.json`**: The canonical JSON schema specifying the experimental parameters to be extracted (e.g., ultrasound frequency, pressure, cell types, reporter molecules).
- **`data/`**:
  - `candidates/`: Filtered paper candidates.
  - `labeled/`: Successfully labeled samples (`gold.jsonl`) and failure logs (`bad.jsonl`).

## 🚀 Getting Started

1. **Setup Environment**:

   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY
   ```

2. **Filter Candidates**:

   ```bash
   uv run scripts/filter_candidates.py
   ```

3. **Run Labeling**:

   ```bash
   uv run scripts/teacher_label.py
   ```

## 📊 Dataset Goals

The goal is to collect **500-1000 high-quality training examples** to fine-tune a specialized local model (using MLX) for automated protocol extraction in the sonogenetics domain.
