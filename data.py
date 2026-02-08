"""
Load and expose the pre-extracted CSEW drug prevalence data.
"""

import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "csew_data.json")

with open(_DATA_PATH) as _f:
    _CSEW = json.load(_f)

BASELINE = _CSEW["baseline"]
DRUG_CLASSES = _CSEW["drug_classes"]
QUESTIONS = _CSEW["questions"]
DRUGS = list(BASELINE.keys())
