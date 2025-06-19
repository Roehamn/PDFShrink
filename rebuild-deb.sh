#!/usr/bin/env bash
set -e

# Auto-bump version: increment patch component of latest tag or start at 0.1.0
if git describe --tags --abbrev=0 &>/dev/null; then
  TAG=$(git describe --tags --abbrev=0)
  BASE=${TAG#v}
  IFS='.' read -r MAJ MIN PATCH <<< "$BASE"
  PATCH=$((PATCH + 1))
  NEWVERSION="$MAJ.$MIN.$PATCH"
else
  NEWVERSION="0.1.0"
fi
# Create annotated tag and push it
echo "Tagging release v$NEWVERSION"
git tag -a "v$NEWVERSION" -m "Release $NEWVERSION"
git push origin --tags
VERSION="$NEWVERSION"
echo "Building PDFShrink version $VERSION"

# Clean previous builds
echo "-- Cleaning old build artifacts"
rm -rf build/ dist/ PDFShrink.spec pkg

# Build the standalone binary
echo "-- Running PyInstaller"
pipx run pyinstaller --noconsole --onefile --name PDFShrink main.py

# Stage binary for Debian package
echo "-- Staging binary"
mkdir -p pkg/usr/local/bin
cp dist/PDFShrink pkg/usr/local/bin/PDFShrink

# Build the .deb with fpm
echo "-- Creating .deb package"
fpm -s dir -t deb \
    -n pdfshrink \
    -v "$VERSION" \
    --license MIT \
    --maintainer "roeham" \
    --description "PDFShrink — OCRmyPDF-based PDF compressor" \
    --url "https://github.com/Roehamn/PDFShrink" \
    pkg=/

# Output result
echo "\nDone! Your Debian package is: pdfshrink_${VERSION}_amd64.deb"
