import re

p = r"C:\Users\Dell\AppData\Local\Temp\opencode\qtrust\paper\main.tex"
s = open(p, encoding="utf-8").read()
lines = [re.sub(r"(?<!\\)%.*$", "", l) for l in s.split("\n")]
body = "\n".join(lines)

# ---- environment balance -------------------------------------------------
stack, errs = [], []
for m in re.finditer(r"\\(begin|end)\{([\w*]+)\}", body):
    kind, env = m.group(1), m.group(2)
    ln = body[:m.start()].count("\n") + 1
    if kind == "begin":
        stack.append((env, ln))
    else:
        if not stack:
            errs.append("extra \\end{%s} at line %d" % (env, ln))
        else:
            e, l = stack.pop()
            if e != env:
                errs.append("mismatch: \\begin{%s} (line %d) closed by \\end{%s} (line %d)"
                            % (e, l, env, ln))
for e, ln in stack:
    errs.append("unclosed \\begin{%s} at line %d" % (e, ln))
print("ENVIRONMENT ERRORS:", errs if errs else "none")

# ---- math mode -----------------------------------------------------------
nd = len(re.findall(r"(?<!\\)\$", body))
print("unescaped $ : %d  even=%s" % (nd, nd % 2 == 0))

# ---- labels / refs -------------------------------------------------------
labels = set(re.findall(r"\\label\{([^}]*)\}", body))
refs = set(re.findall(r"\\(?:eq)?ref\{([^}]*)\}", body))
print("labels defined (%d): %s" % (len(labels), sorted(labels)))
print("refs used     (%d): %s" % (len(refs), sorted(refs)))
print("DANGLING REFS :", sorted(refs - labels) if refs - labels else "none")
print("unused labels :", sorted(labels - refs) if labels - refs else "none")

# ---- citations -----------------------------------------------------------
keys = set()
for m in re.finditer(r"\\cite\{([^}]*)\}", body):
    for k in m.group(1).split(","):
        keys.add(k.strip())
bibkeys = set(re.findall(r"\\bibitem\{([^}]*)\}", body))
print("cited=%d  bibitems=%d" % (len(keys), len(bibkeys)))
print("MISSING BIBITEM:", sorted(keys - bibkeys) if keys - bibkeys else "none")
print("UNCITED BIBITEM:", sorted(bibkeys - keys) if bibkeys - keys else "none")

# ---- figures / tables ----------------------------------------------------
figs = re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]*)\}", body)
import os
base = os.path.dirname(p)
print("figures referenced:", figs)
for f in figs:
    print("   exists:", f, os.path.exists(os.path.join(base, f)))

caps = re.findall(r"\\caption\{", body)
print("captions=%d (expect >= #tables + #figures)" % len(caps))
tabs = len(re.findall(r"\\begin\{table\*?\}", body))
print("tables=%d  figure*=1  total floats=%d" % (tabs, tabs + 1))

# ---- numbers hygiene: flag anything suspicious ---------------------------
print("\napprox word count:", len(re.findall(r"[A-Za-z][A-Za-z'-]+", body)))
print("section count:", len(re.findall(r"\\section\{", body)),
      " subsection:", len(re.findall(r"\\subsection\{", body)))