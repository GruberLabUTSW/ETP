#!/usr/bin/env python3 

import argparse
import re
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from PIL import Image
import yaml

def load_params(p: Path) -> dict:
    with open(p, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def _norm_from_array(arr: np.ndarray) -> Tuple[np.ndarray, float]:
    # your normalized-with-NaN-for-zeros version is fine to keep, or the original
    if arr.dtype == np.uint8:
        maxv = 255.0
    elif arr.dtype == np.uint16:
        maxv = 65535.0
    else:
        vmax = float(arr.max())
        maxv = vmax if vmax > 0 else 1.0
    norm = arr.astype(np.float32) / maxv
    # optional: exclude exact-black background
    # norm[norm == 0] = np.nan
    return norm, maxv

def _load_red(path: Path) -> np.ndarray:
    im = Image.open(path)
    mode = im.mode  # e.g., 'RGB', 'P', 'L', 'I;16'
    if mode == "RGB":
        arr = np.array(im, dtype=np.float32)
        plane = arr[..., 0]  # R channel only
    elif mode == "P":
        # palette-indexed: convert to real grayscale (8-bit)
        plane = np.array(im.convert("L"), dtype=np.float32)
    else:
        # L (8-bit), I;16 (16-bit), etc. → use as-is
        plane = np.array(im, dtype=np.float32)
    red_norm, _ = _norm_from_array(plane)
    return red_norm

def _load_blue(path: Path) -> np.ndarray:
    im = Image.open(path)
    mode = im.mode
    if mode == "RGB":
        arr = np.array(im, dtype=np.float32)
        plane = arr[..., 2]  # B channel only
    elif mode == "P":
        plane = np.array(im.convert("L"), dtype=np.float32)
    else:
        plane = np.array(im, dtype=np.float32)
    blue_norm, _ = _norm_from_array(plane)
    return blue_norm

def _score_intensity(mean_red_norm: float, thr: dict) -> int:
    if mean_red_norm < thr["none"]:
        return 0
    elif mean_red_norm < thr["weak"]:
        return 1
    elif mean_red_norm < thr["moder"]:
        return 2
    return 3


def _score_distribution(pos_frac: float, bins: Tuple[float, float, float]) -> int:
    a, b, c = bins
    if pos_frac < a:
        return 0
    elif pos_frac < b:
        return 1
    elif pos_frac < c:
        return 2
    return 3

def _intensity_text(i: int) -> str:
    return {0: "no staining", 1: "weak staining", 2: "moderate staining", 3: "strong staining"}[i]


def _distribution_text(d: int) -> str:
    return {
        0: "no positive area",
        1: "focal staining (<10% of tissue)",
        2: "regional staining (10–50% of tissue)",
        3: "diffuse staining (>50% of tissue)",
    }[d]


def _tissue_type(case_id: str) -> str:
    row = int(case_id[1:])
    return "TNBC" if row <= 4 else "Benign"


def _detect_modality(name: str, aliases: dict) -> Optional[str]:
    low = name.lower()
    for mode, alias_list in aliases.items():
        for a in alias_list:
            if re.search(rf"\b{re.escape(a)}\b", low):
                return mode
    # special-case: many labs save merges as "... dapi.tif"
    if re.search(r"\bdapi\b", low):
        return "composite"
    return None


def _collect_files(folder: Path, case_regex: re.Pattern, aliases: dict, ex_cases: set) -> Dict[str, Dict[str, Path]]:
    """Return mapping: case_id -> {'red': Path, 'blue': Path, 'composite': Path (optional)}"""
    cases: Dict[str, Dict[str, Path]] = {}
    for p in folder.glob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".tif", ".tiff", ".png", ".jpg", ".jpeg"}:
            continue
        m = case_regex.search(p.stem)
        if not m:
            continue
        case_id = m.group(1).upper()
        if case_id in ex_cases:
            continue
        mode = _detect_modality(p.stem, aliases)
        if mode is None:
            continue
        cases.setdefault(case_id, {})
        cases[case_id][mode] = p
    return cases

    
def score_case(case_id: str,
               paths: Dict[str, Path],
               intensity_thr: dict,
               red_pos_thr: float,
               dist_bins: Tuple[float, float, float],
               blue_min_mean: float,
               red_min_pos: float) -> Dict:
    red_p = paths.get("red")
    if red_p is None:
        return {"Case": case_id, "Tissue Type": _tissue_type(case_id), "Error": "Missing red channel"}
    # Load channels (zeros already converted to NaN inside _norm_from_array)
    red_norm = _load_red(red_p)
    blue_norm = _load_blue(paths["blue"]) if "blue" in paths else None
    # Mask of valid (non-NaN) pixels in red
    valid = ~np.isnan(red_norm) & (red_norm > 0.005)
    if np.any(valid):
        # mean of red over tissue-only pixels
        mean_red = float(np.nanmean(red_norm))
        # fraction of tissue-only pixels that exceed the red threshold
        pos_frac = float(np.mean(red_norm[valid] > red_pos_thr)) if np.any(valid) else float("nan")
    else:
        mean_red = float("nan")
        pos_frac = float("nan")
    # Blue mean, ignoring NaNs (if blue present)
    if blue_norm is not None:
        mean_blue = float(np.nanmean(blue_norm)) if np.any(~np.isnan(blue_norm)) else float("nan")
    else:
        mean_blue = np.nan
    if np.any(valid):
    #  Mask to get 95% "hot" spots
        USE_P95_FOR_INTENSITY = True  # set False to use mean
        if USE_P95_FOR_INTENSITY:
            intensity_measure = float(np.nanpercentile(red_norm[valid], 95))
        else:
            intensity_measure = float(np.nanmean(red_norm[valid]))
    # --- Distribution as fraction positive within tissue ---
        pos_frac = float(np.mean(red_norm[valid] > red_pos_thr))
    else:
        intensity_measure = float("nan")
        pos_frac = float("nan")
    # Scores
    intensity = _score_intensity(intensity_measure, intensity_thr)
    distribution = _score_distribution(pos_frac, dist_bins)
    composite = intensity * distribution  # 0–9
    # Heuristic note
    note = ""
    if blue_norm is not None:
        if (mean_blue < blue_min_mean) and (pos_frac < red_min_pos):
            note = "Low DAPI + low red; likely no tissue / edge."
    return {
    "Case": case_id,
    "Tissue Type": _tissue_type(case_id),
    "Mean Red (norm)": (None if np.isnan(mean_red) else round(mean_red, 4)),
    "ETP+ Fraction": (None if np.isnan(pos_frac) else round(pos_frac, 4)),
    "Mean Blue (norm)": (None if np.isnan(mean_blue) else round(mean_blue, 4)),
    "Intensity Measure (p95)": round(intensity_measure, 4),
    "Intensity (0–3)": intensity,
    "Distribution (0–3)": distribution,
    "Composite (0–9)": composite,
    "Notes": note,
    "Has Composite Image": bool(paths.get("composite"))
}

def main():
    ap = argparse.ArgumentParser(description="Per-core scorer for ETP (red) + DAPI (blue)")
    ap.add_argument("--input", "-i", type=Path, required=True, help="Folder with per-core TIFFs")
    ap.add_argument("--params", "-p", type=Path, default=Path("params_etp.yaml"), help="YAML parameter file")
    ap.add_argument("--out-xlsx", type=Path, default=Path("PerCore_ETP_scoring_PRODUCT.xlsx"))    
    ap.add_argument("--exclude", type=Path, default=Path("exclude_cases.txt"),
                    help="Optional text file with case IDs to exclude (one per line)")
    args = ap.parse_args()
    params = load_params(args.params)
    case_regex = re.compile(params["case_regex"], re.IGNORECASE)
    aliases = params["modality_aliases"]
    intensity_thr = params["intensity_thresholds"]
    red_pos_thr = float(params["red_positive_fraction_threshold"])
    dist_bins = tuple(params["distribution_bins"])
    blue_min_mean = float(params["blue_mean_tissue_min"])
    red_min_pos = float(params["red_positive_fraction_min"])
    # exclusions
    excluded = set(params.get("exclude_cases", []))
    if args.exclude.exists():
        extra = {ln.strip().upper() for ln in args.exclude.read_text().splitlines() if ln.strip()}
        excluded |= extra
    cases = _collect_files(args.input, case_regex, aliases, excluded)
    if not cases:
        raise SystemExit(f"No cases found in {args.input}. Check naming (e.g., 'A1 red.tif', 'A1 blue.tif').")
    rows = []
    for case_id, paths in sorted(cases.items(), key=lambda kv: (int(kv[0][1:]), kv[0][0])):
        rows.append(
            score_case(case_id, paths, intensity_thr, red_pos_thr, dist_bins, blue_min_mean, red_min_pos)
        )
    df = pd.DataFrame(rows)
    keep_cols = [
        "Case","Intensity (0–3)","Distribution (0–3)","Composite (0–9)"
    ]
    for c in keep_cols:
        if c not in df.columns:
            df[c] = ""
    df[keep_cols].to_excel(args.out_xlsx, index=False)
    # descriptions
    lines = []
    for _, r in df.iterrows():
        case = r["Case"]
        err = r.get("Error", "")
        if err:
            lines.append(f"Case {case} ({r['Tissue Type']})\n* Error: {err}\n")
            continue
        i = int(r["Intensity (0–3)"])
        d = int(r["Distribution (0–3)"])
        comp = int(r["Composite (0–9)"])
        obs = f"Tissue core with {_intensity_text(i)}, showing {_distribution_text(d)}."
        lines.append(
            f"Case {case} ({r['Tissue Type']})\n"
            f"* Observation: {obs}\n"
            f"* Intensity: {i}.\n"
            f"* Distribution: {d}.\n"
            f"* Composite Score: {comp}.\n"
        )
    print(f"[OK] Excel   → {args.out_xlsx.resolve()}")
    print(f"[OK] Scored  → {len(df)} cases (red required; blue optional).")
if __name__ == "__main__":
    main()
