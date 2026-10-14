import io, os, pickle, zipfile, glob
R = r"C:\Users\Dell\AppData\Local\Temp\opencode\qtrust\q-trust"
CKPT = os.path.join(R, "planner", "model_gpu_v3.pt")

class Stub:
    def __init__(self, *a, **k): pass
    def __call__(self, *a, **k): return None

class U(pickle.Unpickler):
    def find_class(self, module, name):
        if module.startswith("torch"):
            return type(name, (Stub,), {})
        return super().find_class(module, name)
    def persistent_load(self, pid):
        # (storage_type, key, location, numel) -> return an object carrying numel
        try:
            n = pid[-1]
        except Exception:
            n = 0
        class S:
            def __init__(self, n): self.n = n
        return S(n)

z = zipfile.ZipFile(CKPT)
meta = None
for e in z.namelist():
    if e.endswith("data.pkl"):
        o = U(io.BytesIO(z.read(e))).load()
        if isinstance(o, dict):
            meta = o; break

print("=== model_gpu_v3.pt TOP-LEVEL METADATA ===")
sd = None
for k, v in meta.items():
    if k in ("model_state_dict", "state_dict"):
        sd = v; print("  %-22s -> %d tensors" % (k, len(v)))
    elif isinstance(v, (int, float, str, bool, type(None))):
        print("  %-22s = %r" % (k, v))
    elif isinstance(v, dict):
        print("  %-22s = %r" % (k, v))
    else:
        print("  %-22s -> %s" % (k, type(v).__name__))

print()
print(">>> n_real_graphs     =", repr(meta.get("n_real_graphs")))
print(">>> epochs            =", repr(meta.get("epochs")))
print(">>> n_graphs          =", repr(meta.get("n_graphs")))
print(">>> norm              =", repr(meta.get("norm")))
print(">>> model_config      =", repr(meta.get("model_config")))

print()
print("=== conv2 (GATv2) tensor shapes ===")
tot = 0
for k, t in (sd or {}).items():
    n = getattr(t, "n", None)
    if k.startswith("conv2"):
        print("  %-36s numel=%s" % (k, n))
    if n: tot += n
print()
print("state-dict total elements (sum of persistent numel):", tot)
CB = os.path.join(R, "planner", "data", "real_cboms")
cur = sorted(os.path.basename(p) for p in glob.glob(os.path.join(CB, "*.json")))
print("CBOMs on disk now:", len(cur))
