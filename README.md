## ETP
Analysis of endotrophin immunofluorescence staining in human tissues

Python 3 script created by Bethania Santos and Lavanya Vumma in the Gruber Lab at UT Southwestern
October 13, 2025

Supporting code for the submitted manuscript:
Endotrophin is a circulating fibroinflammatory biomarker associated with treatment response in human metastatic ER+ breast cancer

Bethania Santos1, Lavanya Vumma1, Dawei Bu2, Megan Virostek2, Ethan Johnson3, Cheryl Lewis3, Sunati Sahoo3, Yan Peng3, Ningyan Zhang4, Zhiqiang An4, Heather McArthur1, Philipp E. Scherer2,3, Joshua J. Gruber1,3,5,6

1.	Hematology-Oncology, Internal Medicine, UT Southwestern Medical Center, Dallas, TX. 
2.	Touchstone Diabetes Center, UT Southwestern Medical Center, Dallas, TX. 
3.	Harold C. Simmons Comprehensive Cancer Center & Pathology Department, UT Southwestern Medical Center, Dallas, TX.
4.	Texas Therapeutics Institute, Brown Foundation Institute of Molecular Medicine, University of  Texas Health Science Center at Houston, Houston, Texas.	
5.	Cecil H. and Ida Green Center for Reproductive Biosciences, UT Southwestern Medical Center, Dallas, TX.
6.	Molecular Biology, UT Southwestern Medical Center, Dallas, TX
Corresponding Author: Joshua Gruber,MD, PhD, Division of Hematology and Oncology, Internal Medicine, UT Southwestern Medical Center, 6000 Harry Hines Blvd., Dallas, TX. 75390 joshua.gruber@utsouthwestern.edu, 214-645-5477

Manuscript Abstract
Soluble factors emanating from fibroinflammatory processes are emerging as cancer biomarkers and therapeutic targets. Endotrophin (ETP), a collagen VI proteolytic fragment, is elevated in human breast cancer patients and drives tumor progression in rodent breast cancer models, an effect which neutralizing antibodies can effectively abrogate. This implies that tracking or targeting elevated ETP levels could inform breast cancer therapeutic strategies. However, we lack precise knowledge about the impact of ETP in specific breast cancer subtypes and whether circulating levels provide predictive or prognostic information. To address these gaps, we prospectively assessed circulating ETP levels among breast cancer patients undergoing various treatment modalities. We observed higher ETP levels in estrogen receptor-positive (ER+, HER2-) tumors compared to triple-negative tumors in both early-stage and metastatic settings. However, circulating ETP levels were associated with treatment response only in the metastatic setting. ETP was readily detected in tumor specimens and adjacent benign sections from various breast tumor types, suggesting that both autocrine and paracrine ETP production may be important drivers of tumor growth. In summary, this work establishes circulating ETP levels as a potentially important biomarker in ER+ metastatic breast cancer and could inform the development of endotrophin-targeting agents.  

Overview.

Python 3 code that accepts RGB or grayscale TIFF files in 8-bit or 16-bit format.
Requies an input file to set user-defined pixel thresholds and thresholds to classify outputs.
Intensity is separated into 3 scores: low [1], moderate [2], high [3].
Distribution is separated into 3 scores: low [1], moderate [2], high [3].
composite score is defined as intensity x distribution.
Minimum composite score is 1.
Maximum composite score is 9.

Scoring proceeds through 4 steps:

1. Normalization of all pixels to scale 0 to 1, based on highest pixel reading (eg. 255 for 8 bit).
2. Intensity values calculated by setting all 0 value pixels to NA, taking the 95th percentile value (focus on brightest areas), and scoring between 1-3 based on user-defined values.
3. Distribution values calculated using mean normalized pixel value that is greater than user-defined threshold value and scored between 1-3 based on user-defined values.
4. Computation of composite score by [intensity score] x [distribution score] = [composite score].


Usage Instructions

Per-core TIFF scorer for Endotrophin (ETP, red) + DAPI (blue).

Inputs:  A folder with per-core TIFFs. Filenames are case-insensitive and may contain spaces.
         Case IDs are parsed as grid positions e.g., A1, B6, N8 (A–N, 1–8).
         Example files:
           A1 red.tif
           A1 blue.tif
           A1 composite.tif        # optional; aliases: comp/merge/merged/dapi
           B6 red.tif
           B6 blue.tif
           ...

Outputs:
  - Excel: per-core Intensity (0–3), Distribution (0–3), Composite (product 0–9)

All scoring rules (thresholds, aliases, exclusions) are set via YAML (see params_etp.yaml).

Case IDs: A–N followed by 1–8, at the start of the filename
case_regex: "^([A-N][1-8])\\b"

How to recognize modalities from filenames (case-insensitive, word-boundary matches)
modality_aliases:
  red:       ["red", "etp"]
  blue:      ["blue", "dapi", "nuc", "nuclei"]
  composite: ["composite", "merge", "merged", "comp"]

Intensity thresholds (based on mean red / max) set in params file
intensity_thresholds:
  none:  0.04   # < 0.04 → 0
  weak:  0.16   # 0.04–<0.16 → 1
  moder: 0.40   # 0.16–<0.40 → 2
  strong: ≥0.40 → 3

A pixel is ETP+ if red_norm > threshold, set in params file
red_positive_fraction_threshold: 0.06

Distribution bin edges (fractions of tissue area), set in params file
  none: < 0.05 → 0; 
  weak: [0.05, 0.25) → 1; 
  moderate: [0.25, 0.50) → 2; 
  strong: ≥ 0.50 → 3
distribution_bins: [0.05, 0.25, 0.50]

Heuristic flag for likely empty cores (does not change score; adds a note), set in params
blue_mean_tissue_min: 0.02
red_positive_fraction_min: 0.01

Hard excludes (optional); will be merged with exclude_cases.txt if present, set in params
exclude_cases: []

3)	exclude_cases.txt 

One case ID per line (A–N + 1–8). Lines starting with # are ignored.
Example:
C1
H1
J1
A2
K2
D3
H4
J5
B7
N7

4)	requirements / dependencies

numpy>=1.23
pandas>=1.5
Pillow>=9.2
PyYAML>=6.0

5)	Tutorial

Per-core scoring of endotrophin (ETP) immunofluorescence

Inputs.

A folder of per-core images saved as TIFF/PNG/JPEG. Files must start with a grid case ID (e.g., `A1`, `B6`, `N8`). Red (ETP) and Blue (DAPI) images may be single-channel or RGB; if RGB, the red/blue planes are used automatically. A composite image is optional.

Output files.

- `PerCore_ETP_scoring_PRODUCT.xlsx` — Case, Intensity (0–3), Distribution (0–3), Composite (product 0–9).

How to run

```bash
# 1) run on a folder of TIFFs (python = 3.8)
python 2025_10_10_scorer_etp.py \
  --input ./cores \
  --params params_etp.yaml \
  --out-xlsx PerCore_ETP_scoring_PRODUCT.xlsx \
