# Build Instructions for Technical Documentation

## Files

- documentation.tex
- Makefile

## Manual Build Command

Run from project root:

pdflatex documentation.tex

Recommended for stable references and table of contents:

pdflatex documentation.tex
pdflatex documentation.tex

## Using Makefile

Build PDF:

make

Clean temporary LaTeX artifacts:

make clean

Rebuild from scratch:

make rebuild

## Output

The generated file is:

- documentation.pdf
