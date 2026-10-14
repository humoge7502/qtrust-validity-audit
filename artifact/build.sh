#!/usr/bin/env bash
# build.sh -- one command to reproduce every claim in the manuscript.
#
#   bash build.sh /path/to/q-trust
#
# Requires: Python 3.10+ (3.12 for the clean warm-start re-run),
# numpy, scipy, matplotlib, scikit-learn; torch + torch_geometric for P2.
set -euo pipefail

REPO="${1:-../q-trust}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python}"

echo "=============================================================="
echo " Q-Trust audit -- full reproduction"
echo " repo: $(cd "$REPO" && pwd)"
echo "=============================================================="

echo
echo "[1/7] headline-claim verification (stdlib only)"
"$PY" "$HERE/scripts/verify_qtrust_claims.py" "$REPO"

echo
echo "[2/7] checkpoint-metadata leakage check (stdlib only)"
"$PY" "$HERE/scripts/verify_ckpt_leak.py"

echo
echo "[3/7] six re-audit experiments (numpy + scipy)"
"$PY" "$HERE/scripts/experiments_reaudit.py" "$REPO"

echo
echo "[4/7] repository-agnostic 8-mode checker (stdlib only)"
"$PY" "$HERE/scripts/validate_eval.py" --repo "$REPO" \
      --json "$HERE/results/validate_eval_qtrust.json"

echo
echo "[5/7] second-system fair baseline (needs scikit-learn + the second repo)"
if [ -n "${SYSTEM2:-}" ] && [ -d "${SYSTEM2:-}" ]; then
  "$PY" "$HERE/scripts/fair_baseline_system2.py" "$SYSTEM2" 600
else
  echo "  SKIPPED -- set SYSTEM2=/path/to/pqc-migration-prioritization-ml-qubo"
fi

echo
echo "[6/7] clean warm-start 42-fold LOO (needs torch + torch_geometric)"
if "$PY" -c "import torch, torch_geometric" 2>/dev/null; then
  CUBLAS_WORKSPACE_CONFIG=:4096:8 QW_DEVICE=cpu PYTHONIOENCODING=utf-8 \
    "$PY" "$HERE/scripts/clean_warmstart_loo.py" "$REPO" \
           "$HERE/results/clean_warmstart_loo.json" 2>&1 \
    | grep -v -E "^(Epoch|  -> Saved|Generating|Generation took)"
else
  echo "  SKIPPED -- torch/torch_geometric not installed"
fi

echo
echo "[7/7] figure + manuscript checks"
"$PY" "$HERE/scripts/make_figure1.py" "$REPO" "$HERE/paper"
"$PY" "$HERE/scripts/check_tex.py"

echo
echo "=============================================================="
echo " DONE. Expected checkpoints:"
echo "   [1] 14 headline claims reproduced, 0 mismatched"
echo "   [2] n_real_graphs = 40"
echo "   [3] X1 42/42 folds bit-exact; X2 identical on 42/42"
echo "   [4] >= 6 of 8 modes PRESENT"
echo "   [6] clean base records n_real_graphs = 0"
echo "=============================================================="