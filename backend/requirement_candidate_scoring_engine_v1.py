
from __future__ import annotations
import pandas as pd
import numpy as np

class RequirementCandidateScoringEngineV1:
    """
    Requirement-aware candidate scoring layer.

    Canonical identifier: Packaging_ID.
    Conservative guardrails:
    - deterministic evidence is the backbone
    - only directly scoreable runtime capability signals are added
    - no invented OTR/WVTR/thickness thresholds
    - no universal lower-is-better gas-permeability assumption
    - insufficient evidence is never eligible
    """

    def __init__(self, feature_dataset_path):
        self.df = pd.read_csv(feature_dataset_path, low_memory=False)
        self.df["Deterministic_Score"] = pd.to_numeric(
            self.df["Evidence_Adjusted_Compatibility_Score"], errors="coerce"
        )
        self.df["Evidence_Coverage"] = pd.to_numeric(
            self.df["Evidence_Coverage_Ratio"], errors="coerce"
        ).fillna(0)
        self.df["Evidence_Norm"] = (self.df["Deterministic_Score"] / 83.33).clip(0, 1)

    @staticmethod
    def _norm(x):
        if x is None or pd.isna(x):
            return ""
        return str(x).strip().casefold()

    def score(self, food_name, storage_type=None, shelf_life_days=None,
              humidity=None, transport=None, map_required=None):
        q = self._norm(food_name)
        rows = self.df[self.df["Food_Name"].astype(str).str.casefold() == q].copy()
        if rows.empty:
            rows = self.df[
                self.df["Food_Name"].astype(str).str.casefold().str.contains(q, regex=False)
            ].copy()
        if rows.empty:
            raise ValueError(f"Food '{food_name}' is not in the 109-food catalog.")

        output = []
        for _, r in rows.iterrows():
            signals = []
            reasons = []

            if map_required is True:
                value = r.get("MAP_Suitability_x")
                if pd.isna(value):
                    reasons.append("MAP requested; source MAP suitability unavailable")
                else:
                    text = self._norm(value)
                    match = any(t in text for t in ("yes", "suitable", "compatible", "recommended"))
                    signals.append(float(match))
                    reasons.append(
                        "MAP capability matches request" if match
                        else "MAP capability does not match request"
                    )

            context = [
                ("storage_type", storage_type, "storage condition"),
                ("shelf_life_days", shelf_life_days, "shelf-life target"),
                ("humidity", humidity, "humidity"),
                ("transport", transport, "transport condition"),
            ]
            for _, val, label in context:
                if val is not None:
                    reasons.append(
                        f"{label} recorded as runtime context; no unsupported threshold applied"
                    )

            requirement_match = float(np.mean(signals)) if signals else 0.5

            eligible = (
                r["Evidence_Corrected_Compatibility_Class"] != "Insufficient_Evidence"
                and pd.notna(r["Deterministic_Score"])
            )

            candidate_score = (
                (
                    0.70 * float(r["Evidence_Norm"])
                    + 0.20 * requirement_match
                    + 0.10 * float(r["Evidence_Coverage"])
                ) * 100
                if eligible else np.nan
            )

            output.append({
                "Food_ID": r["Food_ID"],
                "Food_Name": r["Food_Name"],
                "Packaging_ID": r["Packaging_ID"],
                "Packaging_Material": r["Packaging_Material"],
                "Material_Category": r.get("Material_Category"),
                "Structure_Type": r.get("Structure_Type"),
                "Deterministic_Compatibility_Class": r["Evidence_Corrected_Compatibility_Class"],
                "Deterministic_Score": r["Deterministic_Score"],
                "Evidence_Coverage_Ratio": r["Evidence_Coverage"],
                "Requirement_Match_Score": requirement_match,
                "Requirement_Candidate_Score": candidate_score,
                "MAP_Request": map_required,
                "MAP_Request_Flag": (
                    bool(signals[0]) if map_required is True and signals else None
                ),
                "Requirement_Reasons": " | ".join(reasons),
                "Eligible": bool(eligible),
            })

        result = pd.DataFrame(output)
        return result.sort_values(
            ["Eligible", "Requirement_Candidate_Score", "Deterministic_Score"],
            ascending=[False, False, False],
            na_position="last",
            kind="mergesort",
        ).reset_index(drop=True)

    def recommend(self, food_name, top_n=3, **context):
        scored = self.score(food_name=food_name, **context)
        return scored[scored["Eligible"]].head(int(top_n)).copy()
