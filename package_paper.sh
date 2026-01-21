#!/bin/bash

# Configuration
PANDOC="/opt/homebrew/bin/pandoc"
XELATEX="/Library/TeX/texbin/xelatex"
MD_FILE="paper_arxiv.md"
PDF_OUT="paper.pdf"
TEX_OUT="paper.tex"
IMAGE_DIR="paperimages"
BUNDLE_NAME="submission.tar.gz"

echo "🚀 Starting arXiv packaging process..."

# 1. Generate PDF
echo "📄 Generating PDF..."
$PANDOC "$MD_FILE" -o "$PDF_OUT" --pdf-engine="$XELATEX"
if [ $? -eq 0 ]; then
    echo "✅ PDF generated: $PDF_OUT"
else
    echo "❌ Error generating PDF"
    exit 1
fi

# 2. Generate LaTeX source
echo "⚛️ Generating LaTeX source..."
$PANDOC "$MD_FILE" -o "$TEX_OUT" --standalone
if [ $? -eq 0 ]; then
    echo "✅ LaTeX generated: $TEX_OUT"
else
    echo "❌ Error generating LaTeX"
    exit 1
fi

# 3. Create ArXiv submission bundle
echo "📦 Packaging submission bundle..."
# Create a temporary list of files to include
# ArXiv expects the main .tex file and the images directory
tar -cvzf "$BUNDLE_NAME" "$TEX_OUT" "$IMAGE_DIR"
if [ $? -eq 0 ]; then
    echo "✅ Submission bundle created: $BUNDLE_NAME"
else
    echo "❌ Error creating bundle"
    exit 1
fi

echo "✨ Done! Ready for submission to arXiv."
echo "Files prepared:"
echo " - $PDF_OUT (for your review)"
echo " - $BUNDLE_NAME (upload this to arXiv)"
