from dataclasses import dataclass
from core.context import AttemptContext
from core.costant import (
    IMPULSE_TIME_THRESHOLD,
    OVERTHINK_TIME_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
    MIN_EFFECTIVE_ELIMINATIONS,
    MULTIPLE_OPTION_CHANGES
)


@dataclass(frozen=True)
class ScoreProfile:

    impulse_score: float
    familiarity_score: float
    illusion_score: float
    elimination_weakness_score: float
    overthinking_score: float


def clamp(value: float) -> float:
    """Ensure scores stay within [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


def score_attempt(context: AttemptContext) -> ScoreProfile:
    
    # Impulse score (M1)

    impulse_score = 0.0
    if not context.reasoning_started:
        impulse_score += 0.5
    if context.time_taken <= IMPULSE_TIME_THRESHOLD:
        impulse_score += 0.5

    impulse_score = clamp(impulse_score)


    # Familiarity score (M2)
    
    familiarity_score = 0.0
    if context.confidence >= HIGH_CONFIDENCE_THRESHOLD:
        familiarity_score += 0.6
    if not context.reasoning_started:
        familiarity_score += 0.4

    familiarity_score = clamp(familiarity_score)


    # Illusion of competence score (M3)

    illusion_score = 0.0
    if context.confidence >= HIGH_CONFIDENCE_THRESHOLD and not context.is_correct:
        illusion_score += 0.7
    if context.reasoning_started:
        illusion_score += 0.3

    illusion_score = clamp(illusion_score)


    # Elimination weakness score (M4)

    elimination_weakness_score = 0.0
    if len(context.options_eliminated) < MIN_EFFECTIVE_ELIMINATIONS:
        elimination_weakness_score += 0.6
    if context.reasoning_started:
        elimination_weakness_score += 0.4

    elimination_weakness_score = clamp(elimination_weakness_score)


    # Overthinking score 

    overthinking_score = 0.0
    if context.time_taken >= OVERTHINK_TIME_THRESHOLD:
        overthinking_score += 0.6
    if context.option_changes >= MULTIPLE_OPTION_CHANGES:
        overthinking_score += 0.4

    overthinking_score = clamp(overthinking_score)

    return ScoreProfile(
        impulse_score=impulse_score,
        familiarity_score=familiarity_score,
        illusion_score=illusion_score,
        elimination_weakness_score=elimination_weakness_score,
        overthinking_score=overthinking_score
    )
