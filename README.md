# ETP
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

Code description
Python 3 code that accepts RGB or grayscale TIFF files in 8-bit or 16-bit format
Requies an input file to set user-defined pixel thresholds and thresholds to classify outputs
Intensity is separated into 3 scores: low [1], moderate [2], high [3]
Distribution is separated into 3 scores: low [1], moderate [2], high [3]
composite score is defined as intensity x distribution
minimum composite score is 1
maximum composite score is 9

Scoring proceeds through 4 steps:
1. Normalization of all pixels to scale 0 to 1, based on highest pixel reading (eg. 255 for 8 bit)
2. Intensity scoring by setting all 0 value pixels to NA and then taking mean of all remaining pixels that have >= 95% intensity (focus on brightest areas)
3. Distribution scoring of mean normalized pixel value that is greater than user-defined threshold value
4. Computation of composite score by [intensity score] x [distribution score] = [composite score]
