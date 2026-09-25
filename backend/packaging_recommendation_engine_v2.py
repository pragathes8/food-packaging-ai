
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd

CLASS_RANK = {
    "Compatible": 3,
    "Conditionally_Compatible": 2,
    "Low_Compatibility": 1,
    "Insufficient_Evidence": 0,
}

def _norm01(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    lo, hi = s.min(skipna=True), s.max(skipna=True)
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.5, index=s.index)
    return (s - lo) / (hi - lo)

def _safe_text(v):
    if pd.isna(v):
        return "Not available"
    return str(v)

class PackagingRecommendationEngineV2:
    """
    Evidence-guided runtime engine for the current SIH26236 artifact set.

    Decision hierarchy:
      1) Deterministic evidence/candidate status remains the backbone.
      2) Insufficient_Evidence is never promoted to a recommendation.
      3) ML full-fit prediction is an enhancement/tie-break signal, not a
         replacement for deterministic evidence.
      4) Runtime optimization uses the existing 80/10/10 structure:
         technical compatibility / operational fit / evidence coverage.
      5) No cost or sustainability proxy is invented.
    """

    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path)
        self.df = pd.read_csv(self.dataset_path, low_memory=False)

        required = {
            "Food_ID", "Food_Name", "Packaging_ID", "Packaging_Material",
            "Evidence_Adjusted_Compatibility_Score",
            "Evidence_Corrected_Compatibility_Class",
            "Evidence_Coverage_Ratio",
            "ML_Predicted_Score", "ML_Predicted_Class",
            "ML_Model_Confidence", "ML_Score_Tree_SD",
            "Material_Category", "Structure_Type", "Sealability",
            "Gas_Permeability", "Mechanical_Strength",
            "MAP_Suitability_x", "OTR_Min_num", "OTR_Max_num",
            "WVTR_Min_num", "WVTR_Max_num",
            "Thickness_Min_num", "Thickness_Max_num",
        }
        missing = sorted(required - set(self.df.columns))
        if missing:
            raise ValueError(f"Dataset missing required columns: {missing}")

        self.foods = (
            self.df[["Food_ID","Food_Name","Food_Category","Food_Subcategory"]]
            .drop_duplicates("Food_ID")
            .sort_values(["Food_Category","Food_Name"])
            .reset_index(drop=True)
        )
        self.packages = (
            self.df[[
                "Packaging_ID","Packaging_Material","Material_Category",
                "Structure_Type","Sealability","Gas_Permeability",
                "Mechanical_Strength","MAP_Suitability_x",
                "OTR_Min_num","OTR_Max_num","WVTR_Min_num","WVTR_Max_num",
                "Thickness_Min_num","Thickness_Max_num"
            ]]
            .drop_duplicates("Packaging_ID")
            .reset_index(drop=True)
        )

        self._prepare_scores()

    def _prepare_scores(self):
        d = self.df.copy()
        d["det_score"] = pd.to_numeric(
            d["Evidence_Adjusted_Compatibility_Score"], errors="coerce"
        )
        d["ml_score"] = pd.to_numeric(d["ML_Predicted_Score"], errors="coerce")
        d["coverage"] = pd.to_numeric(d["Evidence_Coverage_Ratio"], errors="coerce").fillna(0)
        d["ml_conf"] = pd.to_numeric(d["ML_Model_Confidence"], errors="coerce").fillna(0)
        d["ml_sd"] = pd.to_numeric(d["ML_Score_Tree_SD"], errors="coerce").fillna(0)

        # Operational-fit component from the already-derived, source-backed
        # packaging capability scores. This is deliberately not a cost proxy.
        parts = []
        for c, maxv in [
            ("MAP_Suitability_Score_num", 4.0),
            ("Sealability_Score_num", 4.0),
            ("Mechanical_Strength_Score_num", 5.0),
        ]:
            x = pd.to_numeric(d[c], errors="coerce")
            parts.append((x / maxv).clip(0, 1))
        op = pd.concat(parts, axis=1).mean(axis=1, skipna=True).fillna(0.5)

        # Gas permeability is informative but is not directionally scored here:
        # the project explicitly avoids a universal "lower is better" rule.
        d["operational_fit"] = op

        # Runtime optimization: 80% technical evidence score, 10% operational
        # fit, 10% evidence coverage. ML remains a separate enhancement/tie-break.
        d["technical_norm"] = (d["det_score"] / 83.33).clip(0, 1)
        d["optimization_score"] = (
            0.80 * d["technical_norm"] +
            0.10 * d["operational_fit"] +
            0.10 * d["coverage"]
        ) * 100

        # Stable ML tie-break signal, not a replacement score.
        d["ml_tiebreak"] = d["ml_score"].fillna(d["det_score"]).fillna(-1)

        # Never allow insufficient evidence into final recommendation pool.
        d["eligible"] = d["Evidence_Corrected_Compatibility_Class"].ne(
            "Insufficient_Evidence"
        ) & d["det_score"].notna()

        self.df = d

    def list_foods(self):
        return self.foods.to_dict(orient="records")

    def list_packaging(self):
        return self.packages.to_dict(orient="records")

    def _resolve_food(self, food_name: str):
        q = str(food_name).strip().casefold()
        exact = self.foods[self.foods["Food_Name"].astype(str).str.casefold() == q]
        if len(exact):
            return exact.iloc[0]
        contains = self.foods[
            self.foods["Food_Name"].astype(str).str.casefold().str.contains(q, regex=False)
        ]
        if len(contains):
            return contains.iloc[0]
        raise ValueError(
            f"Food '{food_name}' is not in the current 109-food evidence catalog. "
            "Use list_foods() for the supported catalog."
        )

    def recommend(
        self,
        food_name: str,
        top_n: int = 3,
        storage_type: Optional[str] = None,
        shelf_life_days: Optional[float] = None,
        humidity: Optional[str] = None,
        transport: Optional[str] = None,
        map_required: Optional[bool] = None,
    ) -> Dict[str, Any]:

        food = self._resolve_food(food_name)
        fid = food["Food_ID"]
        rows = self.df[self.df["Food_ID"] == fid].copy()

        # Catalog conditions are reported, not silently used as new scientific
        # evidence. If the request supplies conditions, they are recorded and
        # used only for transparent advisory flags.
        request = {
            "food_name": food_name,
            "storage_type": storage_type,
            "shelf_life_days": shelf_life_days,
            "humidity": humidity,
            "transport": transport,
            "map_required": map_required,
        }

        eligible = rows[rows["eligible"]].copy()
        if eligible.empty:
            return {
                "status": "Insufficient_Evidence",
                "food": food["Food_Name"],
                "food_id": fid,
                "request": request,
                "recommendations": [],
                "message": (
                    "No sufficiently supported deterministic recommendation exists "
                    "for this food in the current evidence catalog. ML predictions "
                    "are not used to force a recommendation."
                ),
                "limitations": self._limitations(),
            }

        # Rank by optimization score, then deterministic class, then ML score,
        # then lower ML tree spread as a stability tie-break.
        eligible["class_rank"] = eligible[
            "Evidence_Corrected_Compatibility_Class"
        ].map(CLASS_RANK).fillna(0)
        eligible = eligible.sort_values(
            ["optimization_score", "class_rank", "ml_tiebreak", "ml_conf", "ml_sd"],
            ascending=[False, False, False, False, True],
            kind="mergesort",
        )

        # Avoid returning duplicate material variants if several rows share the
        # same packaging ID (the source universe is already one row per pair).
        top = eligible.head(max(1, int(top_n))).copy()

        recs = []
        for _, r in top.iterrows():
            cls = r["Evidence_Corrected_Compatibility_Class"]
            agreement = (
                str(r["ML_Predicted_Class"]) == str(cls)
            )
            explanation = self._explain(r, agreement)

            recs.append({
                "rank": len(recs) + 1,
                "packaging_id": r["Packaging_ID"],
                "material": r["Packaging_Material"],
                "material_category": _safe_text(r["Material_Category"]),
                "structure": _safe_text(r["Structure_Type"]),
                "compatibility_class": cls,
                "deterministic_score": None if pd.isna(r["det_score"]) else round(float(r["det_score"]), 2),
                "optimization_score": round(float(r["optimization_score"]), 2),
                "ml_predicted_score": None if pd.isna(r["ml_score"]) else round(float(r["ml_score"]), 2),
                "ml_predicted_class": _safe_text(r["ML_Predicted_Class"]),
                "ml_class_confidence": round(float(r["ml_conf"]), 4),
                "ml_tree_sd": round(float(r["ml_sd"]), 3),
                "ml_agrees_with_deterministic": bool(agreement),
                "evidence_coverage_ratio": round(float(r["coverage"]), 4),
                "sealability": _safe_text(r["Sealability"]),
                "gas_permeability": _safe_text(r["Gas_Permeability"]),
                "mechanical_strength": _safe_text(r["Mechanical_Strength"]),
                "map_suitability": _safe_text(r["MAP_Suitability_x"]),
                "otr_min": _num(r["OTR_Min_num"]),
                "otr_max": _num(r["OTR_Max_num"]),
                "wvtr_min": _num(r["WVTR_Min_num"]),
                "wvtr_max": _num(r["WVTR_Max_num"]),
                "thickness_min": _num(r["Thickness_Min_num"]),
                "thickness_max": _num(r["Thickness_Max_num"]),
                "explanation": explanation,
            })

        return {
            "status": "Recommendations_Available",
            "food": food["Food_Name"],
            "food_id": fid,
            "food_category": food["Food_Category"],
            "request": request,
            "recommendations": recs,
            "engine_notes": [
                "Deterministic evidence is the decision backbone.",
                "ML is an enhancement/tie-break signal and does not override insufficient evidence.",
                "OTR/WVTR are reported from source data; no universal lower-is-better assumption is imposed.",
                "Cost and sustainability are not scored because dedicated reliable fields were not present in the supplied packaging dataset.",
            ],
            "limitations": self._limitations(),
        }

    @staticmethod
    def _explain(r, agreement):
        cls = r["Evidence_Corrected_Compatibility_Class"]
        reasons = []
        if cls == "Compatible":
            reasons.append("deterministic evidence class is Compatible")
        elif cls == "Conditionally_Compatible":
            reasons.append("deterministic evidence class is Conditionally_Compatible")
        if float(r["coverage"]) >= 0.5:
            reasons.append("relatively higher evidence coverage in the supplied candidate record")
        if agreement:
            reasons.append("ML class agrees with the deterministic class")
        else:
            reasons.append("ML class differs from the deterministic class; deterministic status is retained")
        return "; ".join(reasons)

    @staticmethod
    def _limitations():
        return [
            "This engine is evidence-guided decision support, not laboratory validation.",
            "ML targets originate from the deterministic engine, so ML performance partly measures reproduction of that engine.",
            "The current evidence universe contains 109 foods and 40 packaging records.",
            "ML confidence is predictive model confidence, not a calibrated probability of scientific suitability.",
            "Independent experimental or industry validation is required before industrial/scientific suitability claims.",
        ]

def _num(v):
    try:
        if pd.isna(v):
            return None
        return round(float(v), 6)
    except Exception:
        return None
