PDF=documentation.pdf
TEX=documentation.tex

all: $(PDF)

$(PDF): $(TEX)
	pdflatex -interaction=nonstopmode -halt-on-error $(TEX)
	pdflatex -interaction=nonstopmode -halt-on-error $(TEX)

clean:
	-del /q documentation.aux documentation.log documentation.out documentation.toc 2>nul
	-rm -f documentation.aux documentation.log documentation.out documentation.toc

rebuild: clean all

.PHONY: all clean rebuild
