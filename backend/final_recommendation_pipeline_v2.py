
from pathlib import Path
import pandas as pd

try:
    from backend.requirement_candidate_scoring_engine_v1 import RequirementCandidateScoringEngineV1
    from backend.packaging_recommendation_engine_v2 import PackagingRecommendationEngineV2
except ModuleNotFoundError:
    from requirement_candidate_scoring_engine_v1 import RequirementCandidateScoringEngineV1
    from packaging_recommendation_engine_v2 import PackagingRecommendationEngineV2

class FinalRecommendationPipelineV2:
    """
    Fully integrated requirement-aware recommendation pipeline.

    Order:
      requirements -> candidate score -> deterministic/ML/optimization ->
      requirement-aware re-ranking -> explanation-preserving output.

    Deterministic Insufficient_Evidence remains a hard exclusion.
    """

    def __init__(self, base_dir="."):
        base_dir = Path(base_dir)
        self.requirements = RequirementCandidateScoringEngineV1(
            base_dir / "ML_Feature_Dataset(1).csv"
        )
        self.base = PackagingRecommendationEngineV2(
            base_dir / "ML_Feature_Dataset(1).csv"
        )

    def recommend(self, food_name, top_n=3, **context):
        req = self.requirements.score(food_name=food_name, **context)

        # Ask base engine for a sufficiently large pool before requirement-aware
        # re-ranking. This avoids only re-ranking an already tiny top-3 set.
        base_result = self.base.recommend(
            food_name=food_name,
            top_n=40,
            **context
        )

        base_df = pd.DataFrame(base_result.get("recommendations", []))
        if base_df.empty:
            base_result["requirement_aware"] = True
            base_result["pipeline_version"] = "2.1.0"
            base_result["requirement_scoring"] = {
                "weights": {"optimization": 0.75, "requirement_candidate": 0.25}
            }
            return base_result

        # Canonical identifier normalization.
        base_df["Packaging_ID"] = base_df["packaging_id"].astype(str)
        req["Packaging_ID"] = req["Packaging_ID"].astype(str)

        enrich = req[
            [
                "Packaging_ID",
                "Requirement_Candidate_Score",
                "Requirement_Match_Score",
                "MAP_Request_Flag",
                "Requirement_Reasons",
                "Eligible",
            ]
        ].drop_duplicates("Packaging_ID")

        merged = base_df.merge(
            enrich,
            on="Packaging_ID",
            how="left",
            validate="one_to_one",
        )

        # Existing deterministic optimization is primary; requirement matching
        # provides an auditable 25% runtime adjustment.
        merged["Final_Runtime_Score"] = (
            0.75 * pd.to_numeric(merged["optimization_score"], errors="coerce").fillna(0)
            + 0.25 * pd.to_numeric(
                merged["Requirement_Candidate_Score"], errors="coerce"
            ).fillna(50)
        )

        # Hard safety rule: deterministic insufficient evidence cannot enter.
        merged = merged[
            merged["compatibility_class"].astype(str).ne("Insufficient_Evidence")
        ].copy()

        merged = merged.sort_values(
            ["Final_Runtime_Score", "optimization_score", "ml_class_confidence"],
            ascending=[False, False, False],
            kind="mergesort",
        ).head(int(top_n)).reset_index(drop=True)

        merged["rank"] = range(1, len(merged) + 1)

        # Make output JSON-friendly and preserve original recommendation fields.
        base_result["recommendations"] = merged.to_dict(orient="records")
        base_result["requirement_aware"] = True
        base_result["pipeline_version"] = "2.1.0"
        base_result["requirement_scoring"] = {
            "weights": {
                "existing_optimization_score": 0.75,
                "requirement_candidate_score": 0.25,
            },
            "notes": [
                "Requirement score only uses directly scoreable source-backed runtime capability signals.",
                "No OTR/WVTR/thickness thresholds were fabricated.",
                "Deterministic Insufficient_Evidence remains a hard exclusion.",
            ],
        }
        return base_result
