"""Find which PDF page(s) of a pdftotext -layout export contain a regex. Usage: pgfind.py <txt> <regex>"""
import sys, re
txt = open(sys.argv[1], encoding='utf-8', errors='replace').read()
pat = re.compile(sys.argv[2], re.I)
for n, page in enumerate(txt.split('\f'), 1):
    for line in page.splitlines():
        if pat.search(line):
            print(f'p{n}: {" ".join(line.split())[:160]}')
